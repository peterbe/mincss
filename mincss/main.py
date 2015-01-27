from __future__ import print_function

import io
import os
import time

from .processor import Processor


def run(args):
    options = {'debug': args.verbose}
    if args.phantomjs_path:
        options['phantomjs'] = args.phantomjs_path
    elif args.phantomjs:
        options['phantomjs'] = True
    p = Processor(**options)
    t0 = time.time()
    # args.url is actually a list
    p.process(*args.url)
    t1 = time.time()
    print('TOTAL TIME ', t1 - t0)
    for inline in p.inlines:
        print('ON', inline.url)
        print('AT line', inline.line)
        print('BEFORE '.ljust(79, '-'))
        print(inline.before)
        print('AFTER '.ljust(79, '-'))
        print(inline.after)
        print()

    output_dir = args.outputdir
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    for link in p.links:
        print('FOR', link.href)
        orig_name = link.href.split('/')[-1]
        with io.open(os.path.join(output_dir, orig_name), 'w') as f:
            f.write(link.after)
        before_name = 'before_' + link.href.split('/')[-1]
        with io.open(os.path.join(output_dir, before_name), 'w') as f:
            f.write(link.before)
        print('Files written to', output_dir)
        print()
        print(
            '(from %d to %d saves %d)' %
            (len(link.before), len(link.after),
             len(link.before) - len(link.after))
        )


def main():
    import argparse
    parser = argparse.ArgumentParser()
    add = parser.add_argument
    add('url', type=str,
        help='URL(s) to process', nargs="*")
    add('--outputdir', action='store',
        default='./output',
        help='directory where to put output (default ./output)')
    add('-v', '--verbose', action='store_true',
        help='increase output verbosity')
    add('--phantomjs', action='store_true',
        help='Use PhantomJS to download the source')
    add('--phantomjs-path', action='store',
        default='',
        help='Where is the phantomjs executable')

    args = parser.parse_args()
    return run(args) or 0
