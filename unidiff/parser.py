# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2012 Matias Bordese
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.


"""Unified diff parser module."""

from unidiff.patch import (
    LINE_TYPE_ADD,
    LINE_TYPE_DELETE,
    LINE_TYPE_CONTEXT,
    Hunk,
    PatchedFile,
    PatchSet
)
from unidiff.utils import (
    RE_HUNK_BODY_LINE,
    RE_HUNK_HEADER,
    RE_SOURCE_FILENAME,
    RE_TARGET_FILENAME,
)


class UnidiffParseException(Exception):
    """Exception when parsing the diff data."""
    pass


def _parse_hunk(diff, source_start, source_len, target_start, target_len,
                section_header):
    """Parse a diff hunk details."""
    hunk = Hunk(source_start, source_len, target_start, target_len,
                section_header)
    modified = 0
    deleting = 0
    for line in diff:
        valid_line = RE_HUNK_BODY_LINE.match(line)
        if not valid_line:
            raise UnidiffParseException('Hunk diff data expected')

        action = valid_line.group(0)
        original_line = line[1:]
        if action == LINE_TYPE_ADD:
            hunk.append_added_line(original_line)
            # modified lines == deleted immediately followed by added
            if deleting > 0:
                modified += 1
                deleting -= 1
        elif action == LINE_TYPE_DELETE:
            hunk.append_deleted_line(original_line)
            deleting += 1
        elif action == LINE_TYPE_CONTEXT:
            hunk.append_context_line(original_line)
            hunk.add_to_modified_counter(modified)
            # reset modified auxiliar variables
            deleting = 0
            modified = 0

        # check hunk len(old_lines) and len(new_lines) are ok
        if hunk.is_valid():
            break

    return hunk


def parse_unidiff(diff):
    """Unified diff parser, takes a file-like object as argument."""
    ret = PatchSet()
    current_patch = None

    for line in diff:
        # check for source file header
        check_source = RE_SOURCE_FILENAME.match(line)
        if check_source:
            source_file = check_source.group('filename')
            current_patch = None
            continue

        # check for target file header
        check_target = RE_TARGET_FILENAME.match(line)
        if check_target:
            target_file = check_target.group('filename')
            current_patch = PatchedFile(source_file, target_file)
            ret.append(current_patch)
            continue

        # check for hunk header
        re_hunk_header = RE_HUNK_HEADER.match(line)
        if re_hunk_header:
            hunk_info = re_hunk_header.groups()
            hunk = _parse_hunk(diff, *hunk_info)
            current_patch.append(hunk)
    return ret
