.. index:: api

.. _api-chapter:

API
===

**This is work in progress and is likely to change in future version**

* ``process.Processor([debug=False])``
  Creates a processor instance that you can feed HTML and URLs.

  Instances of this allows you to use the following methods:

  * ``process(*urls)``
    Downloads the HTML from that URL(s) and expects it to be 200 return
    code. The content will be transformed to a unicode string in UTF-8.

    Once all URLs have been processed the CSS is analyzed.

  The ``Processor`` instance will make two attributes available

  * ``instance.inlines``
    A list of ``InlineResult`` instances (see below)

  * ``instance.links``
    A list of ``LinkResult`` instances (see below)


* ``InlineResult``

  This is where the results are stored for inline CSS. It holds the
  following attributes:

  * ``line``
    Which line in the original HTML this starts on

  * ``url``
    The URL this was found on

  * ``before``
    The inline CSS before it was analyzed

  * ``after``
    The new CSS with the selectors presumably not used removed


* ``LinkResult``

  This is where the results are stored for all referenced links to CSS
  files. i.e. from things like ``<link rel="stylesheet"
  href="foo.css">``
  It contains the following attributes:

  * ``href``
    The ``href`` attribute on the link tag. e.g. ``/static/main.css``

  * ``before``
    The CSS before it was analyzed

  * ``after``
    The new CSS with the selectors presumably not used removed
