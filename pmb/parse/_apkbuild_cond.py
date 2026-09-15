# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Evaluate the architecture conditionals of an APKBUILD.

abuild sources an APKBUILD with CARCH set, so a top-level
``case "$CARCH" in``, ``if [ "$CARCH" = ... ]`` or ``[ "$CARCH" = ... ] &&``
decides which depends, makedepends and subpackages a build gets. The attribute
parser in _apkbuild.py reads lines without running them, so it used to skip
every such block (indented assignments do not match) or apply all branches at
once (inside subpackage functions, where lines are stripped).

resolve() rewrites the lines first: every block whose conditions can be decided
exactly is replaced by the commands of the branch the shell would run. A block
that needs anything else, such as a command substitution, a loop, or a variable
that only exists at build time ($CBUILD, $BOOTSTRAP), is left exactly as it
was, so the parser sees what it saw before. If the file cannot be tokenized at
all, it is returned unchanged.
"""

import fnmatch
import re
from bisect import bisect_right
from collections.abc import Callable
from dataclasses import dataclass, field

_NAME = r"[A-Za-z_][A-Za-z0-9_]*"
_ASSIGNMENT = re.compile(rf"({_NAME})=")
_FUNCTION_START = re.compile(rf"^{_NAME}\(\)\s*([{{(])")
_KEYWORDS_END = frozenset({"then", "elif", "else", "fi", "esac", "do", "done", "}"})
_OPERATORS = (";;", "&&", "||", "<<", ";", "|", "(", ")", "&", "<", ">")


class UnevaluableError(Exception):
    """The shell code cannot be evaluated exactly without running it."""


@dataclass
class Tok:
    kind: str  # "word", "nl" or one of _OPERATORS
    text: str
    start: int
    end: int


@dataclass
class Cmd:
    """An and-or list of simple commands: ``a && b || c``."""

    pipelines: list[list[Tok]]
    ops: list[str]
    start: int
    end: int


@dataclass
class If:
    # (condition, body); the condition is None for "else"
    arms: list[tuple["list[Item] | None", "list[Item]"]]
    start: int
    end: int


@dataclass
class Case:
    word: Tok
    arms: list[tuple[list[Tok], "list[Item]"]]
    start: int
    end: int


@dataclass
class Opaque:
    """A loop, group or subshell: parsed for its extent, never evaluated."""

    start: int
    end: int


Item = Cmd | If | Case | Opaque


def _skip_dquote(src: str, i: int) -> int:
    """:returns: index after the closing double quote, i points after the opening one"""
    while i < len(src):
        c = src[i]
        if c == "\\":
            i += 2
        elif c == '"':
            return i + 1
        elif src.startswith("$(", i):
            i = _skip_parens(src, i + 2)
        elif c == "`":
            i = _skip_backtick(src, i + 1)
        else:
            i += 1
    raise UnevaluableError("unterminated double quote")


def _skip_backtick(src: str, i: int) -> int:
    end = src.find("`", i)
    if end < 0:
        raise UnevaluableError("unterminated backtick")
    return end + 1


def _skip_parens(src: str, i: int) -> int:
    """:returns: index after the parenthesis closing the one before i"""
    depth = 1
    while i < len(src):
        c = src[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            end = src.find("'", i + 1)
            if end < 0:
                raise UnevaluableError("unterminated single quote")
            i = end + 1
            continue
        if c == '"':
            i = _skip_dquote(src, i + 1)
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise UnevaluableError("unterminated command substitution")


def _word_end(src: str, i: int) -> int:
    while i < len(src):
        c = src[i]
        if c in " \t\n;&|()<>":
            return i
        if c == "\\":
            i += 2
        elif c == "'":
            end = src.find("'", i + 1)
            if end < 0:
                raise UnevaluableError("unterminated single quote")
            i = end + 1
        elif c == '"':
            i = _skip_dquote(src, i + 1)
        elif c == "`":
            i = _skip_backtick(src, i + 1)
        elif src.startswith("$(", i):
            i = _skip_parens(src, i + 2)
        elif src.startswith("${", i):
            end = src.find("}", i)
            if end < 0:
                raise UnevaluableError("unterminated parameter expansion")
            i = end + 1
        else:
            i += 1
    return i


def tokenize(src: str) -> list[Tok]:
    toks: list[Tok] = []
    i = 0
    while i < len(src):
        c = src[i]
        if c in " \t":
            i += 1
        elif src.startswith("\\\n", i):
            i += 2
        elif c == "\n":
            toks.append(Tok("nl", c, i, i + 1))
            i += 1
        elif c == "#":
            end = src.find("\n", i)
            i = len(src) if end < 0 else end
        else:
            op = next((op for op in _OPERATORS if src.startswith(op, i)), None)
            if op == "<<":
                # A here-document body is not shell code
                raise UnevaluableError("here-document")
            if op:
                toks.append(Tok(op, op, i, i + len(op)))
                i += len(op)
            else:
                end = _word_end(src, i)
                toks.append(Tok("word", src[i:end], i, end))
                i = end
    return toks


class _Parser:
    def __init__(self, toks: list[Tok]) -> None:
        self.toks = toks
        self.pos = 0

    def peek(self) -> Tok | None:
        return self.toks[self.pos] if self.pos < len(self.toks) else None

    def next(self) -> Tok:
        tok = self.peek()
        if tok is None:
            raise UnevaluableError("unexpected end of file")
        self.pos += 1
        return tok

    def expect_word(self, text: str) -> Tok:
        tok = self.next()
        if tok.kind != "word" or tok.text != text:
            raise UnevaluableError(f"expected '{text}', got '{tok.text}'")
        return tok

    def skip(self, kinds: tuple[str, ...] = ("nl", ";")) -> None:
        while (tok := self.peek()) is not None and tok.kind in kinds:
            self.pos += 1

    def parse_list(self, stop: frozenset[str] = frozenset()) -> list[Item]:
        items: list[Item] = []
        while True:
            self.skip()
            tok = self.peek()
            if tok is None:
                if stop:
                    raise UnevaluableError("unexpected end of file")
                return items
            if tok.kind == ";;" and "esac" in stop:
                return items
            if tok.kind in ("word", ")") and tok.text in stop:
                return items
            items.append(self.parse_item())

    def parse_item(self) -> Item:
        tok = self.next()
        if tok.kind == "word":
            if tok.text == "if":
                return self.parse_if(tok)
            if tok.text == "case":
                return self.parse_case(tok)
            if tok.text in ("for", "while", "until"):
                return self.parse_loop(tok)
            if tok.text == "{":
                self.parse_list(frozenset({"}"}))
                return Opaque(tok.start, self.next().end)
            if tok.text in _KEYWORDS_END:
                raise UnevaluableError(f"unexpected '{tok.text}'")
        elif tok.kind == "(":
            self.parse_list(frozenset({")"}))
            return Opaque(tok.start, self.next().end)
        else:
            raise UnevaluableError(f"unexpected '{tok.text}'")
        self.pos -= 1
        return self.parse_andor()

    def parse_andor(self) -> Cmd:
        pipelines: list[list[Tok]] = [[]]
        ops: list[str] = []
        start = end = self.toks[self.pos].start
        while (tok := self.peek()) is not None and tok.kind not in ("nl", ";", ";;"):
            if tok.kind in ("&&", "||"):
                if not pipelines[-1]:
                    raise UnevaluableError(f"unexpected '{tok.text}'")
                ops.append(tok.kind)
                pipelines.append([])
                self.pos += 1
                self.skip(("nl",))
                continue
            if tok.kind in ("(", ")", "&"):
                # function definitions, background jobs, case patterns
                raise UnevaluableError(f"unexpected '{tok.text}'")
            pipelines[-1].append(tok)
            end = tok.end
            self.pos += 1
        if not pipelines[-1]:
            raise UnevaluableError("incomplete and-or list")
        return Cmd(pipelines, ops, start, end)

    def parse_if(self, first: Tok) -> If:
        arms: list[tuple[list[Item] | None, list[Item]]] = []
        cond: list[Item] | None = self.parse_list(frozenset({"then"}))
        while True:
            if cond is not None:
                self.expect_word("then")
            body = self.parse_list(frozenset({"elif", "else", "fi"}))
            arms.append((cond, body))
            tok = self.next()
            if tok.text == "fi":
                return If(arms, first.start, tok.end)
            if cond is None:
                raise UnevaluableError("'else' must be the last branch")
            cond = self.parse_list(frozenset({"then"})) if tok.text == "elif" else None

    def parse_case(self, first: Tok) -> Case:
        word = self.next()
        if word.kind != "word":
            raise UnevaluableError("case without a word")
        self.expect_word("in")
        arms: list[tuple[list[Tok], list[Item]]] = []
        while True:
            self.skip(("nl",))
            tok = self.next()
            if tok.kind == "word" and tok.text == "esac":
                return Case(word, arms, first.start, tok.end)
            if tok.kind == "(":
                tok = self.next()
            patterns = []
            while True:
                if tok.kind != "word":
                    raise UnevaluableError("bad case pattern")
                patterns.append(tok)
                sep = self.next()
                if sep.kind == ")":
                    break
                if sep.kind != "|":
                    raise UnevaluableError("bad case pattern")
                tok = self.next()
            body = self.parse_list(frozenset({"esac"}))
            if (tok_end := self.peek()) is not None and tok_end.kind == ";;":
                self.pos += 1
            arms.append((patterns, body))

    def parse_loop(self, first: Tok) -> Opaque:
        if first.text == "for":
            while self.next().text != "do":
                pass
        else:
            self.parse_list(frozenset({"do"}))
            self.expect_word("do")
        self.parse_list(frozenset({"done"}))
        return Opaque(first.start, self.next().end)


@dataclass
class _Evaluator:
    src: str
    variables: dict[str, str | None]
    emitted: list[str] = field(default_factory=list)

    def expand(self, word: str, pattern: bool = False) -> str:
        """
        Remove quotes and expand $NAME and ${NAME}, like the shell does for a
        word that is not split. With pattern=True, quoted glob characters stay
        literal for fnmatch.
        """
        out = []
        quote = ""
        i = 0

        def literal(text: str, quoted: bool) -> None:
            if pattern and quoted:
                text = re.sub(r"([*?\[])", r"[\1]", text)
            out.append(text)

        while i < len(word):
            c = word[i]
            if quote == "'":
                if c == "'":
                    quote = ""
                else:
                    literal(c, True)
                i += 1
            elif c == "'" and not quote:
                quote = "'"
                i += 1
            elif c == '"':
                quote = "" if quote else '"'
                i += 1
            elif c == "\\" and i + 1 < len(word):
                if quote and word[i + 1] not in '$`"\\':
                    literal(c, True)
                    i += 1
                else:
                    literal(word[i + 1], True)
                    i += 2
            elif c == "$":
                match = re.match(rf"\$(?:\{{({_NAME})\}}|({_NAME}))", word[i:])
                if not match:
                    raise UnevaluableError(f"cannot expand {word}")
                value = self.variables.get(match.group(1) or match.group(2))
                if value is None:
                    raise UnevaluableError(f"unknown variable in {word}")
                literal(value, True)
                i += match.end()
            elif c == "`":
                raise UnevaluableError(f"command substitution in {word}")
            else:
                literal(c, bool(quote))
                i += 1
        return "".join(out)

    def test(self, words: list[Tok]) -> bool:
        """Evaluate the arguments of [ or test."""
        if words and words[0].text == "!":
            return not self.test(words[1:])
        raw = [w.text for w in words]
        values = [self.expand(w.text) for w in words]
        if len(words) == 1:
            return values[0] != ""
        if len(words) == 2 and raw[0] in ("-n", "-z"):
            return (values[1] == "") == (raw[0] == "-z")
        if len(words) == 3:
            left, op, right = values[0], raw[1], values[2]
            if op in ("=", "=="):
                return left == right
            if op == "!=":
                return left != right
            integer_ops: dict[str, Callable[[int, int], bool]] = {
                "-eq": int.__eq__,
                "-ne": int.__ne__,
                "-lt": int.__lt__,
                "-le": int.__le__,
                "-gt": int.__gt__,
                "-ge": int.__ge__,
            }
            if op in integer_ops:
                try:
                    return integer_ops[op](int(left), int(right))
                except ValueError as exception:
                    raise UnevaluableError(f"not an integer: {left} {op} {right}") from exception
        raise UnevaluableError(f"unsupported test: {' '.join(raw)}")

    def text(self, toks: list[Tok]) -> str:
        return self.src[toks[0].start : toks[-1].end]

    def assign(self, word: str) -> None:
        match = _ASSIGNMENT.match(word)
        if not match:
            raise ValueError(f"not an assignment: {word}")
        try:
            self.variables[match.group(1)] = self.expand(word[match.end() :])
        except UnevaluableError:
            self.variables[match.group(1)] = None

    def run_simple(self, toks: list[Tok], emit: bool) -> int | None:
        """:returns: exit status, None if unknown"""
        negate = toks[0].text == "!"
        if negate:
            toks = toks[1:]
        if not toks or any(tok.kind != "word" for tok in toks):
            raise UnevaluableError("pipe or redirection")
        words = [tok.text for tok in toks]
        status: int | None
        if words[0] == "[":
            if words[-1] != "]":
                raise UnevaluableError("[ without ]")
            status = 0 if self.test(toks[1:-1]) else 1
        elif words[0] == "test":
            status = 0 if self.test(toks[1:]) else 1
        elif words[0] in (":", "true", "false"):
            status = 1 if words[0] == "false" else 0
        else:
            if all(_ASSIGNMENT.match(word) for word in words):
                for word in words:
                    self.assign(word)
                status = 0
            elif words[0] in ("export", "readonly", "unset", "local"):
                for word in words[1:]:
                    if _ASSIGNMENT.match(word):
                        self.assign(word)
                    else:
                        self.variables[word] = None
                status = 0
            else:
                status = None
            if emit:
                self.emitted.append(self.text(toks))
        if negate and status is not None:
            status = 0 if status else 1
        return status

    def run(self, items: list[Item], emit: bool) -> int | None:
        status: int | None = 0
        for item in items:
            status = self.run_item(item, emit)
        return status

    def run_item(self, item: Item, emit: bool) -> int | None:
        if isinstance(item, Cmd):
            status = self.run_simple(item.pipelines[0], emit)
            for op, pipeline in zip(item.ops, item.pipelines[1:], strict=True):
                if status is None:
                    raise UnevaluableError("condition with unknown exit status")
                if (op == "&&") == (status == 0):
                    status = self.run_simple(pipeline, emit)
            return status
        if isinstance(item, If):
            for cond, body in item.arms:
                if cond is None:
                    return self.run(body, emit)
                status = self.run(cond, False)
                if status is None:
                    raise UnevaluableError("condition with unknown exit status")
                if status == 0:
                    return self.run(body, emit)
            return 0
        if isinstance(item, Case):
            value = self.expand(item.word.text)
            for patterns, body in item.arms:
                if any(fnmatch.fnmatchcase(value, self.expand(p.text, True)) for p in patterns):
                    return self.run(body, emit)
            return 0
        raise UnevaluableError("loop, group or subshell")

    def forget(self, item: Item) -> None:
        """Mark every variable an unevaluated item might set as unknown."""
        code = self.src[item.start : item.end]
        for match in re.finditer(rf"(?:^|[\s;&|(])(?:({_NAME})=|for\s+({_NAME}))", code):
            self.variables[match.group(1) or match.group(2)] = None
        for match in re.finditer(rf"\b(?:unset|export|readonly|local)\s+({_NAME})", code):
            self.variables[match.group(1)] = None


def resolve(lines: list[str], variables: dict[str, str]) -> list[str]:
    """
    Replace the conditional blocks of APKBUILD lines by the branches taken.

    :param lines: newline-terminated lines of shell code, e.g. an APKBUILD or
                  the stripped body of a subpackage function
    :param variables: the variables that are known before the first line,
                      e.g. {"CARCH": "aarch64"}. Every other variable is
                      unknown until the code assigns it.
    :returns: the lines with every block that could be evaluated replaced by
              the commands that the shell would run, one per line
    """
    # Function bodies are not run when the APKBUILD is sourced
    masked = []
    function_end = ""  # "}" or ")" while inside a function body
    for line in lines:
        if function_end:
            if line.startswith(function_end):
                function_end = ""
            masked.append("\n")
        elif match := _FUNCTION_START.match(line):
            end = "}" if match.group(1) == "{" else ")"
            function_end = "" if line.rstrip().endswith(end) else end
            masked.append("\n")
        else:
            masked.append(line if line.endswith("\n") else line + "\n")
    src = "".join(masked)

    try:
        items = _Parser(tokenize(src)).parse_list()
    except UnevaluableError:
        return lines

    line_starts = [0]
    for line in masked[:-1]:
        line_starts.append(line_starts[-1] + len(line))

    def line_of(offset: int) -> int:
        return bisect_right(line_starts, offset) - 1

    def contains_function(first: int, last: int) -> bool:
        return any(masked[i] == "\n" and lines[i].strip() for i in range(first, last + 1))

    evaluator = _Evaluator(src, dict(variables))
    replacements: dict[int, tuple[int, list[str]]] = {}
    for index, item in enumerate(items):
        first, last = line_of(item.start), line_of(item.end - 1)
        conditional = isinstance(item, If | Case) or (isinstance(item, Cmd) and item.ops)
        if not conditional:
            try:
                evaluator.run_item(item, False)
            except UnevaluableError:
                evaluator.forget(item)
            continue

        shares_lines = (index > 0 and line_of(items[index - 1].end - 1) >= first) or (
            index + 1 < len(items) and line_of(items[index + 1].start) <= last
        )
        saved = dict(evaluator.variables)
        evaluator.emitted = []
        try:
            if shares_lines or contains_function(first, last):
                raise UnevaluableError("block shares its lines")
            evaluator.run_item(item, True)
        except UnevaluableError:
            evaluator.variables = saved
            evaluator.forget(item)
            continue
        replacements[first] = (last, evaluator.emitted)

    ret: list[str] = []
    i = 0
    while i < len(lines):
        if i in replacements:
            last, emitted = replacements[i]
            for command in emitted:
                ret += [part.strip() + "\n" for part in command.split("\n")]
            i = last + 1
        else:
            ret.append(lines[i])
            i += 1
    return ret
