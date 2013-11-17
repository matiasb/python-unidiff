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


"""Tests for the unified diff parser process."""

import os.path
import unittest

from unidiff import parser


class TestUnidiffParser(unittest.TestCase):
    """Tests for Unified Diff Parser."""

    def setUp(self):
        super(TestUnidiffParser, self).setUp()
        samples_dir = os.path.dirname(os.path.realpath(__file__))
        self.sample_file = os.path.join(samples_dir, 'sample.diff')
        self.sample_bad_file = os.path.join(samples_dir, 'sample_bad.diff')

    def test_parse_sample(self):
        """Parse sample file."""
        with open(self.sample_file) as diff_file:
            res = parser.parse_unidiff(diff_file)

        # one file in the patch
        self.assertEqual(len(res), 1)
        # three hunks
        self.assertEqual(len(res[0]), 3)

        # Hunk 1: five additions, no deletions, no modifications, a section
        # header
        self.assertEqual(res[0][0].added, 6)
        self.assertEqual(res[0][0].modified, 0)
        self.assertEqual(res[0][0].deleted, 0)
        self.assertEqual(res[0][0].section_header, 'Section Header')

        # Hunk 2: no additions, 6 deletions, 2 modifications, no section header
        self.assertEqual(res[0][1].added, 0)
        self.assertEqual(res[0][1].modified, 2)
        self.assertEqual(res[0][1].deleted, 6)
        self.assertEqual(res[0][1].section_header, '')

        # Hunk 3: four additions, no deletions, no modifications, no section
        # header
        self.assertEqual(res[0][2].added, 4)
        self.assertEqual(res[0][2].modified, 0)
        self.assertEqual(res[0][2].deleted, 0)
        self.assertEqual(res[0][2].section_header, '')

        # Check file totals
        self.assertEqual(res[0].added, 10)
        self.assertEqual(res[0].modified, 2)
        self.assertEqual(res[0].deleted, 6)

    def test_parse_malformed_diff(self):
        """Parse malformed file."""
        with open(self.sample_bad_file) as diff_file:
            self.assertRaises(parser.UnidiffParseException,
                              parser.parse_unidiff, diff_file)

