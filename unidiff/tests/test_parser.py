# -*- coding: utf-8 -*-
# Author: Matías Bordese


"""Tests for the unified diff parser process."""

import os.path
import unittest2

from nlg4patch.unidiff import parser


class TestUnidiffParser(unittest2.TestCase):
    """Tests for Unified Diff Parser."""

    def setUp(self):
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

        # Hunk 1: five additions, no deletions, no modifications
        self.assertEqual(res[0][0].added, 6)
        self.assertEqual(res[0][0].modified, 0)
        self.assertEqual(res[0][0].deleted, 0)

        # Hunk 2: no additions, 6 deletions, 2 modifications
        self.assertEqual(res[0][1].added, 0)
        self.assertEqual(res[0][1].modified, 2)
        self.assertEqual(res[0][1].deleted, 6)

        # Hunk 3: four additions, no deletions, no modifications
        self.assertEqual(res[0][2].added, 4)
        self.assertEqual(res[0][2].modified, 0)
        self.assertEqual(res[0][2].deleted, 0)

        # Check file totals
        self.assertEqual(res[0].added, 10)
        self.assertEqual(res[0].modified, 2)
        self.assertEqual(res[0].deleted, 6)

    def test_parse_malformed_diff(self):
        """Parse malformed file."""
        with open(self.sample_bad_file) as diff_file:
            self.assertRaises(parser.UnidiffParseException,
                              parser.parse_unidiff, diff_file)

