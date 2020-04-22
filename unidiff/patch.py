# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2014-2020 Matias Bordese
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


"""Classes used by the unified diff parser to keep the diff data."""

from __future__ import unicode_literals

import codecs
import sys

from unidiff.constants import (
    DEFAULT_ENCODING,
    LINE_TYPE_ADDED,
    LINE_TYPE_CONTEXT,
    LINE_TYPE_EMPTY,
    LINE_TYPE_REMOVED,
    LINE_TYPE_NO_NEWLINE,
    LINE_VALUE_NO_NEWLINE,
    RE_HUNK_BODY_LINE,
    RE_HUNK_EMPTY_BODY_LINE,
    RE_HUNK_HEADER,
    RE_RENAME_SOURCE_FILENAME,
    RE_RENAME_TARGET_FILENAME,
    RE_SOURCE_FILENAME,
    RE_TARGET_FILENAME,
    RE_NO_NEWLINE_MARKER,
    RE_BINARY_DIFF,
)
from unidiff.errors import UnidiffParseError


PY2 = sys.version_info[0] == 2
if PY2:
    from StringIO import StringIO
    open_file = codecs.open
    make_str = lambda x: x.encode(DEFAULT_ENCODING)

    def implements_to_string(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode(DEFAULT_ENCODING)
        return cls
else:
    from io import StringIO
    open_file = open
    make_str = str
    implements_to_string = lambda x: x
    unicode = str
    basestring = str


@implements_to_string
class Line(object):
    """A diff line."""

    def __init__(self, value, line_type,
                 source_line_no=None, target_line_no=None, diff_line_no=None):
        super(Line, self).__init__()
        self.source_line_no = source_line_no
        self.target_line_no = target_line_no
        self.diff_line_no = diff_line_no
        self.line_type = line_type
        self.value = value

    def __repr__(self):
        return make_str("<Line: %s%s>") % (self.line_type, self.value)

    def __str__(self):
        return "%s%s" % (self.line_type, self.value)

    def __eq__(self, other):
        return (self.source_line_no == other.source_line_no and
                self.target_line_no == other.target_line_no and
                self.diff_line_no == other.diff_line_no and
                self.line_type == other.line_type and
                self.value == other.value)

    @property
    def is_added(self):
        return self.line_type == LINE_TYPE_ADDED

    @property
    def is_removed(self):
        return self.line_type == LINE_TYPE_REMOVED

    @property
    def is_context(self):
        return self.line_type == LINE_TYPE_CONTEXT


@implements_to_string
class PatchInfo(list):
    """Lines with extended patch info.

    Format of this info is not documented and it very much depends on
    patch producer.

    """

    def __repr__(self):
        value = "<PatchInfo: %s>" % self[0].strip()
        return make_str(value)

    def __str__(self):
        return ''.join(unicode(line) for line in self)


@implements_to_string
class Hunk(list):
    """Each of the modified blocks of a file."""

    def __init__(self, src_start=0, src_len=0, tgt_start=0, tgt_len=0,
                 section_header=''):
        super(Hunk, self).__init__()
        if src_len is None:
            src_len = 1
        if tgt_len is None:
            tgt_len = 1
        self.source_start = int(src_start)
        self.source_length = int(src_len)
        self.target_start = int(tgt_start)
        self.target_length = int(tgt_len)
        self.section_header = section_header
        self._added = None
        self._removed = None

    def __repr__(self):
        value = "<Hunk: @@ %d,%d %d,%d @@ %s>" % (self.source_start,
                                                  self.source_length,
                                                  self.target_start,
                                                  self.target_length,
                                                  self.section_header)
        return make_str(value)

    def __str__(self):
        # section header is optional and thus we output it only if it's present
        head = "@@ -%d,%d +%d,%d @@%s\n" % (
            self.source_start, self.source_length,
            self.target_start, self.target_length,
            ' ' + self.section_header if self.section_header else '')
        content = ''.join(unicode(line) for line in self)
        return head + content

    def append(self, line):
        """Append the line to hunk, and keep track of source/target lines."""
        # Make sure the line is encoded correctly. This is a no-op except for
        # potentially raising a UnicodeDecodeError.
        str(line)
        super(Hunk, self).append(line)

    @property
    def added(self):
        if self._added is not None:
            return self._added
        # re-calculate each time to allow for hunk modifications
        # (which should mean metadata_only switch wasn't used)
        return sum(1 for line in self if line.is_added)

    @property
    def removed(self):
        if self._removed is not None:
            return self._removed
        # re-calculate each time to allow for hunk modifications
        # (which should mean metadata_only switch wasn't used)
        return sum(1 for line in self if line.is_removed)

    def is_valid(self):
        """Check hunk header data matches entered lines info."""
        return (len(self.source) == self.source_length and
                len(self.target) == self.target_length)

    def source_lines(self):
        """Hunk lines from source file (generator)."""
        return (l for l in self if l.is_context or l.is_removed)

    @property
    def source(self):
        return [str(l) for l in self.source_lines()]

    def target_lines(self):
        """Hunk lines from target file (generator)."""
        return (l for l in self if l.is_context or l.is_added)

    @property
    def target(self):
        return [str(l) for l in self.target_lines()]


class PatchedFile(list):
    """Patch updated file, it is a list of Hunks."""

    def __init__(self, patch_info=None, source='', target='',
                 source_timestamp=None, target_timestamp=None,
                 is_binary_file=False, is_rename=False):
        super(PatchedFile, self).__init__()
        self.patch_info = patch_info
        self.source_file = source
        self.source_timestamp = source_timestamp
        self.target_file = target
        self.target_timestamp = target_timestamp
        self.is_binary_file = is_binary_file
        self.is_rename = is_rename

    def __repr__(self):
        return make_str("<PatchedFile: %s>") % make_str(self.path)

    def __str__(self):
        source = ''
        target = ''
        # patch info is optional
        info = '' if self.patch_info is None else str(self.patch_info)
        if not self.is_binary_file and self:
            source = "--- %s%s\n" % (
                self.source_file,
                '\t' + self.source_timestamp if self.source_timestamp else '')
            target = "+++ %s%s\n" % (
                self.target_file,
                '\t' + self.target_timestamp if self.target_timestamp else '')
        hunks = ''.join(unicode(hunk) for hunk in self)
        return info + source + target + hunks

    def _parse_hunk(self, header, diff, encoding, metadata_only):
        """Parse hunk details."""
        header_info = RE_HUNK_HEADER.match(header)
        hunk_info = header_info.groups()
        hunk = Hunk(*hunk_info)

        source_line_no = hunk.source_start
        target_line_no = hunk.target_start
        expected_source_end = source_line_no + hunk.source_length
        expected_target_end = target_line_no + hunk.target_length
        added = 0
        removed = 0

        for diff_line_no, line in diff:
            if encoding is not None:
                line = line.decode(encoding)

            if metadata_only:
                # quick line type detection, no regex required
                line_type = line[0] if line else LINE_TYPE_CONTEXT
                if line_type not in (LINE_TYPE_ADDED,
                                     LINE_TYPE_REMOVED,
                                     LINE_TYPE_CONTEXT,
                                     LINE_TYPE_NO_NEWLINE):
                    raise UnidiffParseError(
                        'Hunk diff line expected: %s' % line)

                if line_type == LINE_TYPE_ADDED:
                    target_line_no += 1
                    added += 1
                elif line_type == LINE_TYPE_REMOVED:
                    source_line_no += 1
                    removed += 1
                elif line_type == LINE_TYPE_CONTEXT:
                    target_line_no += 1
                    source_line_no += 1

                # no file content tracking
                original_line = None

            else:
                # parse diff line content
                valid_line = RE_HUNK_BODY_LINE.match(line)
                if not valid_line:
                    valid_line = RE_HUNK_EMPTY_BODY_LINE.match(line)

                if not valid_line:
                    raise UnidiffParseError(
                        'Hunk diff line expected: %s' % line)

                line_type = valid_line.group('line_type')
                if line_type == LINE_TYPE_EMPTY:
                    line_type = LINE_TYPE_CONTEXT

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
                    original_line.source_line_no = source_line_no
                    target_line_no += 1
                    source_line_no += 1
                elif line_type == LINE_TYPE_NO_NEWLINE:
                    pass
                else:
                    original_line = None

            # stop parsing if we got past expected number of lines
            if (source_line_no > expected_source_end or
                    target_line_no > expected_target_end):
                raise UnidiffParseError('Hunk is longer than expected')

            if original_line:
                original_line.diff_line_no = diff_line_no
                hunk.append(original_line)

            # if hunk source/target lengths are ok, hunk is complete
            if (source_line_no == expected_source_end and
                    target_line_no == expected_target_end):
                break

        # report an error if we haven't got expected number of lines
        if (source_line_no < expected_source_end or
                target_line_no < expected_target_end):
            raise UnidiffParseError('Hunk is shorter than expected')

        if metadata_only:
            # HACK: set fixed calculated values when metadata_only is enabled
            hunk._added = added
            hunk._removed = removed

        self.append(hunk)

    def _add_no_newline_marker_to_last_hunk(self):
        if not self:
            raise UnidiffParseError(
                'Unexpected marker:' + LINE_VALUE_NO_NEWLINE)
        last_hunk = self[-1]
        last_hunk.append(
            Line(LINE_VALUE_NO_NEWLINE + '\n', line_type=LINE_TYPE_NO_NEWLINE))

    def _append_trailing_empty_line(self):
        if not self:
            raise UnidiffParseError('Unexpected trailing newline character')
        last_hunk = self[-1]
        last_hunk.append(Line('\n', line_type=LINE_TYPE_EMPTY))

    @property
    def path(self):
        """Return the file path abstracted from VCS."""
        if (self.source_file.startswith('a/') and
                self.target_file.startswith('b/')):
            filepath = self.source_file[2:]
        elif (self.source_file.startswith('a/') and
              self.target_file == '/dev/null'):
            filepath = self.source_file[2:]
        elif (self.target_file is not None and
              self.target_file.startswith('b/') and
              self.source_file == '/dev/null'):
            filepath = self.target_file[2:]
        else:
            filepath = self.source_file
        return filepath

    @property
    def added(self):
        """Return the file total added lines."""
        return sum([hunk.added for hunk in self])

    @property
    def removed(self):
        """Return the file total removed lines."""
        return sum([hunk.removed for hunk in self])

    @property
    def is_added_file(self):
        """Return True if this patch adds the file."""
        if self.source_file == '/dev/null':
            return True
        return (len(self) == 1 and self[0].source_start == 0 and
                self[0].source_length == 0)

    @property
    def is_removed_file(self):
        """Return True if this patch removes the file."""
        if self.target_file == '/dev/null':
            return True
        return (len(self) == 1 and self[0].target_start == 0 and
                self[0].target_length == 0)

    @property
    def is_modified_file(self):
        """Return True if this patch modifies the file."""
        return not (self.is_added_file or self.is_removed_file)


@implements_to_string
class PatchSet(list):
    """A list of PatchedFiles."""

    def __init__(self, f, encoding=None, metadata_only=False):
        super(PatchSet, self).__init__()

        # convert string inputs to StringIO objects
        if isinstance(f, basestring):
            f = self._convert_string(f, encoding)

        # make sure we pass an iterator object to parse
        data = iter(f)
        # if encoding is None, assume we are reading unicode data
        # when metadata_only is True, only perform a minimal metadata parsing
        # (ie. hunks without content) which is around 2.5-6 times faster;
        # it will still validate the diff metadata consistency and get counts
        self._parse(data, encoding=encoding, metadata_only=metadata_only)

    def __repr__(self):
        return make_str('<PatchSet: %s>') % super(PatchSet, self).__repr__()

    def __str__(self):
        return ''.join(unicode(patched_file) for patched_file in self)

    def _parse(self, diff, encoding, metadata_only):
        current_file = None
        patch_info = None

        diff = enumerate(diff, 1)
        for unused_diff_line_no, line in diff:
            if encoding is not None:
                line = line.decode(encoding)

            # check for a git rename, source file
            is_rename_source_filename = RE_RENAME_SOURCE_FILENAME.match(line)
            if is_rename_source_filename:
                # prefix with 'a/' to match expected git source format
                source_file = (
                    'a/' + is_rename_source_filename.group('filename'))
                # keep line as patch_info
                patch_info.append(line)
                # reset current file
                current_file = None
                continue

            # check for a git rename, target file
            is_rename_target_filename = RE_RENAME_TARGET_FILENAME.match(line)
            if is_rename_target_filename:
                if current_file is not None:
                    raise UnidiffParseError('Target without source: %s' % line)
                # prefix with 'b/' to match expected git source format
                target_file = (
                    'b/' + is_rename_target_filename.group('filename'))
                # keep line as patch_info
                patch_info.append(line)
                # add current file to PatchSet
                current_file = PatchedFile(
                    patch_info, source_file, target_file, None, None,
                    is_rename=True)
                self.append(current_file)
                continue

            # check for source file header
            is_source_filename = RE_SOURCE_FILENAME.match(line)
            if is_source_filename:
                source_file = is_source_filename.group('filename')
                source_timestamp = is_source_filename.group('timestamp')
                # reset current file, unless we are processing a rename
                # (in that case, source files should match)
                if current_file is not None and not (current_file.is_rename and
                        current_file.source_file == source_file):
                    current_file = None
                continue

            # check for target file header
            is_target_filename = RE_TARGET_FILENAME.match(line)
            if is_target_filename:
                if current_file is not None and not current_file.is_rename:
                    raise UnidiffParseError('Target without source: %s' % line)
                target_file = is_target_filename.group('filename')
                target_timestamp = is_target_filename.group('timestamp')
                if current_file is None:
                    # add current file to PatchSet
                    current_file = PatchedFile(
                        patch_info, source_file, target_file,
                        source_timestamp, target_timestamp)
                    self.append(current_file)
                    patch_info = None
                continue

            # check for hunk header
            is_hunk_header = RE_HUNK_HEADER.match(line)
            if is_hunk_header:
                if current_file is None:
                    raise UnidiffParseError('Unexpected hunk found: %s' % line)
                current_file._parse_hunk(line, diff, encoding, metadata_only)
                continue

            # check for no newline marker
            is_no_newline = RE_NO_NEWLINE_MARKER.match(line)
            if is_no_newline:
                if current_file is None:
                    raise UnidiffParseError('Unexpected marker: %s' % line)
                current_file._add_no_newline_marker_to_last_hunk()
                continue

            # sometimes hunks can be followed by empty lines
            if line == '\n' and current_file is not None:
                current_file._append_trailing_empty_line()
                continue

            is_binary_diff = RE_BINARY_DIFF.match(line)
            if is_binary_diff:
                source_file = is_binary_diff.group('source_filename')
                target_file = is_binary_diff.group('target_filename')
                patch_info.append(line)
                current_file = PatchedFile(
                    patch_info, source_file, target_file, is_binary_file=True)
                self.append(current_file)
                patch_info = None
                current_file = None
                continue

            # if nothing has matched above then this line is a patch info
            if patch_info is None:
                current_file = None
                patch_info = PatchInfo()
            patch_info.append(line)

    @classmethod
    def from_filename(cls, filename, encoding=DEFAULT_ENCODING, errors=None):
        """Return a PatchSet instance given a diff filename."""
        with open_file(filename, 'r', encoding=encoding, errors=errors) as f:
            instance = cls(f)
        return instance

    @staticmethod
    def _convert_string(data, encoding=None, errors='strict'):
        if encoding is not None:
            # if encoding is given, assume bytes and decode
            data = unicode(data, encoding=encoding, errors=errors)
        return StringIO(data)

    @classmethod
    def from_string(cls, data, encoding=None, errors='strict'):
        """Return a PatchSet instance given a diff string."""
        return cls(cls._convert_string(data, encoding, errors))

    @property
    def added_files(self):
        """Return patch added files as a list."""
        return [f for f in self if f.is_added_file]

    @property
    def removed_files(self):
        """Return patch removed files as a list."""
        return [f for f in self if f.is_removed_file]

    @property
    def modified_files(self):
        """Return patch modified files as a list."""
        return [f for f in self if f.is_modified_file]

    @property
    def added(self):
        """Return the patch total added lines."""
        return sum([f.added for f in self])

    @property
    def removed(self):
        """Return the patch total removed lines."""
        return sum([f.removed for f in self])
