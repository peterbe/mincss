.. index:: features

.. _features-chapter:

Supported Features and Limitations
==================================

**Things that work:**

* Any selector that ``lxml``'s ``CSSSelector`` can match such as
  ``#foo > .bar input[type="submit"]``

* media queries are supported (this is treated as nested CSS basically)

* keyframes are left untouched

* You can manually over selectors that should be untouched for things
  you definitely know will be needed by Javascript code but isn't part
  of the initial HTML tree.

* You can analyze multiple URLs and find the common CSS amongst them.
  (This doesn't work for inline CSS)

* Comments are left untouched and minute whitespace details are
  preseved so the generated output looks similar to its input, but
  with the selectors not needed removed.

* A proxy server apps is available that can help you preview the
  result of just one URL.

**Things that don't yet work:**

* Javascript events that manipulate the DOM tree.
  A future version might use a parser that supports Javascript but
  likely it will never be perfect.

* keyframes are always left untouched even if it's never referenced

* Broken HTML or broken/invalid CSS isn't support and good results can
  not be guaranteed.


**Things that don't work:**

* link tags wrapped in IE-only style comments (e.g ``<!--[if lte IE
  7]>``) is not supported.
