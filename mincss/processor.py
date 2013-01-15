import sys
import collections
import random
import re
from urlparse import urlparse
from lxml import etree
from lxml.cssselect import CSSSelector, SelectorSyntaxError, ExpressionError
import urllib


RE_FIND_MEDIA = re.compile("(@media.+?)(\{)", re.DOTALL | re.MULTILINE)
RE_NESTS = re.compile('@(-|keyframes).*?({)', re.DOTALL | re.M)


EXCEPTIONAL_SELECTORS = (
    'html',
)


class ParserError(Exception):
    """happens when we fail to parse the HTML"""
    pass


class DownloadError(Exception):
    """happens when we fail to down the URL"""
    pass


def _get_random_string():
    p = 'abcdefghijklmopqrstuvwxyz'
    pl = list(p)
    random.shuffle(pl)
    return ''.join(pl)


class Processor(object):

    def __init__(self, debug=False):
        self.debug = debug
        self.tab = ' ' * 4
        self.blocks = {}
        #self.keep = collections.defaultdict(list)
        #self.blocks_bytes = {}
        self.inlines = []
        self.links = []
        self._bodies = []

    def _download(self, url):
        try:
            response = urllib.urlopen(url)
            if response.getcode() is not None:
                if response.getcode() != 200:
                    raise DownloadError(
                        '%s -- %s ' % (url, response.getcode())
                    )
            content = response.read()
            return unicode(content, 'utf-8')
        except IOError:
            raise IOError(url)

    def process(self, *urls):
        for url in urls:
            self.process_url(url)

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
                        #url,
                        content,
                        processed
                    )
                )

    def process_url(self, url):
        html = self._download(url)
        self.process_html(html.strip(), url=url)

    def process_html(self, html, url):
        parser = etree.HTMLParser()
        tree = etree.fromstring(html, parser).getroottree()
        page = tree.getroot()

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
                link.attrib['href'].lower().split('?')[0].endswith('.css')
            ):
                link_url = self._make_absolute_url(url, link.attrib['href'])
                key = (link_url, link.attrib['href'])
                self.blocks[key] = self._download(link_url)

    def _process_content(self, content, bodies):
        # Find all of the unique media queries

        comments = []
        _css_comments = re.compile(r'/\*.*?\*/', re.MULTILINE | re.DOTALL)
        no_mincss_blocks = []

        def commentmatcher(match):
            whole = match.group()
            # are we in a block or outside
            nearest_close = content[:match.start()].rfind('}')
            nearest_open = content[:match.start()].rfind('{')
            next_close = content[match.end():].find('}')
            next_open = content[match.end():].find('{')

            outside = False
            if nearest_open == -1 and nearest_close == -1:
                # it's at the very beginning of the file
                outside = True
            elif next_open == -1 and next_close == -1:
                # it's at the very end of the file
                outside = True
            elif nearest_close == -1 and nearest_open > -1:
                outside = False
            elif nearest_close > -1 and nearest_open > -1:
                outside = nearest_close > nearest_open
            else:
                raise Exception("can this happen?!")
                print repr(match.group())
                print "nearest", (nearest_close, nearest_open)
                print nearest_close < nearest_open
                #print "next", (next_close, next_open)
                print

            if outside:
                temp_key = '@%scomment{}' % _get_random_string()
            else:
                temp_key = '%sinnercomment' % _get_random_string()
                if re.findall(r'\bno mincss\b', match.group()):
                    no_mincss_blocks.append(temp_key)

            comments.append(
                (temp_key, whole)
            )
            return temp_key
        content = _css_comments.sub(commentmatcher, content)
        if no_mincss_blocks:
            no_mincss_regex = re.compile(
                '|'.join(re.escape(x) for x in no_mincss_blocks)
            )
        else:
            no_mincss_regex = None

        nests = [(m.group(1), m) for m in RE_NESTS.finditer(content)]
        _nests = []
        for start, m in nests:
            __, whole = self._get_contents(m, content)
            _nests.append(whole)
        # once all nests have been spotted, temporarily replace them

        queries = [(m.group(1), m) for m in RE_FIND_MEDIA.finditer(content)]
        inner_improvements = []

        for nest in _nests:
            temp_key = '@%snest{}' % _get_random_string()
            inner_improvements.append(
                (temp_key, nest, nest)
            )

        # Consolidate the media queries
        for (query, m) in queries:
            inner, whole = self._get_contents(m, content)
            improved_inner = self._process_content(inner, bodies)
            if improved_inner.strip():
                improved = query.rstrip() + ' {' + improved_inner + '}'
            else:
                improved = ''
            temp_key = '@%s{}' % _get_random_string()
            #content = content.replace(whole, temp_key)
            inner_improvements.append(
                (temp_key, whole, improved)
            )

        for temp_key, old, __ in inner_improvements:
            assert old in content
            content = content.replace(old, temp_key)

        _regex = re.compile('((.*?){(.*?)})', re.DOTALL | re.M)

        _already_found = set()
        _already_tried = set()

        def matcher(match):
            whole, selectors, bulk = match.groups()
            selectors = selectors.split('*/')[-1].lstrip()
            if selectors.strip().startswith('@'):
                return whole
            if no_mincss_regex and no_mincss_regex.findall(bulk):
                return no_mincss_regex.sub('', whole)

            improved = selectors
            perfect = True
            selectors_split = [
                x.strip() for x in
                selectors.split(',')
                if x.strip() and not x.strip().startswith(':')
            ]
            for selector in selectors_split:
                s = selector.strip()
                if s in EXCEPTIONAL_SELECTORS:
                    continue

                if s in _already_found:
                    found = True
                elif s in _already_tried:
                    found = False
                else:

                    found = self._found(bodies, s)

                if found:
                    _already_found.add(s)
                else:
                    _already_tried.add(s)
                    perfect = False
                    improved = re.sub(
                        '%s,?\s*' % re.escape(s),
                        '',
                        improved,
                        count=1
                    )

            if perfect:
                return whole
            if improved != selectors:
                if not improved.strip():
                    return ''
                else:
                    improved = re.sub(',\s*$', ' ', improved)
                    whole = whole.replace(selectors, improved)
            return whole

        fixed = _regex.sub(matcher, content)

        for temp_key, __, improved in inner_improvements:
            assert temp_key in fixed
            fixed = fixed.replace(temp_key, improved)
        for temp_key, whole in comments:
            # note, `temp_key` might not be in the `fixed` thing because the
            # comment could have been part of a selector that is entirely
            # removed
            fixed = fixed.replace(temp_key, whole)
        return fixed

    def _get_contents(self, match, original_content):
        # we are starting the character after the first opening brace
        open_braces = 1
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
        return (
            content[:-1].strip(),
            # the last closing brace gets captured, drop it
            original_content[match.start():position]
        )

    def _found(self, bodies, selector):
        #print "SELECTOR", repr(selector)
        r = self.__found(bodies, selector)
        #print "R", repr(r)
        return r

    def __found(self, bodies, selector):
        selector = selector.split(':')[0]

        if '}' in selector:
            # XXX does this ever happen any more?
            return

        for body in bodies:
            try:
                for each in CSSSelector(selector)(body):
                    return True
            except SelectorSyntaxError:
                print >>sys.stderr, "TROUBLEMAKER"
                print >>sys.stderr, repr(selector)
            except ExpressionError:
                print >>sys.stderr, "EXPRESSIONERROR"
                print >>sys.stderr, repr(selector)
        return False

    def _make_absolute_url(self, url, href):
        parsed = urlparse(url)
        if href.startswith('//'):
            return parsed.scheme + ':' + href
        if href.startswith('/'):
            return parsed.scheme + '://' + parsed.netloc + href
        if href.count('://'):
            return href
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

    def __init__(self, href, *args):
        self.href = href
        #self.url = url
        super(LinkResult, self).__init__(*args)
