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


"""Tests for PatchedFile."""

import unittest

from unidiff.patch import PatchedFile, Hunk


class TestPatchedFile(unittest.TestCase):
    """Tests for PatchedFile."""

    def setUp(self):
        super(TestPatchedFile, self).setUp()
        self.patched_file = PatchedFile()

    def test_is_added_file(self):
        hunk = Hunk(src_start=0, src_len=0, tgt_start=1, tgt_len=10)
        self.patched_file.append(hunk)
        self.assertTrue(self.patched_file.is_added_file)

    def test_is_removed_file(self):
        hunk = Hunk(src_start=1, src_len=10, tgt_start=0, tgt_len=0)
        self.patched_file.append(hunk)
        self.assertTrue(self.patched_file.is_removed_file)

    def test_is_modified_file(self):
        hunk = Hunk(src_start=1, src_len=10, tgt_start=1, tgt_len=8)
        self.patched_file.append(hunk)
        self.assertTrue(self.patched_file.is_modified_file)

    def test_default_file_prefix(self):
        patched_file = PatchedFile(source="a/foo/bar", target="b/foo/bar")
        self.assertEqual(patched_file.path, "foo/bar")

    def test_git_mnemonic_file_prefix(self):
        # mnemonic prefixes used when diff.mnemonicPrefix is set (c/ i/ o/ w/)
        # and the 1/ 2/ pair used by `git diff --no-index`
        for prefix in ('c', 'i', 'o', 'w', '1', '2'):
            patched_file = PatchedFile(source="%s/foo/bar" % prefix,
                                       target="%s/foo/bar" % prefix)
            self.assertEqual(patched_file.path, "foo/bar")

    def test_no_file_prefix(self):
        # a leading slash is not a prefix and must be preserved
        patched_file = PatchedFile(source="/foo/bar", target="/foo/bar")
        self.assertEqual(patched_file.path, "/foo/bar")
