from pprint import pprint
import os
import unittest
from nose.tools import eq_, ok_
from mincss.processor import Processor


_here = os.path.dirname(__file__)
html_one = os.path.join(_here, 'one.html')
html_two = os.path.join(_here, 'two.html')
html_two_half = os.path.join(_here, 'two_half.html')
html_three = os.path.join(_here, 'three.html')
html_four = os.path.join(_here, 'four.html')
html_five = os.path.join(_here, 'five.html')


class TestMinCSS(unittest.TestCase):

    def test_just_inline(self):
        url = 'file://' + html_one
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

    def test_just_one_link(self):
        url = 'file://' + html_two
        p = Processor()
        p.process(url)
        # two.html only has 1 link CSS ref
        link = p.links[0]
        eq_(link.href, 'two.css')
        eq_(link.url, url.replace('.html', '.css'))
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
        url1 = 'file://' + html_two
        url2 = 'file://' + html_two_half
        p = Processor()
        p.process(url1, url2)
        # two.html only has 1 link CSS ref
        link = p.links[0]
        eq_(link.href, 'two.css')
        eq_(link.url, url1.replace('.html', '.css'))
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
        url = 'file://' + html_three
        p = Processor()
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

        ok_('div::-moz-focus-inner' in after)
        ok_('button::-moz-focus-inner' not in after)

        ok_('@-webkit-keyframes progress-bar-stripes' in after)
        ok_('from {' in after)
        #print after

        # some day perhaps this can be untangled and parsed too
        ok_('@import url(other.css)' in after)

    def test_media_query_simple(self):
        url = 'file://' + html_four
        p = Processor()
        p.process(url)

        link = p.links[0]
        after = link.after
        #print repr(after)
        ok_('/* A comment */' in after, after)
        ok_('@media (max-width: 900px) {' in after, after)
        ok_('.container .two {' in after, after)
        ok_('.container .nine {' not in after, after)
        ok_('a.four' not in after, after)
        print after

    def test_double_classes(self):
        url = 'file://' + html_five
        p = Processor()
        p.process(url)

        link = p.links[0]
        after = link.after
        ok_('input.span6' in after)
        ok_('.uneditable-input.span9' in after)
        ok_('.uneditable-{' not in after)
        ok_('.uneditable-input.span3' not in after)
