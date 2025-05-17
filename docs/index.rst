Welcome to pmbootstrap's documentation!
=======================================

pmbootstrap is the central command-line application for postmarketOS development. Among other things,
it allows building packages, creating installation images and flashing themx to your device. If you just want to install 
postmarketOS, read the `Installation`_ wiki article first since you might not need pmbootstrap depeing on the method.

For the latest releases please check the `repository`_. 
  
In case of any problems that is also the place to check the `issue-tracker`_.

For further information, please check out the `postmarketOS-wiki`_.


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   installation
   usage
   chroot
   debugging
   cross_compiling
   ssh-keys
   api/modules
   mirrors
   environment_variables



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Deploying locally
=================

To deploy with :doc:`pmbootstrap ci <api/pmb.ci>` command (see also: `Pmbootstrap_CI`_ wiki article):

.. code-block:: sh

   cd /path/to/pmbootstrap
   pmbootstrap ci docs

.. code-block:: text

   build succeeded.
   The HTML pages are in public.
   Copy CI artifacts to ./ci-artifacts/docs

After this, you should be able to host results with ``darkhttpd`` or Python's built-in server:

.. code-block:: sh

   python -m http.server -d ./ci-artifacts/docs/public

*Note:* This documentation is currently a work-in-progress, your feedback and contributions are very welcome!

.. _postmarketOS-wiki: https://wiki.postmarketos.org/wiki/Main_Page
.. _issue-tracker: https://gitlab.postmarketos.org/postmarketOS/pmbootstrap/-/issues
.. _repository: https://gitlab.postmarketos.org/postmarketOS/pmbootstrap/
.. _Installation: https://wiki.postmarketos.org/wiki/Installation
.. _Pmbootstrap_CI: https://wiki.postmarketos.org/wiki/Pmbootstrap_CI
