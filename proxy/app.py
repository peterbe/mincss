#!/usr/bin/env python
import codecs
import datetime
import os
import functools
import logging
import hashlib
import re
import urllib
import urlparse
import shutil

from lxml import etree
from lxml.cssselect import CSSSelector

from flask import Flask, abort, make_response, request
app = Flask(__name__)

import sys
# do this to help development
sys.path.insert(0, os.path.normpath('../'))
from mincss.processor import Processor


CACHE_DIR = os.path.join(
    os.path.dirname(__file__),
    '.cache'
)


@app.route("/cache/<path:path>")
def cache(path):
    source = os.path.join(CACHE_DIR, path)
    with open(source) as f:
        response = make_response(f.read())
        response.headers["Content-type"] = "text/css"
        return response


def download(url):
    html = urllib.urlopen(url).read()
    return unicode(html, 'utf-8')


@app.route("/<path:path>")
def proxy(path):
    if path == 'favicon.ico':
        abort(404)
    url = path
    if not path.count('://'):
        url = 'http://' + url

    query = urlparse.urlparse(request.url).query
    if query:
        url += '?%s' % query
    logging.info('Downloading %s' % url)
    html = download(url)

    p = Processor(debug=False)
    # since we've already download the HTML
    p.process_html(html, url)
    p.process()

    collect_stats = request.args.get('MINCSS_STATS', False)
    stats = []
    css_url_regex = re.compile('url\(([^\)]+)\)')

    def css_url_replacer(match, href=None):
        filename = match.groups()[0]
        bail = match.group()

        if (
            (filename.startswith('"') and filename.endswith('"')) or
            (filename.startswith("'") and filename.endswith("'"))
        ):
            filename = filename[1:-1]
        if 'data:image' in filename or '://' in filename:
            return bail
        if filename == '.':
            # this is a known IE hack in CSS
            return bail

        if not filename.startswith('/'):

            filename = os.path.normpath(
                os.path.join(
                    os.path.dirname(href),
                    filename
                )
            )

        new_filename = urlparse.urljoin(url, filename)
        return 'url("%s")' % new_filename

    for i, each in enumerate(p.inlines):
        # this should be using CSSSelector instead
        new_inline = each.after
        new_inline = css_url_regex.sub(
            functools.partial(css_url_replacer, href=url),
            new_inline
        )
        stats.append(
            ('inline %s' % (i + 1), each.before, each.after)
        )
        html = html.replace(each.before, new_inline)

    parser = etree.HTMLParser()
    stripped = html.strip()
    tree = etree.fromstring(stripped, parser).getroottree()
    page = tree.getroot()

    # lxml inserts a doctype if none exists, so only include it in
    # the root if it was in the original html.
    was_doctype = tree.docinfo.doctype
    #root = tree if stripped.startswith(tree.docinfo.doctype) else page

    links = dict((x.href, x) for x in p.links)

    #all_lines = html.splitlines()
    for link in CSSSelector('link')(page):
        if (
            link.attrib.get('rel', '') == 'stylesheet' or
            link.attrib['href'].lower().split('?')[0].endswith('.css')
        ):
            hash_ = hashlib.md5(url + link.attrib['href']).hexdigest()[:7]
            now = datetime.date.today()
            destination_dir = os.path.join(
                CACHE_DIR,
                str(now.year),
                str(now.month),
                str(now.day),
            )
            mkdir(destination_dir)
            new_css = links[link.attrib['href']].after
            stats.append((
                link.attrib['href'],
                links[link.attrib['href']].before,
                links[link.attrib['href']].after
            ))
            new_css = css_url_regex.sub(
                functools.partial(
                    css_url_replacer,
                    href=link.attrib['href']
                ),
                new_css
            )
            destination = os.path.join(destination_dir, hash_ + '.css')

            with codecs.open(destination, 'w', 'utf-8') as f:
                f.write(new_css)

            link.attrib['href'] = (
                '/cache%s' % destination.replace(CACHE_DIR, '')
            )

    for img in CSSSelector('img, script')(page):
        if 'src' in img.attrib:
            orig_src = urlparse.urljoin(url, img.attrib['src'])
            img.attrib['src'] = orig_src

    for a in CSSSelector('a')(page):
        if 'href' not in a.attrib:
            continue
        href = a.attrib['href']

        if (
            '://' in href or
            href.startswith('#') or
            href.startswith('javascript:')
        ):
            continue

        if href.startswith('/'):
            a.attrib['href'] = (
                '/' +
                urlparse.urljoin(url, a.attrib['href'])
                .replace('http://', '')
            )
        #else:
        if collect_stats:
            a.attrib['href'] = add_collect_stats_qs(
                a.attrib['href'],
                collect_stats
            )

    html = etree.tostring(page)
    if collect_stats:
        html = re.sub(
            '<body[^>]*>',
            lambda m: m.group() + summorize_stats_html(stats),
            html,
            flags=re.I | re.M,
            count=1
        )

    return (was_doctype and was_doctype or '') + '\n' + html


def add_collect_stats_qs(url, value):
    """
    if :url is `page.html?foo=bar`
    return `page.html?foo=bar&MINCSS_STATS=:value`
    """
    if '?' in url:
        url += '&'
    else:
        url += '?'
    url += 'MINCSS_STATS=%s' % value
    return url


def summorize_stats_html(stats):
    style = """
        font-size:10px;
        border:1px solid black;
        position:absolute;
        top:50px;
        right:5px;
        padding:4px;
        z-index:1001;
        background-color: white;
        color: black
    """
    template = """<div id="_mincss_stats"
    style="%s">
    <ul>
      %s
    </ul>
    </div>
    """
    lis = []
    total_before = total_after = 0
    for each, before, after in stats:
        total_before += len(before)
        total_after += len(after)
        lis.append(
            """<li>
            <strong>%s</strong>
            <ul>
              <li>before: %s</li>
              <li>after: %s</li>
            </ul>
            </li>""" %
            (
                each,
                sizeof(len(before)),
                sizeof(len(after))
            )
        )

    lis.append(
        """<li>
        <strong>TOTAL</strong>
        <ul>
          <li style="font-weigt:bold">before: %s</li>
          <li style="font-weigt:bold">after: %s</li>
          <li style="font-weigt:bold">saving: %s</li>
        </ul>
        </li>""" %
        (
            sizeof(total_before),
            sizeof(total_after),
            sizeof(total_before - total_after)
        )
    )
    style = style.strip().replace('\n', '')
    return template % (style, ('\n'.join(lis)))


def sizeof(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        return
    if os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired "
                      "dir, '%s', already exists." % newdir)
    head, tail = os.path.split(newdir)
    if head and not os.path.isdir(head):
        mkdir(head)
    if tail:
        os.mkdir(newdir)


_link_regex = re.compile('<link .*?>')
_href_regex = re.compile('href=[\'"]([^\'"]+)[\'"]')


def _find_link(line, href):
    for each in _link_regex.findall(line):
        for each_href in _href_regex.findall(each):
            if each_href == href:
                return each


if __name__ == "__main__":
    app.run(debug=True)
    try:
        shutil.rmtree(CACHE_DIR)
    except Exception:
        pass
