# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2014 Matias Bordese
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


"""Unified diff parser module."""

from unidiff.patch import (
    Hunk,
    Line,
    PatchedFile,
    PatchSet
)
from unidiff.constants import (
    LINE_TYPE_ADDED,
    LINE_TYPE_CONTEXT,
    LINE_TYPE_REMOVED,
    RE_HUNK_BODY_LINE,
    RE_HUNK_HEADER,
    RE_SOURCE_FILENAME,
    RE_TARGET_FILENAME,
)
from unidiff.errors import UnidiffParseError


def _parse_hunk(diff, source_start, source_len, target_start, target_len,
                section_header):
    """Parse a diff hunk details."""
    hunk = Hunk(source_start, source_len, target_start, target_len,
                section_header)
    source_line_no = hunk.source_start
    target_line_no = hunk.target_start

    for line in diff:
        valid_line = RE_HUNK_BODY_LINE.match(line)
        if not valid_line:
            raise UnidiffParseError('Hunk diff line expected: %s' % line)

        line_type = valid_line.group('line_type')
        value = valid_line.group('value')
        original_line = Line(value, line_type=line_type)
        if line_type == LINE_TYPE_ADDED:
            original_line.target_line_no = target_line_no
            target_line_no += 1
        elif line_type == LINE_TYPE_REMOVED:
            original_line.source_line_no = source_line_no
            source_line_no += 1
        elif line_type == LINE_TYPE_CONTEXT:
            original_line.target_line_no = target_line_no
            target_line_no += 1
            original_line.source_line_no = source_line_no
            source_line_no += 1
        else:
            original_line = None

        if original_line:
            hunk.append(original_line)

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
            source_timestamp = check_source.group('timestamp')
            current_patch = None
            continue

        # check for target file header
        check_target = RE_TARGET_FILENAME.match(line)
        if check_target:
            target_file = check_target.group('filename')
            target_timestamp = check_target.group('timestamp')
            current_patch = PatchedFile(source_file, target_file,
                                        source_timestamp, target_timestamp)
            ret.append(current_patch)
            continue

        # check for hunk header
        re_hunk_header = RE_HUNK_HEADER.match(line)
        if re_hunk_header:
            hunk_info = re_hunk_header.groups()
            hunk = _parse_hunk(diff, *hunk_info)
            current_patch.append(hunk)
    return ret

#parse:
    #get source/target files
    #get hunk info/parse hunk
