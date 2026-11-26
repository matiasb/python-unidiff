"""Round trips for Git binary patch data."""

from pathlib import Path
import unittest

from unidiff import PatchSet
from unidiff.errors import UnidiffParseError


class TestGitBinaryPatch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        samples = Path(__file__).parent / 'samples'
        cls.email = (samples / 'binary.diff').read_text(encoding='utf-8')
        # Use the existing Git patch without its mail preamble and signature.
        cls.literal = cls.email[cls.email.index('diff --git '):]
        cls.literal = cls.literal.split('\n--\n', 1)[0] + '\n'
        cls.delta = (samples / 'binary_delta.diff').read_text(encoding='utf-8')
        cls.plain_text = (
            '--- a/story.txt\n'
            '+++ b/story.txt\n'
            '@@ -1,2 +1,2 @@\n'
            ' unchanged\n'
            '-before\n'
            '+after\n'
        )
        cls.git_text = 'diff --git a/story.txt b/story.txt\n' + cls.plain_text

    def test_literal_round_trip(self):
        patch = PatchSet(self.literal)

        self.assertEqual(len(patch), 1)
        self.assertEqual(str(patch[0]), self.literal)
        self.assertEqual(str(patch), self.literal)
        self.assertTrue(patch[0].is_binary_file)
        self.assertTrue(patch[0].is_added_file)
        self.assertEqual(patch[0].target_mode, '100644')
        self.assertEqual(len(patch[0]), 0)
        self.assertEqual((patch.added, patch.removed), (0, 0))

    def test_delta_round_trip(self):
        patch = PatchSet(self.delta)

        self.assertEqual(len(patch), 1)
        self.assertEqual(str(patch[0]), self.delta)
        self.assertEqual(str(patch), self.delta)
        self.assertTrue(patch[0].is_binary_file)
        self.assertTrue(patch[0].is_modified_file)
        self.assertEqual(patch[0].source_mode, '100644')
        self.assertEqual(patch[0].target_mode, '100644')
        self.assertEqual(len(patch[0]), 0)
        self.assertEqual((patch.added, patch.removed), (0, 0))

    def test_consecutive_binary_files(self):
        patch = PatchSet(self.literal + self.delta)

        self.assertEqual([file.path for file in patch], ['1x1.png', 'data.bin'])
        self.assertEqual([str(file) for file in patch],
                         [self.literal, self.delta])
        self.assertEqual(str(patch), self.literal + self.delta)
        self.assertEqual(patch[1].diff_line_no, self.literal.count('\n') + 1)
        self.assertEqual((patch.added, patch.removed), (0, 0))

    def test_binary_and_text_round_trip(self):
        for text in (self.git_text, self.plain_text):
            for parts in ((self.literal, text), (text, self.delta)):
                with self.subTest(parts=parts):
                    patch = PatchSet(''.join(parts))

                    self.assertEqual([str(file) for file in patch], list(parts))
                    self.assertEqual(str(patch), ''.join(parts))
                    self.assertEqual((patch.added, patch.removed), (1, 1))
                    second_start = 2 if parts[1] == self.plain_text else 1
                    self.assertEqual(patch[1].diff_line_no,
                                     parts[0].count('\n') + second_start)

    def test_format_patch_signature_is_not_binary_data(self):
        patch = PatchSet(self.email)

        self.assertEqual(str(patch[0]), self.literal)
        self.assertEqual(str(patch), self.literal)

    def test_metadata_only(self):
        for parts in ((self.literal, self.delta, self.git_text),
                      (self.literal, self.plain_text),
                      (self.delta, self.plain_text)):
            with self.subTest(parts=parts):
                diff = ''.join(parts)
                full = PatchSet(diff)
                metadata = PatchSet(diff, metadata_only=True)

                self.assertEqual(len(metadata), len(parts))
                self.assertEqual((metadata.added, metadata.removed), (1, 1))
                for file, original, part in zip(metadata, full, parts):
                    for attr in ('source_file', 'target_file', 'source_mode',
                                 'target_mode', 'diff_line_no', 'is_binary_file',
                                 'is_added_file', 'is_modified_file',
                                 'is_removed_file', 'added', 'removed'):
                        self.assertEqual(getattr(file, attr),
                                         getattr(original, attr))
                    if file.is_binary_file:
                        self.assertEqual(str(file),
                                         part.split('GIT binary patch\n')[0])
                        self.assertEqual(len(file), 0)
                    else:
                        self.assertEqual(len(file), 1)
                        self.assertEqual(len(file[0]), 0)
                        if part == self.plain_text:
                            self.assertIsNone(file.patch_info)

    def test_binary_notice_round_trip(self):
        diff = ('diff --git a/image.png b/image.png\n'
                'Binary files a/image.png and b/image.png differ\n')
        for metadata_only in (False, True):
            with self.subTest(metadata_only=metadata_only):
                patch = PatchSet(diff, metadata_only=metadata_only)
                self.assertEqual(str(patch[0]), diff)
                self.assertEqual(str(patch), diff)
                self.assertTrue(patch[0].is_binary_file)

    def test_binary_marker_without_git_header(self):
        with self.assertRaisesRegex(UnidiffParseError,
                                    'Unexpected binary patch marker'):
            PatchSet('GIT binary patch\nliteral 0\nHcmV?d00001\n\n')
