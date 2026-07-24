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


"""Tests for the unified diff parser process."""

import codecs
import os.path
import unittest

from unidiff import PatchSet
from unidiff.errors import UnidiffParseError


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
        lines = str(res).splitlines()
        self.assertEqual(lines[12], '@@ -5,16 +11,10 @@')
        self.assertEqual(lines[31], '@@ -22,3 +22,7 @@')

    def _test_parse_sample(self, metadata_only):
        """Parse sample file."""
        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            res = PatchSet(diff_file, metadata_only=metadata_only)

        # three file in the patch
        self.assertEqual(len(res), 3)
        # three hunks
        self.assertEqual(len(res[0]), 3)

        # first file is modified
        self.assertTrue(res[0].is_modified_file)
        self.assertFalse(res[0].is_removed_file)
        self.assertFalse(res[0].is_added_file)
        self.assertFalse(res[0].is_binary_file)

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
        self.assertFalse(res[1].is_binary_file)

        # third file is removed
        self.assertFalse(res[2].is_modified_file)
        self.assertTrue(res[2].is_removed_file)
        self.assertFalse(res[2].is_added_file)
        self.assertFalse(res[2].is_binary_file)

        self.assertEqual(res.added, 21)
        self.assertEqual(res.removed, 17)

    def test_parse_sample_full(self):
        self._test_parse_sample(metadata_only=False)

    def test_parse_sample_metadata_only(self):
        self._test_parse_sample(metadata_only=True)

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

    def test_metadata_only_via_convenience_constructors(self):
        # from_filename and from_string should forward metadata_only (the
        # from_filename usage is documented in the README)
        ps_file = PatchSet.from_filename(
            self.sample_file, encoding='utf-8', metadata_only=True)
        with codecs.open(self.sample_file, 'r', encoding='utf-8') as diff_file:
            ps_string = PatchSet.from_string(diff_file.read(), metadata_only=True)

        # counts are still computed under metadata_only
        self.assertEqual((ps_file.added, ps_file.removed), (21, 17))
        self.assertEqual((ps_string.added, ps_string.removed), (21, 17))
        # metadata_only skips storing the line content
        self.assertEqual(len(ps_file[0][0]), 0)
        self.assertEqual(len(ps_string[0][0]), 0)

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

    def test_patchset_bytes_input(self):
        # issue #43: accept bytes directly so callers need not pre-decode;
        # with no encoding given, bytes default to UTF-8
        utf8_file = os.path.join(self.samples_dir, 'samples/sample3.diff')
        with open(utf8_file, 'rb') as diff_file:
            diff_bytes = diff_file.read()

        ps_default = PatchSet(diff_bytes)
        ps_explicit = PatchSet(diff_bytes, encoding='utf-8')
        with open(utf8_file, 'rb') as diff_file:
            ps_ref = PatchSet(diff_file, encoding='utf-8')

        self.assertEqual(ps_default, ps_ref)
        self.assertEqual(ps_explicit, ps_ref)
        # from_string also accepts bytes without an explicit encoding
        self.assertEqual(PatchSet.from_string(diff_bytes), ps_ref)

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

    def test_from_filename_with_cr_in_diff_text_files(self):
        """Parse git diff text files that contain CR"""
        utf8_file = os.path.join(self.samples_dir, 'samples/git_cr.diff')
        self.assertRaises(UnidiffParseError, PatchSet.from_filename, utf8_file)

        ps1 = PatchSet.from_filename(utf8_file, newline='\n')
        import io
        with io.open(utf8_file, 'r', newline='\n') as diff_file:
            ps2 = PatchSet(diff_file)

        self.assertEqual(ps1, ps2)

    def test_parse_content_with_control_characters(self):
        # regression test for issue #120: hunk content may contain arbitrary
        # control bytes (e.g. ESC, and lone CR) as in the reported vim diff.
        # A lone CR must not be treated as a line separator; reading the data
        # without universal-newline translation preserves and round-trips it.
        content = (
            '--- a/f\n'
            '+++ b/f\n'
            '@@ -1,1 +1,3 @@\n'
            ' context\n'
            '+sil! norm R\x1bdoo\x1bbdeu\x17\x18R\rcont\n'
            '+tail line\n'
        )

        # string input goes through StringIO, which only splits on \n
        res = PatchSet(content)
        self.assertEqual(res.added, 2)
        self.assertEqual(len(res[0][0]), 3)
        self.assertEqual(
            str(res[0][0][1]), '+sil! norm R\x1bdoo\x1bbdeu\x17\x18R\rcont\n')
        self.assertEqual(str(res), content)

        # reading from a file requires newline='\n' to avoid the lone CR being
        # interpreted as a line boundary (the from_filename default would raise)
        path = os.path.join(self.samples_dir, 'samples', '_control_chars.diff')
        try:
            with open(path, 'wb') as f:
                f.write(content.encode('utf-8'))
            self.assertRaises(UnidiffParseError, PatchSet.from_filename, path)
            res2 = PatchSet.from_filename(path, newline='\n')
            self.assertEqual(res, res2)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_parse_diff_with_new_and_modified_binary_files(self):
        """Parse git diff file with newly added and modified binaries files."""
        utf8_file = os.path.join(self.samples_dir, 'samples/sample8.diff')
        with open(utf8_file, 'r') as diff_file:
            res = PatchSet(diff_file)

        # three file in the patch
        self.assertEqual(len(res), 5)

        # first empty file is added
        self.assertFalse(res[0].is_modified_file)
        self.assertFalse(res[0].is_removed_file)
        self.assertTrue(res[0].is_added_file)
        self.assertFalse(res[0].is_binary_file)
        self.assertEqual(res[0].diff_line_no, 1)

        # second file is added
        self.assertFalse(res[1].is_modified_file)
        self.assertFalse(res[1].is_removed_file)
        self.assertTrue(res[1].is_added_file)
        self.assertTrue(res[1].is_binary_file)
        self.assertEqual(res[1].diff_line_no, 4)

        # third file is modified
        self.assertTrue(res[2].is_modified_file)
        self.assertFalse(res[2].is_removed_file)
        self.assertFalse(res[2].is_added_file)
        self.assertTrue(res[2].is_binary_file)
        self.assertEqual(res[2].diff_line_no, 8)

        # fourth file is removed
        self.assertFalse(res[3].is_modified_file)
        self.assertTrue(res[3].is_removed_file)
        self.assertFalse(res[3].is_added_file)
        self.assertTrue(res[3].is_binary_file)
        self.assertEqual(res[3].diff_line_no, 11)

        # fifth empty file is added
        self.assertFalse(res[4].is_modified_file)
        self.assertFalse(res[4].is_removed_file)
        self.assertTrue(res[4].is_added_file)
        self.assertFalse(res[4].is_binary_file)
        self.assertEqual(res[4].diff_line_no, 15)

    def test_parse_debdiff_binary_file_line_numbers(self):
        # issue #122 / PR #123: a binary change without hunks should still
        # expose the diff line number where its entry appears.
        utf8_file = os.path.join(self.samples_dir, 'samples/debdiff.diff')
        with open(utf8_file, 'r') as diff_file:
            res = PatchSet(diff_file)

        self.assertEqual(len(res), 3)

        # first file has a hunk; entry starts at the +++ line (3)
        self.assertEqual(res[0].path, 'new/added.txt')
        self.assertEqual(res[0].diff_line_no, 3)
        self.assertEqual(res[0][0][0].diff_line_no, 5)

        # the binary entries carry the line number of their "Binary files" line
        self.assertEqual(res[1].path, '/t/p2/a.png')
        self.assertTrue(res[1].is_binary_file)
        self.assertEqual(res[1].diff_line_no, 6)

        self.assertEqual(res[2].path, '/t/p2/b.png')
        self.assertTrue(res[2].is_binary_file)
        self.assertEqual(res[2].diff_line_no, 7)

    def test_parse_round_trip_with_binary_files_in_diff(self):
        """Parse git diff with binary files though round trip"""
        utf8_file = os.path.join(self.samples_dir, 'samples/sample8.diff')
        with open(utf8_file, 'r') as diff_file:
            res1 = PatchSet(diff_file)

        res2 = PatchSet(str(res1))
        self.assertEqual(res1, res2)

    def test_parse_diff_git_no_prefix(self):
        utf8_file = os.path.join(self.samples_dir, 'samples/git_no_prefix.diff')
        with open(utf8_file, 'r') as diff_file:
            res = PatchSet(diff_file)

        self.assertEqual(len(res), 3)

        self.assertEqual(res[0].source_file, 'file1')
        self.assertEqual(res[0].target_file, '/dev/null')
        self.assertTrue(res[0].is_removed_file)
        self.assertEqual(res[0].path, 'file1')

        self.assertEqual(res[1].source_file, 'file2')
        self.assertEqual(res[1].target_file, 'file2')
        self.assertTrue(res[1].is_modified_file)
        self.assertEqual(res[1].path, 'file2')

        self.assertEqual(res[2].source_file, '/dev/null')
        self.assertEqual(res[2].target_file, 'file3')
        self.assertTrue(res[2].is_added_file)
        self.assertEqual(res[2].path, 'file3')

    def test_parse_diff_git_mnemonic_prefix(self):
        # issue #81: git diff with diff.mnemonicPrefix set uses i/ w/ (etc.)
        # instead of a/ b/; path should still resolve to the plain filename.
        diff = (
            'diff --git i/foo/bar.py w/foo/bar.py\n'
            'index abc1234..def5678 100644\n'
            '--- i/foo/bar.py\n'
            '+++ w/foo/bar.py\n'
            '@@ -1,2 +1,2 @@\n'
            ' a\n'
            '-b\n'
            '+c\n'
        )
        res = PatchSet(diff)

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].source_file, 'i/foo/bar.py')
        self.assertEqual(res[0].target_file, 'w/foo/bar.py')
        self.assertEqual(res[0].path, 'foo/bar.py')
        self.assertFalse(res[0].is_rename)
        self.assertTrue(res[0].is_modified_file)
        self.assertEqual(str(res), diff)

    def test_parse_diff_with_empty_filenames(self):
        # regression test for issue #115: difflib.unified_diff() without
        # fromfile/tofile emits bare "--- " / "+++ " headers (empty
        # filenames), which should parse instead of raising.
        import difflib
        a = 'l1\nl2\nl3\nl4\nl5\nl6\nl7\n'.splitlines(keepends=True)
        b = 'l1\nl2x\nl3\nl4\nl5\nl6\nl7\n'.splitlines(keepends=True)
        diff = list(difflib.unified_diff(a, b))

        res = PatchSet(diff)

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].source_file, '')
        self.assertEqual(res[0].target_file, '')
        self.assertEqual(res[0].path, '')
        self.assertTrue(res[0].is_modified_file)
        self.assertFalse(res[0].is_rename)
        self.assertEqual(res.added, 1)
        self.assertEqual(res.removed, 1)
        # the parsed patch should round-trip back to the original input
        self.assertEqual(str(res), ''.join(diff))

    def test_parse_filename_with_spaces(self):
        filename = os.path.join(self.samples_dir, 'samples/git_filenames_with_spaces.diff')
        with open(filename) as f:
            res = PatchSet(f)

        self.assertEqual(len(res), 1)

        self.assertEqual(res[0].source_file, '/dev/null')
        self.assertEqual(res[0].target_file, 'b/has spaces/t.sql')
        self.assertTrue(res[0].is_added_file)
        self.assertEqual(res[0].path, 'has spaces/t.sql')

    def test_parse_filename_prefix_with_spaces(self):
        filename = os.path.join(self.samples_dir, 'samples/git_filenames_with_spaces_prefix.diff')
        with open(filename) as f:
            res = PatchSet(f)

        self.assertEqual(len(res), 1)

        self.assertEqual(res[0].source_file, '/dev/null')
        self.assertEqual(res[0].target_file, 'dst://foo bar/baz')
        self.assertTrue(res[0].is_added_file)
        self.assertEqual(res[0].path, 'dst://foo bar/baz')

    def test_parse_quoted_filename(self):
        filename = os.path.join(self.samples_dir, 'samples/git_quoted_filename.diff')
        with open(filename) as f:
            res = PatchSet(f)

        self.assertEqual(len(res), 1)

        self.assertEqual(res[0].source_file, '/dev/null')
        self.assertEqual(res[0].target_file, '"b/A \\303\\242 B.py"')
        self.assertTrue(res[0].is_added_file)
        self.assertEqual(res[0].path, '"A \\303\\242 B.py"')

    def test_parse_quoted_filename_with_spaces(self):
        # regression test for issue #119: a quoted filename containing
        # spaces must not be mis-split into wrong source/target and must
        # not be detected as a rename when source and target match.
        filename = os.path.join(
            self.samples_dir, 'samples/git_quoted_filename_with_spaces.diff')
        with open(filename) as f:
            res = PatchSet(f)

        self.assertEqual(len(res), 1)
        self.assertEqual(
            res[0].source_file, '"a/docs/develop/Bug \\346\\216\\222\\346\\237\\245.md"')
        self.assertEqual(
            res[0].target_file, '"b/docs/develop/Bug \\346\\216\\222\\346\\237\\245.md"')
        self.assertFalse(res[0].is_rename)
        self.assertTrue(res[0].is_modified_file)
        self.assertEqual(
            res[0].path, '"docs/develop/Bug \\346\\216\\222\\346\\237\\245.md"')

    def test_line_numbers_with_section_header(self):
        # regression test for issue / PR #118: a hunk carrying a non-empty
        # section header must not throw off source/target line numbering.
        diff = (
            '--- a/f.py\n'
            '+++ b/f.py\n'
            '@@ -10,7 +10,7 @@ def my_function(arg):\n'
            ' ctx1\n'
            ' ctx2\n'
            ' ctx3\n'
            '-old line\n'
            '+new line\n'
            ' ctx4\n'
            ' ctx5\n'
            ' ctx6\n'
        )
        res = PatchSet(diff)
        hunk = res[0][0]

        self.assertEqual(hunk.section_header, 'def my_function(arg):')
        self.assertTrue(hunk.is_valid())
        self.assertEqual(hunk.added, 1)
        self.assertEqual(hunk.removed, 1)
        # the removed line is source line 13; the added line is target line 13
        removed = [l for l in hunk if l.is_removed][0]
        added = [l for l in hunk if l.is_added][0]
        self.assertEqual(removed.source_line_no, 13)
        self.assertEqual(added.target_line_no, 13)
        # trailing context keeps counting correctly
        self.assertEqual(hunk[-1].source_line_no, 16)
        self.assertEqual(hunk[-1].target_line_no, 16)


    def test_deleted_file(self):
        filename = os.path.join(self.samples_dir, 'samples/git_delete.diff')
        with open(filename) as f:
            res = PatchSet(f)

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].source_file, 'a/somefile.c')
        self.assertEqual(res[0].target_file, '/dev/null')
        self.assertTrue(res[0].is_removed_file)

    def test_added_symlink_file_mode(self):
        # issue #125: expose the file mode; a new symlink has mode 120000
        filename = os.path.join(self.samples_dir, 'samples/git_symlink.diff')
        with open(filename) as f:
            res = PatchSet(f)

        self.assertEqual(len(res), 1)
        self.assertTrue(res[0].is_added_file)
        self.assertIsNone(res[0].source_mode)
        self.assertEqual(res[0].target_mode, '120000')
        self.assertTrue(res[0].is_symlink)

    def test_new_file_mode(self):
        # issue #125: a regular new file carries `new file mode 100644`
        filename = os.path.join(self.samples_dir, 'samples/git_quoted_filename.diff')
        with open(filename) as f:
            res = PatchSet(f)

        self.assertEqual(res[0].target_mode, '100644')
        self.assertFalse(res[0].is_symlink)

    def test_mode_change_file(self):
        # issue #125: `old mode` / `new mode` expose a chmod
        diff = (
            'diff --git a/server.py b/bin/server.py\n'
            'old mode 100644\n'
            'new mode 100755\n'
            'similarity index 100%\n'
            'rename from server.py\n'
            'rename to bin/server.py\n'
        )
        res = PatchSet(diff)

        self.assertEqual(res[0].source_mode, '100644')
        self.assertEqual(res[0].target_mode, '100755')
        self.assertFalse(res[0].is_symlink)
        self.assertTrue(res[0].is_rename)

    def test_index_line_mode(self):
        # issue #125: an unchanged mode on the index line applies to both sides
        diff = (
            'diff --git a/info.sh b/info.sh\n'
            'index ddbe53c40..6c84b8acf 100755\n'
            '--- a/info.sh\n'
            '+++ b/info.sh\n'
            '@@ -1,2 +1,2 @@\n'
            ' a\n'
            '-b\n'
            '+c\n'
        )
        res = PatchSet(diff)

        self.assertEqual(res[0].source_mode, '100755')
        self.assertEqual(res[0].target_mode, '100755')
        self.assertFalse(res[0].is_symlink)
        # the index line is preserved so the diff still round-trips
        self.assertEqual(str(res), diff)

    def test_parse_format_patch_hunkless_rename(self):
        # regression test for issues #73 / #74: git format-patch output where a
        # hunkless file (a pure rename) is followed by the "-- " email
        # signature and a trailing blank line must not raise.
        lines = [
            'From 82dd164 Mon Sep 17 00:00:00 2001\n',
            'From: Someone <someone@example.com>\n',
            'Subject: [PATCH] Rename JSONHelper to JSONHelper.java\n',
            '\n',
            '---\n',
            ' JSONHelper => JSONHelper.java | 0\n',
            ' 1 file changed, 0 insertions(+), 0 deletions(-)\n',
            ' rename JSONHelper => JSONHelper.java (100%)\n',
            '\n',
            'diff --git a/JSONHelper b/JSONHelper.java\n',
            'similarity index 100%\n',
            'rename from JSONHelper\n',
            'rename to JSONHelper.java\n',
            '-- \n',
            '2.17.1\n',
            '\n',
        ]

        res = PatchSet(lines)

        self.assertEqual(len(res), 1)
        self.assertTrue(res[0].is_rename)
        self.assertEqual(res[0].path, 'JSONHelper.java')
        self.assertEqual(len(res[0]), 0)

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

    def test_diff_hunk_positions(self):
        with open(self.sample_file, 'rb') as diff_file:
            res = PatchSet(diff_file, encoding='utf-8')
        self.do_test_diff_hunk_positions(res)

    def test_diff_metadata_only(self):
        with open(self.sample_file, 'rb') as diff_file:
            res = PatchSet(diff_file, encoding='utf-8', metadata_only=True)
        self.do_test_diff_hunk_positions(res)

    def do_test_diff_hunk_positions(self, res):
        hunk_positions = []
        for diff_file in res:
            for hunk in diff_file:
                hunk_positions.append((hunk.source_start, hunk.target_start,
                                       hunk.source_length, hunk.target_length))

        expected_hunk_positions = [
            # File: 1, Hunk: 1
            (1, 1, 3, 9),
            # File: 1, Hunk: 2
            (5, 11, 16, 10),
            # File: 1, Hunk: 3
            (22, 22, 3, 7),
            # File: 2, Hunk: 1
            (0, 1, 0, 9),
            # File: 3, Hunk: 1
            (1, 0, 9, 0)
        ]

        self.assertEqual(hunk_positions, expected_hunk_positions)

    def test_binary_patch(self):
        utf8_file = os.path.join(self.samples_dir, 'samples/binary.diff')
        with open(utf8_file, 'r') as diff_file:
            res = PatchSet(diff_file)
            self.assertEqual(len(res), 1)
            patch = res[0]
            self.assertEqual(patch.source_file, '/dev/null')
            self.assertEqual(patch.target_file, 'b/1x1.png')
            self.assertTrue(patch.is_binary_file)
            self.assertTrue(patch.is_added_file)

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

    def test_git_renaming(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(tests_dir, 'samples/git_rename.diff')
        with codecs.open(file_path, 'r', encoding='utf-8') as diff_file:
            res = PatchSet(diff_file)

        self.assertEqual(len(res), 3)
        self.assertEqual(len(res.modified_files), 3)
        self.assertEqual(len(res.added_files), 0)
        self.assertEqual(len(res.removed_files), 0)

        # renamed and modified files
        for patch in res[:2]:
            self.assertTrue(patch.is_rename)
            self.assertEqual(patch.added, 1)
            self.assertEqual(patch.removed, 1)
        # renamed file under sub-path
        patch = res[2]
        self.assertTrue(patch.is_rename)
        self.assertEqual(patch.added, 0)
        self.assertEqual(patch.removed, 0)
        # confirm the full path is in source/target filenames
        self.assertEqual(patch.source_file, 'a/sub/onefile')
        self.assertEqual(patch.target_file, 'b/sub/otherfile')
        # check path is the target path
        self.assertEqual(patch.path, 'sub/otherfile')

        # check that original diffs and those produced
        # by unidiff are the same
        with codecs.open(file_path, 'r', encoding='utf-8') as diff_file:
            self.assertEqual(diff_file.read(), str(res))
