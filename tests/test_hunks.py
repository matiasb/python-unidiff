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


"""Tests for Hunk."""

from __future__ import unicode_literals

import unittest

from unidiff.patch import (
    LINE_TYPE_ADDED,
    LINE_TYPE_CONTEXT,
    LINE_TYPE_REMOVED,
    Hunk,
    Line,
)


class TestHunk(unittest.TestCase):
    """Tests for Hunk."""

    def setUp(self):
        super(TestHunk, self).setUp()
        self.context_line = Line('Sample line', line_type=LINE_TYPE_CONTEXT)
        self.added_line = Line('Sample line', line_type=LINE_TYPE_ADDED)
        self.removed_line = Line('Sample line', line_type=LINE_TYPE_REMOVED)

    def test_missing_length(self):
        hunk = Hunk(src_len=None, tgt_len=None)
        hunk.append(self.context_line)
        self.assertTrue(hunk.is_valid())

    def test_default_is_valid(self):
        hunk = Hunk()
        self.assertTrue(hunk.is_valid())

    def test_missing_data_is_not_valid(self):
        hunk = Hunk(src_len=1, tgt_len=1)
        self.assertFalse(hunk.is_valid())

    def test_append_context(self):
        hunk = Hunk(src_len=1, tgt_len=1)
        hunk.append(self.context_line)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(len(hunk.source), 1)
        self.assertEqual(hunk.target, hunk.source)
        self.assertIn(str(self.context_line), hunk.source)
        source_lines = list(hunk.source_lines())
        target_lines = list(hunk.target_lines())
        self.assertEqual(target_lines, source_lines)
        self.assertEqual(target_lines, [self.context_line])

    def test_append_added_line(self):
        hunk = Hunk(src_len=0, tgt_len=1)
        hunk.append(self.added_line)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(len(hunk.target), 1)
        self.assertEqual(hunk.source, [])
        self.assertIn(str(self.added_line), hunk.target)
        target_lines = list(hunk.target_lines())
        self.assertEqual(target_lines, [self.added_line])

    def test_append_deleted_line(self):
        hunk = Hunk(src_len=1, tgt_len=0)
        hunk.append(self.removed_line)
        self.assertTrue(hunk.is_valid())
        self.assertEqual(len(hunk.source), 1)
        self.assertEqual(hunk.target, [])
        self.assertIn(str(self.removed_line), hunk.source)
        source_lines = list(hunk.source_lines())
        self.assertEqual(source_lines, [self.removed_line])
