import collections
import re
from cStringIO import StringIO
from urlparse import urlparse
from pprint import pprint
import cssmin
from lxml import etree
from lxml.cssselect import CSSSelector, SelectorSyntaxError, ExpressionError
import pyquery
import urllib
import tinycss


EXCEPTIONAL_SELECTORS = (
    'html',
)

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

        parser = tinycss.make_parser('page3')
        stylesheet = parser.parse_stylesheet(content)
        for rule in stylesheet.rules:
            #print type(rule)
            #print dir(rule)
            #print repr(rule.at_keyword)
            #print repr(rule.selector)
            #print repr(rule.selector.as_css())
            selectors = rule.selector.as_css()
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
                    #print "\t\tREMOVE", repr(selector)
                    #print "\t\tBEFORE", repr(improved)
                    improved = re.sub('%s,?\s*' % re.escape(selector.strip()), '', improved)
                    #print "\t\tNOW:", repr(improved)
                #else:
                #    print "\t\tFOUND"

            if perfect:
                continue
            if improved != selectors:
                if not improved:
                    # there's nothing left!
                    # then delete the whole line
                    content = re.sub(
                        '%s\s*{.*?}\s*' % re.escape(selectors),
                        '',
                        content
                    )
                else:
                    if improved.count(',') == 1:
                        left = [x.strip() for x in improved.split(',')
                                if x.strip()]
                        if len(left) == 1:
                            improved = re.sub(',\s*', ' ', improved)
                            improved = re.sub('\s\s+', ' ', improved)
                    content = content.replace(selectors, improved.rstrip())
        return content

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
                print "TROUBLEMAKER"
                print repr(selector)
            except ExpressionError, msg:
                print "EXPRESSIONERROR"
                print repr(selector)
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
