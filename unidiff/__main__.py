# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2014-2023 Matias Bordese
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.


"""Command line entry point for unidiff.

Examples:
    $ git diff | unidiff
    $ hg diff | unidiff --show-diff
    $ unidiff -f patch.diff
    $ python -m unidiff -f patch.diff
"""

import argparse
import sys

from unidiff import DEFAULT_ENCODING, PatchSet


DESCRIPTION = """Unified diff metadata.

Examples:
    $ git diff | unidiff
    $ hg diff | unidiff --show-diff
    $ unidiff -f patch.diff

"""


def get_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION)
    parser.add_argument('--show-diff', action="store_true", default=False,
                        dest='show_diff', help='output diff to stdout')
    parser.add_argument('-f', '--file', dest='diff_file',
                        type=argparse.FileType('r'),
                        help='if not specified, read diff data from stdin')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    encoding = DEFAULT_ENCODING
    if args.diff_file:
        diff_file = args.diff_file
    else:
        encoding = sys.stdin.encoding or encoding
        diff_file = sys.stdin

    patch = PatchSet(diff_file, metadata_only=(not args.show_diff))

    if args.show_diff:
        print(patch)
        print()

    print('Summary')
    print('-------')
    additions = 0
    deletions = 0
    renamed_files = 0
    for f in patch:
        if f.is_binary_file:
            print('%s:' % f.path, '(binary file)')
        else:
            additions += f.added
            deletions += f.removed
            print('%s:' % f.path, '+%d additions,' % f.added,
                  '-%d deletions' % f.removed)
        renamed_files = renamed_files + 1 if f.is_rename else renamed_files

    print()
    print('%d modified file(s), %d added file(s), %d removed file(s)' % (
        len(patch.modified_files), len(patch.added_files),
        len(patch.removed_files)))
    if renamed_files:
        print('%d file(s) renamed' % renamed_files)
    print('Total: %d addition(s), %d deletion(s)' % (additions, deletions))


if __name__ == '__main__':
    main()
