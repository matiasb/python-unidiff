# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2014-2017 Matias Bordese
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


"""Tests for the unified diff parser process."""

from __future__ import unicode_literals

import codecs
import os.path
import unittest

from unidiff import PatchSet
from unidiff.patch import PY2
from unidiff.errors import UnidiffParseError

if not PY2:
    unicode = str

class TestUnidiffParser(unittest.TestCase):
    """Tests for Unified Diff Parser."""

    def setUp(self):
        super(TestUnidiffParser, self).setUp()
        self.samples_dir = os.path.dirname(os.path.realpath(__file__))
        self.sample_file = os.path.join(
            self.samples_dir, 'samples/sample0.diff')
        self.sample_bad_file = os.path.join(
            self.samples_dir, 'samples/sample1.diff')

    def test_missing_encoding(self):
        utf8_file = os.path.join(self.samples_dir, 'samples/sample3.diff')
        # read bytes
        with open(utf8_file, 'rb') as diff_file:
            if PY2:
                self.assertRaises(UnicodeDecodeError, PatchSet, diff_file)
            else:
                # unicode expected
                self.assertRaises(TypeError, PatchSet, diff_file)

    def test_encoding_param(self):
        utf8_file = os.path.join(self.samples_dir, 'samples/sample3.diff')
        with open(utf8_file, 'rb') as diff_file:
            res = PatchSet(diff_file, encoding='utf-8')

        # 3 files updated by diff
        self.assertEqual(len(res), 3)
        added_unicode_line = res.added_files[0][0][1]
        self.assertEqual(added_unicode_line.value, 'holá mundo!\n')

    def test_no_newline_at_end_of_file(self):
        utf8_file = os.path.join(self.samples_dir, 'samples/sample3.diff')
        with open(utf8_file, 'rb') as diff_file:
            res = PatchSet(diff_file, encoding='utf-8')

        # 3 files updated by diff
        self.assertEqual(len(res), 3)
        added_unicode_line = res.added_files[0][0][4]
        self.assertEqual(added_unicode_line.line_type, '\\')
        self.assertEqual(added_unicode_line.value, ' No newline at end of file\n')
        added_unicode_line = res.modified_files[0][0][8]
        self.assertEqual(added_unicode_line.line_type, '\\')
        self.assertEqual(added_unicode_line.value, ' No newline at end of file\n')

    def test_preserve_dos_line_endings(self):
        utf8_file = os.path.join(self.samples_dir, 'samples/sample4.diff')
        with open(utf8_file, 'rb') as diff_file:
            res = PatchSet(diff_file, encoding='utf-8')

        # 3 files updated by diff
        self.assertEqual(len(res), 3)
        added_unicode_line = res.added_files[0][0][1]
        self.assertEqual(added_unicode_line.value, 'holá mundo!\r\n')

    def test_preserve_dos_line_endings_empty_line_type(self):
        utf8_file = os.path.join(self.samples_dir, 'samples/sample5.diff')
        with open(utf8_file, 'rb') as diff_file:
            res = PatchSet(diff_file, encoding='utf-8')

        # 2 files updated by diff
        self.assertEqual(len(res), 2)
        modified_unicode_line = res.modified_files[0][0][6]
        self.assertEqual(modified_unicode_line.value, '\r\n')
        self.assertEqual(modified_unicode_line.line_type, ' ')

        modified_unicode_line = res.modified_files[1][0][6]
        self.assertEqual(modified_unicode_line.value, '\n')
        self.assertEqual(modified_unicode_line.line_type, ' ')

    def test_print_hunks_without_gaps(self):
        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            res = PatchSet(diff_file)
        lines = unicode(res).splitlines()
        self.assertEqual(lines[12], '@@ -5,16 +11,10 @@')
        self.assertEqual(lines[31], '@@ -22,3 +22,7 @@')

    def test_parse_sample(self):
        """Parse sample file."""
        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            res = PatchSet(diff_file)

        # three file in the patch
        self.assertEqual(len(res), 3)
        # three hunks
        self.assertEqual(len(res[0]), 3)

        # first file is modified
        self.assertTrue(res[0].is_modified_file)
        self.assertFalse(res[0].is_removed_file)
        self.assertFalse(res[0].is_added_file)

        # Hunk 1: five additions, no deletions, a section header
        self.assertEqual(res[0][0].added, 6)
        self.assertEqual(res[0][0].removed, 0)
        self.assertEqual(res[0][0].section_header, 'Section Header')

        # Hunk 2: 2 additions, 8 deletions, no section header
        self.assertEqual(res[0][1].added, 2)
        self.assertEqual(res[0][1].removed, 8)
        self.assertEqual(res[0][1].section_header, '')

        # Hunk 3: four additions, no deletions, no section header
        self.assertEqual(res[0][2].added, 4)
        self.assertEqual(res[0][2].removed, 0)
        self.assertEqual(res[0][2].section_header, '')

        # Check file totals
        self.assertEqual(res[0].added, 12)
        self.assertEqual(res[0].removed, 8)

        # second file is added
        self.assertFalse(res[1].is_modified_file)
        self.assertFalse(res[1].is_removed_file)
        self.assertTrue(res[1].is_added_file)

        # third file is removed
        self.assertFalse(res[2].is_modified_file)
        self.assertTrue(res[2].is_removed_file)
        self.assertFalse(res[2].is_added_file)

        self.assertEqual(res.added, 21)
        self.assertEqual(res.removed, 17)

    def test_patchset_compare(self):
        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            ps1 = PatchSet(diff_file)

        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            ps2 = PatchSet(diff_file)

        other_file = os.path.join(self.samples_dir, 'samples/sample3.diff')
        with open(other_file, 'rb') as diff_file:
            ps3 = PatchSet(diff_file, encoding='utf-8')

        self.assertEqual(ps1, ps2)
        self.assertNotEqual(ps1, ps3)

    def test_patchset_from_string(self):
        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            diff_data = diff_file.read()
            ps1 = PatchSet.from_string(diff_data)

        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            ps2 = PatchSet(diff_file)

        self.assertEqual(ps1, ps2)

    def test_patchset_from_bytes_string(self):
        with codecs.open(self.sample_file, 'rb') as diff_file:
            diff_data = diff_file.read()
            ps1 = PatchSet.from_string(diff_data, encoding='utf-8')

        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            ps2 = PatchSet(diff_file)

        self.assertEqual(ps1, ps2)

    def test_patchset_string_input(self):
        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            diff_data = diff_file.read()
            ps1 = PatchSet(diff_data)

        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            ps2 = PatchSet(diff_file)

        self.assertEqual(ps1, ps2)

    def test_parse_malformed_diff(self):
        """Parse malformed file."""
        with open(self.sample_bad_file) as diff_file:
            self.assertRaises(UnidiffParseError, PatchSet, diff_file)

    def test_parse_malformed_diff_longer_than_expected(self):
        """Parse malformed file with non-terminated hunk."""
        utf8_file = os.path.join(self.samples_dir, 'samples/sample6.diff')
        with open(utf8_file, 'r') as diff_file:
            self.assertRaises(UnidiffParseError, PatchSet, diff_file)

    def test_parse_malformed_diff_shorter_than_expected(self):
        """Parse malformed file with non-terminated hunk."""
        utf8_file = os.path.join(self.samples_dir, 'samples/sample7.diff')
        with open(utf8_file, 'r') as diff_file:
            self.assertRaises(UnidiffParseError, PatchSet, diff_file)

    def test_parse_diff_with_new_and_modified_binary_files(self):
        """Parse git diff file with newly added and modified binaries files."""
        utf8_file = os.path.join(self.samples_dir, 'samples/sample8.diff')
        with open(utf8_file, 'r') as diff_file:
            res = PatchSet(diff_file)

        # three file in the patch
        self.assertEqual(len(res), 3)

        # first file is added
        self.assertFalse(res[0].is_modified_file)
        self.assertFalse(res[0].is_removed_file)
        self.assertTrue(res[0].is_added_file)

        # second file is added
        self.assertTrue(res[1].is_modified_file)
        self.assertFalse(res[1].is_removed_file)
        self.assertFalse(res[1].is_added_file)

        # third file is removed
        self.assertFalse(res[2].is_modified_file)
        self.assertTrue(res[2].is_removed_file)
        self.assertFalse(res[2].is_added_file)

    def test_parse_round_trip_with_binary_files_in_diff(self):
        """Parse git diff with binary files though round trip"""
        utf8_file = os.path.join(self.samples_dir, 'samples/sample8.diff')
        with open(utf8_file, 'r') as diff_file:
            res1 = PatchSet(diff_file)

        res2 = PatchSet(str(res1))
        self.assertEqual(res1, res2)


    def test_diff_lines_linenos(self):
        with open(self.sample_file, 'rb') as diff_file:
            res = PatchSet(diff_file, encoding='utf-8')

        target_line_nos = []
        source_line_nos = []
        diff_line_nos = []
        for diff_file in res:
            for hunk in diff_file:
                for line in hunk:
                    target_line_nos.append(line.target_line_no)
                    source_line_nos.append(line.source_line_no)
                    diff_line_nos.append(line.diff_line_no)

        expected_target_line_nos = [
            # File: 1, Hunk: 1
            1, 2, 3, 4, 5, 6, 7, 8, 9,
            # File: 1, Hunk: 2
            11, 12, 13, None, None, None, None, None, None, None, 14, 15, 16, None, 17, 18, 19, 20,
            # File: 1, Hunk: 3
            22, 23, 24, 25, 26, 27, 28,
            # File: 2, Hunk 1
            1, 2, 3, 4, 5, 6, 7, 8, 9,
            # File: 3, Hunk 1
            None, None, None, None, None, None, None, None, None,
        ]
        expected_source_line_nos = [
            # File: 1, Hunk: 1
            None, None, None, None, None, None, 1, 2, 3,
            # File: 1, Hunk: 2
            5, 6, 7, 8, 9, 10, 11, 12, 13, 14, None, 15, 16, 17, None, 18, 19, 20,
            # File: 1, Hunk: 3
            22, 23, 24, None, None, None, None,
            # File: 2, Hunk 1
            None, None, None, None, None, None, None, None, None,
            # File: 3, Hunk 1
            1, 2, 3, 4, 5, 6, 7, 8, 9,
        ]
        expected_diff_line_nos = [
            # File: 1, Hunk: 1
            4, 5, 6, 7, 8, 9, 10, 11, 12,
            # File: 1, Hunk: 2
            14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31,
            # File: 1, Hunk: 3
            33, 34, 35, 36, 37, 38, 39,
            # File: 2, Hunk 1
            43, 44, 45, 46, 47, 48, 49, 50, 51,
            # File: 3, Hunk 1
            55, 56, 57, 58, 59, 60, 61, 62, 63,
        ]

        self.assertEqual(target_line_nos, expected_target_line_nos)
        self.assertEqual(source_line_nos, expected_source_line_nos)
        self.assertEqual(diff_line_nos, expected_diff_line_nos)


