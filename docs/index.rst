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

To deploy with python virtual environment and sphinx-autobuild:

.. code-block:: sh

   cd /path/to/pmbootstrap
   python -m venv build-sphinx-env
   source ./build-sphinx-env/bin/activate
   pip install sphinx-autobuild sphinx_rtd_theme myst-parser sphinxcontrib-autoprogram
   sphinx-autobuild docs docs/_build/html

.. code-block:: text

   [sphinx-autobuild] Serving on http://127.0.0.1:8000
   [sphinx-autobuild] Waiting to detect changes...

*Note:* This documentation is currently a work-in-progress, your feedback and contributions are very welcome!

.. _postmarketOS-wiki: https://wiki.postmarketos.org/wiki/Main_Page
.. _issue-tracker: https://gitlab.postmarketos.org/postmarketOS/pmbootstrap/-/issues
.. _repository: https://gitlab.postmarketos.org/postmarketOS/pmbootstrap/
.. _Installation: https://wiki.postmarketos.org/wiki/Installation
