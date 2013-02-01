#!/usr/bin/env python
import os
import sys

# make sure it's running the mincss here and not anything installed
sys.path.insert(0, os.path.dirname(__file__))
from mincss.processor import Processor

def run(args):
    options = {'debug': args.verbose}
    if args.phantomjs_path:
        options['phantomjs'] = args.phantomjs_path
    elif args.phantomjs:
        options['phantomjs'] = True
    p = Processor(**options)
    p.process(args.url)
    for inline in p.inlines:
        print "ON", inline.url
        print "AT line", inline.line
        print "BEFORE ".ljust(79, '-')
        print inline.before
        print "AFTER ".ljust(79, '-')
        print inline.after
        print

    _here = os.path.dirname(__file__)
    output_dir = args.outputdir
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    for link in p.links:
        print "FOR", link.href
        #print "BEFORE ".ljust(79, '-')
        #print link.before
        #print "AFTER ".ljust(79, '-')
        #print link.after
        with open(os.path.join(output_dir, link.href.split('/')[-1]), 'w') as f:
            f.write(link.after)
        with open(os.path.join(output_dir, 'before_' + link.href.split('/')[-1]), 'w') as f:
            f.write(link.before)
        print "Files written to", output_dir
        print
        print (
            '(from %d to %d saves %d)' %
            (len(link.before), len(link.after),
             len(link.before) - len(link.after))
        )

    return 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str,
                    help="URL to process")
    parser.add_argument("--outputdir", action="store",
                        default="./output",
                    help="directory where to put output (default ./output)")
    parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase output verbosity")
    parser.add_argument("--phantomjs", action="store_true",
                    help="Use PhantomJS to download the source")
    parser.add_argument("--phantomjs-path", action="store",
                        default="",
                    help="Where is the phantomjs executable")

    args = parser.parse_args()
    sys.exit(run(args))
