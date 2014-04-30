# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2012 Matias Bordese
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.


"""Tests for Hunk."""

import unittest

from unidiff.patch import Hunk, LINE_TYPE_ADD, LINE_TYPE_DELETE, LINE_TYPE_CONTEXT


class TestHunk(unittest.TestCase):
    """Tests for Hunk."""

    def setUp(self):
        super(TestHunk, self).setUp()
        self.sample_line = 'Sample line'

    def test_missing_length(self):
        hunk = Hunk(src_len=None, tgt_len=None)
        hunk.append_context_line(self.sample_line)
        self.assertTrue(hunk.is_valid())
    
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
        self.assertEqual(len(hunk.source_types), 1)
        self.assertEqual(hunk.target_types, hunk.source_types)
        self.assertEqual(hunk.source_types[0], LINE_TYPE_CONTEXT)
        self.assertEqual(hunk.target_types[0], LINE_TYPE_CONTEXT)

    def test_append_added_line(self):
        hunk = Hunk(src_len=0, tgt_len=1)
        hunk.append_added_line(self.sample_line)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(len(hunk.target_lines), 1)
        self.assertEqual(hunk.source_lines, [])
        self.assertIn(self.sample_line, hunk.target_lines)
        self.assertEqual(hunk.source_types, [])
        self.assertEqual(len(hunk.target_types), 1)
        self.assertEqual(hunk.target_types[0], LINE_TYPE_ADD)

    def test_append_deleted_line(self):
        hunk = Hunk(src_len=1, tgt_len=0)
        hunk.append_deleted_line(self.sample_line)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(len(hunk.source_lines), 1)
        self.assertEqual(hunk.target_lines, [])
        self.assertIn(self.sample_line, hunk.source_lines)
        self.assertEqual(hunk.target_types, [])
        self.assertEqual(len(hunk.source_types), 1)
        self.assertEqual(hunk.source_types[0], LINE_TYPE_DELETE)

    def test_modified_counter(self):
        hunk = Hunk(src_len=1, tgt_len=1)
        hunk.append_deleted_line(self.sample_line)
        hunk.append_added_line(self.sample_line)
        hunk.add_to_modified_counter(1)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(hunk.modified, 1)
        self.assertEqual(hunk.added, 0)
        self.assertEqual(hunk.deleted, 0)

