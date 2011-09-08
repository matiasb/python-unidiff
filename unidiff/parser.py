# -*- coding: utf-8 -*-
# Author: Matías Bordese


"""Unified diff parser module."""

import re

from patch import PatchSet, PatchedFile, Hunk
from utils import (RE_SOURCE_FILENAME, RE_TARGET_FILENAME,
                   RE_HUNK_HEADER, RE_HUNK_BODY_LINE)


class UnidiffParseException(Exception):
    pass


def _parse_hunk(diff, source_start, source_len, target_start, target_len):
    hunk = Hunk(source_start, source_len, target_start, target_len)
    modified = 0
    deleting = 0
    for line in diff:
        valid_line = RE_HUNK_BODY_LINE.match(line)
        if valid_line:
            action = valid_line.group(0)
            original_line = line[1:]
            if action == '+':
                hunk.append_added_line(original_line)
                # modified lines == deleted immediately followed by added
                if deleting > 0:
                    modified += 1
                    deleting -= 1
            elif action == '-':
                hunk.append_deleted_line(original_line)
                deleting += 1
            elif action == ' ':
                hunk.append_context_line(original_line)
                hunk.add_to_modified_counter(modified)
                # reset modified auxiliar variables
                deleting = 0
                modified = 0
        else:
            raise UnidiffParseException('Hunk diff data expected')

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

