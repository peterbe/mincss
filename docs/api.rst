.. index:: api

.. _api-chapter:

API
===

**This is work in progress and is likely to change in future version**

* ``process.Processor([debug=False, preserve_remote_urls=True])``
  Creates a processor instance that you can feed HTML and URLs.

  The arguments:

    * ``debug=False``
      Currently does nothing particular.

    * ``preserve_remote_urls=True``
      If you run a URL like ``http://www.example.org`` that references
      ``http://cdn.cloudware.com/foo.css`` which contains
      ``url(/background.png)`` then the CSS will be rewritten to become
      ``url(http://cdn.cloudware.com/background.png)``

    * ``phantomjs=None``
      If ``True`` will default to ``phantomjs``, If a string it's
      assume it's the path to the executable ``phantomjs`` path.

    * ``phantomjs_options={}``
      Additional options/switches to the ``phantomjs`` command. This
      has to be a dict. So, for example ``{'script-encoding': 'latin1'}``
      becomes ``--script-encoding=latin1``.

    * ``optimize_lookup=True``
      If true, will make a set of all ids and class names in all
      processed documents and use these to avoid some expensive CSS
      query searches.

  Instances of this allows you to use the following methods:

  * ``process(*urls)``
    Downloads the HTML from that URL(s) and expects it to be 200 return
    code. The content will be transformed to a unicode string in UTF-8.

    Once all URLs have been processed the CSS is analyzed.

  * ``process_url(url)``
    Given a specific URL it will download it and parse the HTML. This
    method will download the HTML then called ``process_html()``.

  * ``process_html(html, url)``
    If you for some reason already have the HTML you can jump straight
    to this method. Note, you still need to provide the URL where you
    got the HTML from so it can use that to download any external CSS.
    
  * When calling ``process_url()`` or ``process_html()``, you have to call ``process()``
    at the end without arguments, in order to post process the pages that were
    processed individually.

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
