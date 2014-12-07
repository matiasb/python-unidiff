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


"""Classes used by the unified diff parser to keep the diff data."""


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


class Line(object):
    """A diff line."""

    def __init__(self, value, line_type,
                 source_line_no=None, target_line_no=None):
        super(Line, self).__init__()
        self.source_line_no = source_line_no
        self.target_line_no = target_line_no
        self.line_type = line_type
        self.value = value

    def __str__(self):
        # PY3 -> unicode
        return self.value.encode('utf-8')

    def __unicode__(self):
        return self.value

    @property
    def is_added(self):
        return self.line_type == LINE_TYPE_ADDED

    @property
    def is_removed(self):
        return self.line_type == LINE_TYPE_REMOVED

    @property
    def is_context(self):
        return self.line_type == LINE_TYPE_CONTEXT

    def as_unified_diff(self):
        return '%s%s' % (self.line_type, self.value)


class Hunk(list):
    """Each of the modified blocks of a file."""

    def __init__(self, src_start=0, src_len=0, tgt_start=0, tgt_len=0,
                 section_header=''):
        if src_len is None:
            src_len = 1
        if tgt_len is None:
            tgt_len = 1
        self.source_start = int(src_start)
        self.source_length = int(src_len)
        self.target_start = int(tgt_start)
        self.target_length = int(tgt_len)
        self.section_header = section_header

    def __repr__(self):
        return "<@@ %d,%d %d,%d @@ %s>" % (self.source_start,
                                           self.source_length,
                                           self.target_start,
                                           self.target_length,
                                           self.section_header)

    def as_unified_diff(self):
        """Output hunk data in unified diff format."""
        head = "@@ -%d,%d +%d,%d @@ %s" % (
            self.source_start, self.source_length,
            self.target_start, self.target_length, self.section_header)
        yield head
        for line in self:
            yield line.as_unified_diff()

    def is_valid(self):
        """Check hunk header data matches entered lines info."""
        return (len(self.source) == self.source_length and
                len(self.target) == self.target_length)

    @property
    def added(self):
        return len([l for l in self if l.is_added])

    @property
    def removed(self):
        return len([l for l in self if l.is_removed])

    @property
    def source(self):
        return [unicode(l) for l in self.source_lines()]

    @property
    def target(self):
        return [unicode(l) for l in self.target_lines()]

    def source_lines(self):
        return (l for l in self if l.is_context or l.is_removed)

    def target_lines(self):
        return (l for l in self if l.is_context or l.is_added)


class PatchedFile(list):
    """Data of a patched file, each element is a Hunk."""

    def __init__(self, source='', target='',
                 source_timestamp=None, target_timestamp=None):
        super(PatchedFile, self).__init__()
        self.source_file = source
        self.source_timestamp = source_timestamp
        self.target_file = target
        self.target_timestamp = target_timestamp

    def __repr__(self):
        return "%s: %s" % (self.target_file,
                           super(PatchedFile, self).__repr__())

    def __str__(self):
        s = self.path + "\n"
        for e in enumerate([repr(e) for e in self]):
            s += "Hunk #%s: %s\n" % e
        s += "\n"
        return s

    def _parse_hunk(self, header, diff):
        """Parse hunk details."""
        header_info = RE_HUNK_HEADER.match(header)
        hunk_info = header_info.groups()
        hunk = Hunk(*hunk_info)

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

        self.append(hunk)

    def as_unified_diff(self):
        """Output file changes in unified diff format."""
        source = "--- %s" % self.source_file
        yield source

        target = "+++ %s" % self.target_file
        yield target

        for hunk in self:
            hunk_data = hunk.as_unified_diff()
            for line in hunk_data:
                yield line

    @property
    def path(self):
        """Return the file path abstracted from VCS."""
        if (self.source_file.startswith('a/') and
                self.target_file.startswith('b/')):
            filepath = self.source_file[2:]
        elif (self.source_file.startswith('a/') and
                self.target_file == '/dev/null'):
            filepath = self.source_file[2:]
        elif (self.target_file.startswith('b/') and
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
        return (len(self) == 1 and self[0].source_start == 0 and
                self[0].source_length == 0)

    @property
    def is_removed_file(self):
        """Return True if this patch removes the file."""
        return (len(self) == 1 and self[0].target_start == 0 and
                self[0].target_length == 0)

    @property
    def is_modified_file(self):
        """Return True if this patch modifies the file."""
        return not (self.is_added_file or self.is_removed_file)


class PatchSet(list):
    """A list of PatchedFiles."""

    def __init__(self, f):
        super(PatchSet, self).__init__()
        self._parse(f)

    def __str__(self):
        return ''.join([str(e) for e in self])

    def _parse(self, diff):
        current_file = None

        for line in diff:
            # check for source file header
            is_source_filename = RE_SOURCE_FILENAME.match(line)
            if is_source_filename:
                source_file = is_source_filename.group('filename')
                source_timestamp = is_source_filename.group('timestamp')
                # reset current file
                current_file = None
                continue

            # check for target file header
            is_target_filename = RE_TARGET_FILENAME.match(line)
            if is_target_filename:
                if current_file is not None:
                    raise UnidiffParseError('Target without source: %s' % line)
                target_file = is_target_filename.group('filename')
                target_timestamp = is_target_filename.group('timestamp')
                # add current file to PatchSet
                current_file = PatchedFile(source_file, target_file,
                                           source_timestamp, target_timestamp)
                self.append(current_file)
                continue

            # check for hunk header
            is_hunk_header = RE_HUNK_HEADER.match(line)
            if is_hunk_header:
                if current_file is None:
                    raise UnidiffParseError('Unexpected hunk found: %s' % line)
                current_file._parse_hunk(line, diff)

    @classmethod
    def from_filename(cls, filename):
        with open(filename, 'r') as f:
            instance = cls(f)
        return instance

    @property
    def added_files(self):
        return [f for f in self if f.is_added_file]

    @property
    def removed_files(self):
        return [f for f in self if f.is_removed_file]

    @property
    def modified_files(self):
        return [f for f in self if f.is_modified_file]

    def as_unified_diff(self):
        """Output patch data in unified diff format.

        It won't necessarily match the original unified diff,
        but it should be equivalent.
        """
        for patched_file in self:
            data = patched_file.as_unified_diff()
            for line in data:
                yield line
