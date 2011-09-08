# -*- coding: utf-8 -*-
# Author: Matías Bordese

"""Classes used by the unified diff parser to keep the diff data."""

import difflib
import re

from utils import RE_HUNK_HEADER

class Hunk(object):
    """Each of the modified blocks of a file."""

    def __init__(self, src_start=0, src_len=0, tgt_start=0, tgt_len=0):
        self.source_start = int(src_start)
        self.source_length = int(src_len)
        self.target_start = int(tgt_start)
        self.target_length = int(tgt_len)
        self.source_lines = []
        self.target_lines = []
        self.modified = 0
        self.added = 0
        self.deleted = 0
        self._unidiff_generator = None

    def __repr__(self):
        return "<@@ %d,%d %d,%d @@>" % (self.source_start, self.source_length,
                                        self.target_start, self.target_length)

    def as_unified_diff(self):
        """Output hunk data in unified diff format."""
        if self._unidiff_generator is None:
            self._unidiff_generator = difflib.unified_diff(self.source_lines,
                                                           self.target_lines)
            # throw the header information
            for i in range(3):
                self._unidiff_generator.next()

        head = "@@ -%d,%d +%d,%d @@\n" % (self.source_start, self.source_length,
                                          self.target_start, self.target_length)
        yield head
        while True:
            yield self._unidiff_generator.next()

    def is_valid(self):
        """Check hunk header data matches entered lines info."""
        return (len(self.source_lines) == self.source_length and 
                len(self.target_lines) == self.target_length)

    def append_context_line(self, line):
        """Add a new context line to the hunk."""
        self.source_lines.append(line)
        self.target_lines.append(line)

    def append_added_line(self, line):
        """Add a new added line to the hunk."""
        self.target_lines.append(line)
        self.added += 1

    def append_deleted_line(self, line):
        """Add a new deleted line to the hunk."""
        self.source_lines.append(line)
        self.deleted += 1

    def add_to_modified_counter(self, mods):
        """Update the number of lines modified in the hunk."""
        self.deleted -= mods
        self.added -= mods
        self.modified += mods


class PatchedFile(list):
    """Data from a patched file."""

    def __init__(self, source='', target=''):
        self.source_file = source
        self.target_file = target

    def __repr__(self):
        return "%s: %s" % (self.target_file,
                           super(PatchedFile, self).__repr__())

    def as_unified_diff(self):
        """Output file changes in unified diff format."""
        source = "--- %s\n" % self.source_file
        yield source
        
        target = "+++ %s\n" % self.target_file
        yield target
        
        for hunk in self:
            hunk_data = hunk.as_unified_diff()
            for line in hunk_data:
                yield line

    @property
    def path(self):
        #TODO: improve git/hg detection
        if self.source_file.startswith('a/') and self.target_file.startswith('b/'):
            filepath = self.source_file[2:]
        elif self.source_file.startswith('a/') and self.target_file == '/dev/null':
            filepath = self.source_file[2:]
        elif self.target_file.startswith('b/') and self.source_file == '/dev/null':
            filepath = self.target_file[2:]
        else:
            filepath = self.source_file
        return filepath 

    @property
    def added(self):
        """Return the file total added lines."""
        return sum([hunk.added for hunk in self])

    @property
    def deleted(self):
        """Return the file total deleted lines."""
        return sum([hunk.deleted for hunk in self])

    @property
    def modified(self):
        """Return the file total modified lines."""
        return sum([hunk.modified for hunk in self])

    @property
    def is_added_file(self):
        """Return True if this a file added by the patch."""
        return (len(self) == 1 and self[0].source_start == 0 and
                self[0].source_length == 0)

    @property
    def is_deleted_file(self):
        """Return True if this a file deleted by the patch."""
        return (len(self) == 1 and self[0].target_start == 0 and 
                self[0].target_length == 0)

    def is_modified_file(self):
        """Return True if this a file modified by the patch."""
        return not (self.is_added_file or self.is_deleted_file)


class PatchSet(list):
    """Full patch data."""

    def as_unified_diff(self):
        """Output patch data in unified diff format.
        
        It won't necessarily match the original unified diff,
        but it should be equivalent.
        """
        for patched_file in self:
            data = patched_file.as_unified_diff()
            for line in data:
                yield line


