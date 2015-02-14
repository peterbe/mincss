import os
import unittest
from nose.tools import eq_, ok_

# make sure it's running the mincss here and not anything installed
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from mincss.processor import Processor


try:
    unicode
except NameError:
    unicode = str


HERE = os.path.dirname(__file__)

PHANTOMJS = os.path.join(HERE, 'fake_phantomjs')


class TestMinCSS(unittest.TestCase):

    def test_just_inline(self):
        html = os.path.join(HERE, 'one.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)
        # on line 7 there inline css starts
        # one.html only has 1 block on inline CSS
        inline = p.inlines[0]
        lines_after = inline.after.strip().splitlines()
        eq_(inline.line, 7)
        ok_(len(inline.after) < len(inline.before))

        # compare line by line
        expect = '''
            h1, h2, h3 { text-align: center; }
            h3 { font-family: serif; }
            h2 { color:red }
        '''
        for i, line in enumerate(expect.strip().splitlines()):
            eq_(line.strip(), lines_after[i].strip())

    def test_html_with_empty_style_tag(self):
        html = os.path.join(HERE, 'one-2.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)
        eq_(p.inlines, [])

    def test_html_with_totally_empty_style_tag(self):
        html = os.path.join(HERE, 'one-3.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)
        eq_(p.inlines, [])

    def test_just_one_link(self):
        html = os.path.join(HERE, 'two.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)
        # two.html only has 1 link CSS ref
        link = p.links[0]
        eq_(link.href, 'two.css')
        ok_(len(link.after) < len(link.before))
        lines_after = link.after.splitlines()
        # compare line by line
        expect = '''
            body, html { margin: 0; }
            h1, h2, h3 { text-align: center; }
            h3 { font-family: serif; }
            h2 { color:red }
        '''
        for i, line in enumerate(expect.strip().splitlines()):
            eq_(line.strip(), lines_after[i].strip())

    def test_one_link_two_different_pages(self):
        html = os.path.join(HERE, 'two.html')
        url1 = 'file://' + html
        html_half = os.path.join(HERE, 'two_half.html')
        url2 = 'file://' + html_half
        p = Processor()
        p.process(url1, url2)
        # two.html only has 1 link CSS ref
        link = p.links[0]
        eq_(link.href, 'two.css')
        ok_(len(link.after) < len(link.before))
        lines_after = link.after.splitlines()
        # compare line by line
        expect = '''
            body, html { margin: 0; }
            h1, h2, h3 { text-align: center; }
            h3 { font-family: serif; }
            .foobar { delete:me }
            .foobar, h2 { color:red }
        '''
        for i, line in enumerate(expect.strip().splitlines()):
            eq_(line.strip(), lines_after[i].strip())

    def test_pseudo_selectors_hell(self):
        html = os.path.join(HERE, 'three.html')
        url = 'file://' + html
        p = Processor(preserve_remote_urls=False)
        p.process(url)
        # two.html only has 1 link CSS ref
        link = p.links[0]
        after = link.after
        ok_('a.three:hover' in after)
        ok_('a.hundred:link' not in after)

        ok_('.container > a.one' in after)
        ok_('.container > a.notused' not in after)
        ok_('input[type="button"]' not in after)

        ok_('input[type="search"]::-webkit-search-decoration' in after)
        ok_('input[type="reset"]::-webkit-search-decoration' not in after)

        ok_('@media (max-width: 900px)' in after)
        ok_('.container .two' in after)
        ok_('a.four' not in after)

        ok_('::-webkit-input-placeholder' in after)
        ok_(':-moz-placeholder {' in after)
        ok_('div::-moz-focus-inner' in after)
        ok_('button::-moz-focus-inner' not in after)

        ok_('@-webkit-keyframes progress-bar-stripes' in after)
        ok_('from {' in after)

        # some day perhaps this can be untangled and parsed too
        ok_('@import url(other.css)' in after)

    def test_media_query_simple(self):
        html = os.path.join(HERE, 'four.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)

        link = p.links[0]
        after = link.after
        ok_('/* A comment */' in after, after)
        ok_('@media (max-width: 900px) {' in after, after)
        ok_('.container .two {' in after, after)
        ok_('.container .nine {' not in after, after)
        ok_('a.four' not in after, after)

    def test_double_classes(self):
        html = os.path.join(HERE, 'five.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)

        after = p.links[0].after
        eq_(after.count('{'), after.count('}'))
        ok_('input.span6' in after)
        ok_('.uneditable-input.span9' in after)
        ok_('.uneditable-{' not in after)
        ok_('.uneditable-input.span3' not in after)

    def test_complicated_keyframes(self):
        html = os.path.join(HERE, 'six.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)

        after = p.inlines[0].after
        eq_(after.count('{'), after.count('}'))
        ok_('.pull-left' in after)
        ok_('.pull-right' in after)
        ok_('.pull-middle' not in after)

    def test_ignore_annotations(self):
        html = os.path.join(HERE, 'seven.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)

        after = p.inlines[0].after
        eq_(after.count('{'), after.count('}'))
        ok_('/* Leave this comment as is */' in after)
        ok_('/* Lastly leave this as is */' in after)
        ok_('/* Also stick around */' in after)
        ok_('/* leave untouched */' in after)
        ok_('.north' in after)
        ok_('.south' in after)
        ok_('.east' not in after)
        ok_('.west' in after)
        ok_('no mincss' not in after)

    def test_non_ascii_html(self):
        html = os.path.join(HERE, 'eight.html')
        url = 'file://' + html
        p = Processor()
        p.process(url)

        after = p.inlines[0].after
        ok_(isinstance(after, unicode))
        ok_(u'Varf\xf6r st\xe5r det h\xe4r?' in after)

    def test_preserve_remote_urls(self):
        html = os.path.join(HERE, 'nine.html')
        url = 'file://' + html
        p = Processor(preserve_remote_urls=True)
        p.process(url)

        after = p.links[0].after
        ok_("url('http://www.google.com/north.png')" in after)
        url = 'file://' + HERE + '/deeper/south.png'
        ok_('url("%s")' % url in after)
        # since local file URLs don't have a domain, this is actually expected
        ok_('url("file:///east.png")' in after)
        url = 'file://' + HERE + '/west.png'
        ok_('url("%s")' % url in after)

    @unittest.skip('This has always been failing')
    def test_download_with_phantomjs(self):
        html = os.path.join(HERE, 'one.html')
        url = 'file://' + html
        p = Processor(
            phantomjs=PHANTOMJS,
            phantomjs_options={'cookies-file': 'bla'}
        )
        p.process(url)
        # on line 7 there inline css starts
        # one.html only has 1 block on inline CSS
        inline = p.inlines[0]
        lines_after = inline.after.strip().splitlines()
        eq_(inline.line, 7)
        ok_(len(inline.after) < len(inline.before))

        # compare line by line
        expect = '''
            h1, h2, h3 { text-align: center; }
            h3 { font-family: serif; }
            h2 { color:red }
        '''
        for i, line in enumerate(expect.strip().splitlines()):
            eq_(line.strip(), lines_after[i].strip())

    def test_make_absolute_url(self):
        p = Processor()
        eq_(
            p.make_absolute_url('http://www.com/', './style.css'),
            'http://www.com/style.css'
        )
        eq_(
            p.make_absolute_url('http://www.com', './style.css'),
            'http://www.com/style.css'
        )
        eq_(
            p.make_absolute_url('http://www.com', '//cdn.com/style.css'),
            'http://cdn.com/style.css'
        )
        eq_(
            p.make_absolute_url('http://www.com/', '//cdn.com/style.css'),
            'http://cdn.com/style.css'
        )
        eq_(
            p.make_absolute_url('http://www.com/', '/style.css'),
            'http://www.com/style.css'
        )
        eq_(
            p.make_absolute_url('http://www.com/elsewhere', '/style.css'),
            'http://www.com/style.css'
        )
        eq_(
            p.make_absolute_url('http://www.com/elsewhere/', '/style.css'),
            'http://www.com/style.css'
        )
        eq_(
            p.make_absolute_url('http://www.com/elsewhere/', './style.css'),
            'http://www.com/elsewhere/style.css'
        )
        eq_(
            p.make_absolute_url('http://www.com/elsewhere', './style.css'),
            'http://www.com/style.css'
        )
