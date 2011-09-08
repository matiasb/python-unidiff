# -*- coding: utf-8 -*-
# Author: Matías Bordese


"""Tests for Hunk."""

import os.path
import unittest2

from nlg4patch.unidiff.patch import Hunk


class TestHunk(unittest2.TestCase):
    """Tests for Hunk."""
    
    def setUp(self):
        self.sample_line = 'Sample line'

    def test_default_is_valid(self):
        hunk = Hunk()
        self.assertTrue(hunk.is_valid())

    def test_missing_data_is_not_valid(self):
        hunk = Hunk(src_len=1, tgt_len=1)
        self.assertFalse(hunk.is_valid())

    def test_append_context(self):
        hunk = Hunk(src_len=1, tgt_len=1)
        hunk.append_context_line(self.sample_line)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(len(hunk.source_lines), 1)
        self.assertEqual(hunk.target_lines, hunk.source_lines)
        self.assertIn(self.sample_line, hunk.source_lines)

    def test_append_added_line(self):
        hunk = Hunk(src_len=0, tgt_len=1)
        hunk.append_added_line(self.sample_line)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(len(hunk.target_lines), 1)
        self.assertEqual(hunk.source_lines, [])
        self.assertIn(self.sample_line, hunk.target_lines)

    def test_append_deleted_line(self):
        hunk = Hunk(src_len=1, tgt_len=0)
        hunk.append_deleted_line(self.sample_line)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(len(hunk.source_lines), 1)
        self.assertEqual(hunk.target_lines, [])
        self.assertIn(self.sample_line, hunk.source_lines)

    def test_modified_counter(self):
        hunk = Hunk(src_len=1, tgt_len=1)
        hunk.append_deleted_line(self.sample_line)
        hunk.append_added_line(self.sample_line)
        hunk.add_to_modified_counter(1)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(hunk.modified, 1)
        self.assertEqual(hunk.added, 0)
        self.assertEqual(hunk.deleted, 0)

