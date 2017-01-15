# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2017 Matias Bordese
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


"""Tests for Line."""

from __future__ import unicode_literals

import unittest

from unidiff.patch import (
    LINE_TYPE_ADDED,
    LINE_TYPE_CONTEXT,
    LINE_TYPE_REMOVED,
    Line,
)


class TestLine(unittest.TestCase):
    """Tests for Line."""

    def setUp(self):
        super(TestLine, self).setUp()
        self.context_line = Line('Sample line', line_type=LINE_TYPE_CONTEXT)
        self.added_line = Line('Sample line', line_type=LINE_TYPE_ADDED)
        self.removed_line = Line('Sample line', line_type=LINE_TYPE_REMOVED)

    def test_str(self):
        self.assertEqual(str(self.added_line), '+Sample line')

    def test_repr(self):
        self.assertEqual(repr(self.added_line), '<Line: +Sample line>')

    def test_equal(self):
        other = Line('Sample line', line_type=LINE_TYPE_ADDED)
        self.assertEqual(self.added_line, other)

    def test_not_equal(self):
        self.assertNotEqual(self.added_line, self.removed_line)

    def test_is_added(self):
        self.assertTrue(self.added_line.is_added)
        self.assertFalse(self.context_line.is_added)
        self.assertFalse(self.removed_line.is_added)

    def test_is_removed(self):
        self.assertTrue(self.removed_line.is_removed)
        self.assertFalse(self.added_line.is_removed)
        self.assertFalse(self.context_line.is_removed)

    def test_is_context(self):
        self.assertTrue(self.context_line.is_context)
        self.assertFalse(self.added_line.is_context)
        self.assertFalse(self.removed_line.is_context)
