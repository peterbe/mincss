.. mincss documentation master file, created by Peter Bengtsson
   sphinx-quickstart on Fri Jan 11 14:08:28 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

mincss - Clears the junk out of your CSS
========================================

``mincss`` is a Python library that makes it possible to evaluate
which CSS is actually being used. It does this by download the whole
page(s) and finds all inline and linked CSS and analyses which
selectors are still in use somewhere.

It currently does the analysis entirely statically and does not
support Javascript.

``mincss`` is currently under development and the API is possibly
changing.

Installation should be as simple as ``pip install mincss``. The code
is `available on Github <https://github.com/peterbe/mincss>`_.

.. toctree::
   :maxdepth: 2

   gettingstarted
   features
   api
   changelog


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
