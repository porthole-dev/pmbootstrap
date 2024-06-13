# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

import copy
from typing import Callable, Dict, Optional


class Wrapper:
    def __init__(self, cache: "Cache", func: Callable):
        self.cache = cache
        self.func = func
        self.disabled = False
        self.__module__ = func.__module__
        self.__name__ = func.__name__


    # When someone attempts to call a cached function, they'll
    # actually end up here. We first check if we have a cached
    # result and if not then we do the actual function call and
    # cache it if applicable
    def __call__(self, *args, **kwargs):
        if self.disabled:
            return self.func(*args, **kwargs)

        # Build the cache key from the function arguments that we
        # care about, which might be none of them
        key = self.cache.build_key(self.func, *args, **kwargs)
        # Don't cache
        if key is None:
            return self.func(*args, **kwargs)

        if key not in self.cache.cache:
            try:
                self.cache.cache[key] = self.func(*args, **kwargs)
            except Exception as e:
                raise e
        elif self.cache.cache_deepcopy:
            self.cache.cache[key] = copy.deepcopy(self.cache.cache[key])

        #print(f"Cache: {func.__name__}({key})")
        return self.cache.cache[key]

    def cache_clear(self):
        self.cache.clear()

    def cache_disable(self):
        self.disabled = True


class Cache:
    """Cache decorator for caching function results based on parameters.

    :param args: a list of function arguments to use as the cache key.
    :param kwargs: these are arguments where we should only cache if the
    function is called with the given value. For example, in pmb.build._package
    we never want to use the cached result when called with force=True."""

    def __init__(self, *args, cache_deepcopy=False, **kwargs):
        for a in args:
            if not isinstance(a, str):
                raise ValueError(f"Cache key must be a string, not {type(a)}")

        if len(args) != len(set(args)):
            raise ValueError("Duplicate cache key properties")

        self.cache = {}
        self.params = args
        self.kwargs = kwargs
        self.cache_deepcopy = cache_deepcopy


    # Build the cache key, or return None to not cache in the case where
    # we only cache when an argument has a specific value
    def build_key(self, func: Callable, *args, **kwargs) -> Optional[str]:
        key = "~"
        # Easy case: cache irrelevant of arguments
        if not self.params and not self.kwargs:
            return key

        argnames = list(func.__code__.co_varnames)[:func.__code__.co_argcount]

        # Build a dictionary of the arguments passed to the function and their values
        # including the default values
        # This is a silly mess because I wanted to avoid using inspect, but the reflection
        # stuff is not fun to work with...
        _kwargs = {}
        kwargs_start = len(argnames)-len(list(func.__defaults__ or [])) - 1
        for i in range(len(argnames)-1, 0, -1):
            arg = argnames[i]
            if arg not in self.kwargs:
                continue
            if arg in kwargs:
                _kwargs[argnames[i]] = kwargs[arg]
            elif i >= kwargs_start:
                #print(f"{func.__name__} -- {i}: {argnames[i]}")
                _kwargs[argnames[i]] = list(func.__defaults__ or [])[kwargs_start + i - 1]
        passed_args = dict(zip(argnames, args + tuple(_kwargs)))

        #print(f"Cache.build_key({func}, {args}, {kwargs}) -- {passed_args}")
        if self.kwargs:
            for k, v in self.kwargs.items():
                if k not in argnames:
                    raise ValueError(f"Cache key attribute {k} is not a valid parameter to {func.__name__}()")
                # Get the value passed into the function, or the default value
                # FIXME: could get a false hit if this is None
                passed_val = passed_args.get(k, _kwargs.get(k))
                if passed_val != v:
                    return None
                else:
                    key += f"{k}=({v})~"

        if self.params:
            for i, param in enumerate(args + tuple(kwargs.keys())):
                if argnames[i] in self.params[0]:
                    if param.__str__ != object.__str__:
                        key += f"{param}~"
                    else:
                        raise ValueError(f"Cache key argument {argnames[i]} to function"
                                            f" {func.__name__} must be a stringable type")

        return key


    def __call__(self, func: Callable):
        argnames = func.__code__.co_varnames
        for a in self.params:
            if a not in argnames:
                raise ValueError(f"Cache key attribute {a} is not a valid parameter to {func.__name__}()")

        return Wrapper(self, func)


    def clear(self):
        self.cache.clear()
