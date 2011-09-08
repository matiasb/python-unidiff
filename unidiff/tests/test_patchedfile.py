# -*- coding: utf-8 -*-
# Author: Matías Bordese

"""Tests for PatchedFile."""

import os.path
import unittest2

from nlg4patch.unidiff.patch import PatchedFile, Hunk


class TestPatchedFile(unittest2.TestCase):
    """Tests for PatchedFile."""

    def setUp(self):
        self.patched_file = PatchedFile()

    def test_is_added_file(self):
        hunk = Hunk(src_start=0, src_len=0, tgt_start=1, tgt_len=10)
        self.patched_file.append(hunk)
        self.assertTrue(self.patched_file.is_added_file)

    def test_is_deleted_file(self):
        hunk = Hunk(src_start=1, src_len=10, tgt_start=0, tgt_len=0)
        self.patched_file.append(hunk)
        self.assertTrue(self.patched_file.is_deleted_file)

    def test_is_modified_file(self):
        hunk = Hunk(src_start=1, src_len=10, tgt_start=1, tgt_len=8)
        self.patched_file.append(hunk)
        self.assertTrue(self.patched_file.is_modified_file)

