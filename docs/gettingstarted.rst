.. index:: gettingstarted

.. _gettingstarted-chapter:

Getting started
===============

Suppose you have a page like this::

 <!doctype html>
 <html>
   <head>
     <style type="text/css">
     .foo, input:hover { color: black; }
     .bar { color: blue; }
     </style>
   </head>
   <body>
     <div id="content">
       <p class="foo">Foo!</p>
     </div>
   </body>
 </html>

And, let's assume that this is available as
``http://localhost/page.html``.

Now, let's use ``mincss`` as follows::

 >>> from mincss.processor import Processor
 >>> p = Processor()
 >>> p.process('http://localhost/page.html')
 >>> inline = p.inlines[0]
 >>> inline.before
 '\n    .foo, input:hover { color: black; }\n    .bar { color: blue; }\n    '
 >>> inline.after
 '\n    .foo { color: black; }\n    '

As you can see, it automatically discovered that the ``input:hover``
and the ``.bar`` selectors are not used in the HTML DOM tree.