class TestVCSSamples(unittest.TestCase):
    """Tests for real examples from VCS."""

    samples = ['bzr.diff', 'git.diff', 'hg.diff', 'svn.diff']

    def test_samples(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for fname in self.samples:
            file_path = os.path.join(tests_dir, 'samples', fname)
            with codecs.open(file_path, 'r', encoding='utf-8') as diff_file:
                res = PatchSet(diff_file)

            # 3 files updated by diff
            self.assertEqual(len(res), 3)

            # 1 added file
            added_files = res.added_files
            self.assertEqual(len(added_files), 1)
            self.assertEqual(added_files[0].path, 'added_file')
            # 1 hunk, 4 lines
            self.assertEqual(len(added_files[0]), 1)
            self.assertEqual(added_files[0].added, 4)
            self.assertEqual(added_files[0].removed, 0)

            # 1 removed file
            removed_files = res.removed_files
            self.assertEqual(len(removed_files), 1)
            self.assertEqual(removed_files[0].path, 'removed_file')
            # 1 hunk, 3 removed lines
            self.assertEqual(len(removed_files[0]), 1)
            self.assertEqual(removed_files[0].added, 0)
            self.assertEqual(removed_files[0].removed, 3)

            # 1 modified file
            modified_files = res.modified_files
            self.assertEqual(len(modified_files), 1)
            self.assertEqual(modified_files[0].path, 'modified_file')
            # 1 hunk, 3 added lines, 1 removed line
            self.assertEqual(len(modified_files[0]), 1)
            self.assertEqual(modified_files[0].added, 3)
            self.assertEqual(modified_files[0].removed, 1)

            self.assertEqual(res.added, 7)
            self.assertEqual(res.removed, 4)

            # check that original diffs and those produced
            # by unidiff are the same
            with codecs.open(file_path, 'r', encoding='utf-8') as diff_file:
                self.assertEqual(diff_file.read(), str(res))
