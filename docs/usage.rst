
#####
Usage
#####

pmbootstrap offers many options and actions and is normally ran from a shell.


Before pmbootstrap can be used, a number of configuration questions need to be answered. The sections below go into detail for the various questions. 

.. code-block:: shell

  $ pmboostrap init

If you already ran this before, run the following to update your local clone of pmaports.git instead, before moving straight onto the installation step: 

.. code-block:: shell

   $ pmbootstrap pull

For further details on the different actions please see below and refer to the wiki-arcticle on `pmbootstrap`_.

.. autoprogram:: pmb.parse:get_parser()
   :prog: pmbootstrap
   :groups:

Requirements
============

pmbootstrap requires the following:

  * Linux distribution on the host system (`x86`, `x86_64`, `aarch64` or `armv7`)
    
    .. note::
       Windows subsystem for `Linux (WSL)`_ does **not** work! Please use `VirtualBox`_ instead.


  * Linux kernel 3.17 or higher (`oldkernel`_)

    .. note::
       Kernel version 5.8 - 6.0 might have issues with loop-devices


  * Python 3.7+
  * OpenSSL
  * git
  * ps
  * tar
  * sudo or doas


.. _pmbootstrap: https://wiki.postmarketos.org/wiki/Pmbootstrap#Using_pmbootstrap

.. _Linux (WSL): https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux

.. _virtualbox: https://www.virtualbox.org/

.. _oldkernel: https://postmarketos.org/oldkernel

