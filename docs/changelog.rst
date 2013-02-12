.. index:: changelog

.. _changelog-chapter:

Changelog
=========

v0.6.1 (2013-02-12)
-------------------

The proxy app would turn `<script src="foo"></script>` into `<script
src="http://remote/foo"/>`. Same for iframe, textarea and divs.

v0.6.0 (2013-02-01)
-------------------

New option, `phantomjs` that allows you to download the HTML using
phantomjs instead of regular Python's urllib.


v0.5.0 (2013-01-24)
-------------------

New option `preserve_remote_urls` to `Processor()` class. Useful when
the hrefs in link tags are of different domain than the URL you're
processing.


v0.1 (2013-01-14)
-----------------

Initial release.
