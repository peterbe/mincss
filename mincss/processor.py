import sys
import collections
import random
import re
from cStringIO import StringIO
from urlparse import urlparse
from pprint import pprint
import cssmin
from lxml import etree
from lxml.cssselect import CSSSelector, SelectorSyntaxError, ExpressionError
import pyquery
import urllib
from collections import OrderedDict

RE_HAS_MEDIA = re.compile("@media")
RE_FIND_MEDIA = re.compile("(@media.+?)(\{)", re.DOTALL | re.MULTILINE)


EXCEPTIONAL_SELECTORS = (
    'html',
)

def _get_random_string():
    p = 'abcdefghijklmopqrstuvwxyz'
    pl = list(p)
    random.shuffle(pl)
    return ''.join(pl)


class Processor(object):

    def __init__(self, debug=False, exclude_pseudoclasses=True):
        self.debug = debug
        self.tab = ' ' * 4
        self.blocks = {}
        self.keep = collections.defaultdict(list)
        self.blocks_bytes = {}
        self.exclude_pseudoclasses = exclude_pseudoclasses
        self.inlines = []
        self.links = []
        self._bodies = []

    def download(self, url):
        return urllib.urlopen(url).read()

    def process(self, *urls):
        for url in urls:
            self.process_url(url)

        #pprint(blocks)
        for identifier in sorted(self.blocks.keys()):
            content = self.blocks[identifier]
            processed = self._process_content(content, self._bodies)

            if isinstance(identifier[0], int):
                line, url = identifier
                # inline
                self.inlines.append(
                    InlineResult(
                        line,
                        url,
                        content,
                        processed
                    )
                )
            else:
                url, href = identifier
                self.links.append(
                    LinkResult(
                        href,
                        url,
                        content,
                        processed
                    )
                )

    def process_url(self, url):
        html = self.download(url)
        parser = etree.HTMLParser()
        stripped = html.strip()
        tree = etree.fromstring(stripped, parser).getroottree()
        page = tree.getroot()

        # lxml inserts a doctype if none exists, so only include it in
        # the root if it was in the original html.
        root = tree if stripped.startswith(tree.docinfo.doctype) else page

        if page is None:
            print repr(html)
            raise ParserError("Could not parse the html")

        lines = html.splitlines()
        body, = CSSSelector('body')(page)
        self._bodies.append(body)
        for style in CSSSelector('style')(page):
            first_line = style.text.strip().splitlines()[0]
            for i, line in enumerate(lines):
                if line.count(first_line):
                    key = (i + 1, url)
                    self.blocks[key] = style.text
                    break

        for link in CSSSelector('link')(page):
            if (
                link.attrib.get('rel', '') == 'stylesheet' or
                link.attrib['href'].lower().endswith('.css')
            ):
                link_url = self.make_absolute_url(url, link.attrib['href'])
                key = (link_url, link.attrib['href'])
                self.blocks[key] = self.download(link_url)

    def _process_content(self, content, bodies):
        # Find all of the unique media queries

        queries = [(m.group(1), m) for m in RE_FIND_MEDIA.finditer(content)]

        inner_improvements = []
        # Consolidate the media queries
        for (query, m) in queries:
            inner, whole = self._get_contents(m, content)
            improved_inner = self._process_content(inner, bodies)
            if improved_inner.strip():
                improved = query + ' {' + improved_inner + '}'
            else:
                improved = ''
            temp_key = '@%s{}' % _get_random_string()
            content = content.replace(whole, temp_key)
            inner_improvements.append(
                (temp_key, improved)
            )

        _regex = re.compile('((.*?){(.*?)})', re.DOTALL | re.M)

        def matcher(match):
            whole, selectors, bulk = match.groups()
            if selectors.strip().startswith('@'):
                return whole

            improved = selectors
            perfect = True
            for selector in [x for x in
                             selectors.split(',')
                             if x.strip()]:
                #print "\t", repr(selector)
                if selector.strip() in EXCEPTIONAL_SELECTORS:
                    pass
                elif not self._found(bodies, selector.strip()):
                    perfect = False
                    improved = re.sub('%s,?\s*' % re.escape(selector.strip()), '', improved)

            if perfect:
                pass
            if improved != selectors:
                if not improved.strip():
                    return ''
                else:
                    if improved.count(',') == 1:
                        left = [x.strip() for x in improved.split(',')
                                if x.strip()]
                        if len(left) == 1:
                            #print "\t\tIMPROVED", repr(improved)
                            improved = re.sub(',\s*$', ' ', improved)
                            #improved = re.sub('\s\s+', ' ', improved)
                    whole = whole.replace(selectors, improved)
            return whole

        fixed = _regex.sub(matcher, content)
        for original, improved in inner_improvements:
            fixed = fixed.replace(original, improved)
        return fixed

    def _get_contents(self, match, original_content):
        open_braces = 1  # we are starting the character after the first opening brace
        position = match.end()
        content = ""
        while open_braces > 0:
            c = original_content[position]
            if c == "{":
                open_braces += 1
            if c == "}":
                open_braces -= 1
            content += c
            position += 1
        return (content[:-1].strip(), original_content[match.start():position])  # the last closing brace gets captured, drop it

    def _found(self, bodies, selector):
        selector = selector.split(':')[0]
        #print "SEARCH FOR", repr(selector)
        if '}' in selector:
            return

        for body in bodies:
            #print "SELECTOR", repr(selector)
            try:
                for each in CSSSelector(selector)(body):
                    return True
            except SelectorSyntaxError:
                print >>sys.stderr, "TROUBLEMAKER"
                print >>sys.stderr, repr(selector)
            except ExpressionError, msg:
                print >>sys.stderr, "EXPRESSIONERROR"
                print >>sys.stderr, repr(selector)
        return False

    def make_absolute_url(self, url, href):
        parsed = urlparse(url)
        if href.startswith('//'):
            return parsed.scheme + ':' + href
        if href.startswith('/'):
            return parsed.scheme + '://' + parsed.netloc + href
        path = parsed.path
        parts = path.split('/')
        parts[-1] = href
        path = '/'.join(parts)
        return parsed.scheme + '://' + parsed.netloc + path


class _Result(object):
    def __init__(self, before, after):
        self.before = before
        self.after = after


class InlineResult(_Result):

    def __init__(self, line, url, *args):
        self.line = line
        self.url = url
        super(InlineResult, self).__init__(*args)


class LinkResult(_Result):

    def __init__(self, href, url, *args):
        self.href = href
        self.url = url
        super(LinkResult, self).__init__(*args)
