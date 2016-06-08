#!/usr/bin/env python
from __future__ import print_function
import sys, os
import time
sys.path.insert(0, os.path.abspath('.'))
from mincss.processor import Processor

DEFAULT_URL = 'http://localhost:9000/page.html'

def run(url):
    p = Processor()
    t0 = time.time()
    p.process(url)
    t1 = time.time()

    print("INLINES ".ljust(79, '-'))
    total_size_before = 0
    total_size_after = 0
    # for each in p.inlines:
    #     print("On line %s" % each.line)
    #     print('- ' * 40)
    #     print("BEFORE")
    #     print(each.before)
    #     total_size_before += len(each.before)
    #     print('- ' * 40)
    #     print("AFTER:")
    #     print(each.after)
    #     total_size_after += len(each.after)
    #     print("\n")
    #
    # print("LINKS ".ljust(79, '-'))
    # for each in p.links:
    #     print("On href %s" % each.href)
    #     print('- ' * 40)
    #     print("BEFORE")
    #     print(each.before)
    #     total_size_before += len(each.before)
    #     print('- ' * 40)
    #     print("AFTER:")
    #     print(each.after)
    #     print("\n")
    #
    # print("LINKS ".ljust(79, '-'))
    # for each in p.links:
    #     print("On href %s" % each.href)
    #     print('- ' * 40)
    #     print("BEFORE")
    #     print(each.before)
    #     total_size_before += len(each.before)
    #     print('- ' * 40)
    #     print("AFTER:")
    #     print(each.after)
    #     total_size_after += len(each.after)
    #     print("\n")

    print(
        "TOOK:".ljust(20),
        "%.5fs" % (t1 - t0)
    )
    print(
        "TOTAL SIZE BEFORE:".ljust(20),
        "%.1fKb" % (total_size_before / 1024.0)
    )
    print(
        "TOTAL SIZE AFTER:".ljust(20),
        "%.1fKb" % (total_size_after / 1024.0)
    )


if __name__ == '__main__':
    urls = sys.argv[1:]
    if not urls:
        urls = [DEFAULT_URL]
    for url in urls:
        run(url)
