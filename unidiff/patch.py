
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


"""Classes used by the unified diff parser to keep the diff data."""

from __future__ import annotations

import pathlib
from collections.abc import Iterable, Iterator
from io import StringIO

from unidiff.constants import (
    DEFAULT_ENCODING,
    DEV_NULL,
    LINE_TYPE_ADDED,
    LINE_TYPE_CONTEXT,
    LINE_TYPE_EMPTY,
    LINE_TYPE_NO_NEWLINE,
    LINE_TYPE_REMOVED,
    LINE_VALUE_NO_NEWLINE,
    RE_BINARY_DIFF,
    RE_DIFF_GIT_DELETED_FILE,
    RE_DIFF_GIT_HEADER,
    RE_DIFF_GIT_HEADER_NO_PREFIX,
    RE_DIFF_GIT_HEADER_URI_LIKE,
    RE_DIFF_GIT_INDEX,
    RE_DIFF_GIT_NEW_FILE,
    RE_DIFF_GIT_NEW_MODE,
    RE_DIFF_GIT_OLD_MODE,
    RE_HUNK_BODY_LINE,
    RE_HUNK_EMPTY_BODY_LINE,
    RE_HUNK_HEADER,
    RE_NO_NEWLINE_MARKER,
    RE_PATCH_FILE_PREFIX,
    RE_SOURCE_FILENAME,
    RE_TARGET_FILENAME,
    SYMLINK_FILE_MODE,
)
from unidiff.errors import UnidiffParseError


class Line:
    """A diff line."""

    def __init__(self, value: str, line_type: str,
                 source_line_no: int | None = None,
                 target_line_no: int | None = None,
                 diff_line_no: int | None = None) -> None:
        super().__init__()
        self.source_line_no = source_line_no
        self.target_line_no = target_line_no
        self.diff_line_no = diff_line_no
        self.line_type = line_type
        self.value = value

    def __repr__(self) -> str:
        return f"<Line: {self.line_type}{self.value}>"

    def __str__(self) -> str:
        return f"{self.line_type}{self.value}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Line):
            return NotImplemented
        return (self.source_line_no == other.source_line_no and
                self.target_line_no == other.target_line_no and
                self.diff_line_no == other.diff_line_no and
                self.line_type == other.line_type and
                self.value == other.value)

    @property
    def is_added(self) -> bool:
        return self.line_type == LINE_TYPE_ADDED

    @property
    def is_removed(self) -> bool:
        return self.line_type == LINE_TYPE_REMOVED

    @property
    def is_context(self) -> bool:
        return self.line_type == LINE_TYPE_CONTEXT


class PatchInfo(list[str]):
    """Lines with extended patch info.

    Format of this info is not documented and it very much depends on
    patch producer.

    """

    def __repr__(self) -> str:
        return f"<PatchInfo: {self[0].strip()}>"

    def __str__(self) -> str:
        return ''.join(str(line) for line in self)


class Hunk(list[Line]):
    """Each of the modified blocks of a file."""

    def __init__(self, src_start: str | int = 0,
                 src_len: str | int | None = 0,
                 tgt_start: str | int = 0,
                 tgt_len: str | int | None = 0,
                 section_header: str = '') -> None:
        super().__init__()
        if src_len is None:
            src_len = 1
        if tgt_len is None:
            tgt_len = 1
        self.source_start = int(src_start)
        self.source_length = int(src_len)
        self.target_start = int(tgt_start)
        self.target_length = int(tgt_len)
        self.section_header = section_header
        self._added: int | None = None
        self._removed: int | None = None

    def __repr__(self) -> str:
        return (
            f"<Hunk: @@ {self.source_start},{self.source_length} "
            f"{self.target_start},{self.target_length} @@ {self.section_header}>"
        )

    def __str__(self) -> str:
        # section header is optional and thus we output it only if it's present
        section = f' {self.section_header}' if self.section_header else ''
        head = (
            f"@@ -{self.source_start},{self.source_length} "
            f"+{self.target_start},{self.target_length} @@{section}\n"
        )
        content = ''.join(str(line) for line in self)
        return head + content

    def append(self, line: Line) -> None:
        """Append the line to hunk, and keep track of source/target lines."""
        # Make sure the line is encoded correctly. This is a no-op except for
        # potentially raising a UnicodeDecodeError.
        str(line)
        super().append(line)

    @property
    def added(self) -> int:
        if self._added is not None:
            return self._added
        # re-calculate each time to allow for hunk modifications
        # (which should mean metadata_only switch wasn't used)
        return sum(1 for line in self if line.is_added)

    @property
    def removed(self) -> int:
        if self._removed is not None:
            return self._removed
        # re-calculate each time to allow for hunk modifications
        # (which should mean metadata_only switch wasn't used)
        return sum(1 for line in self if line.is_removed)

    def is_valid(self) -> bool:
        """Check hunk header data matches entered lines info."""
        return (len(self.source) == self.source_length and
                len(self.target) == self.target_length)

    def source_lines(self) -> Iterator[Line]:
        """Hunk lines from source file (generator)."""
        return (line for line in self if line.is_context or line.is_removed)

    @property
    def source(self) -> list[str]:
        return [str(line) for line in self.source_lines()]

    def target_lines(self) -> Iterator[Line]:
        """Hunk lines from target file (generator)."""
        return (line for line in self if line.is_context or line.is_added)

    @property
    def target(self) -> list[str]:
        return [str(line) for line in self.target_lines()]


class PatchedFile(list[Hunk]):
    """Patch updated file, it is a list of Hunks."""

    def __init__(self, patch_info: PatchInfo | None = None,
                 source: str = '', target: str = '',
                 source_timestamp: str | None = None,
                 target_timestamp: str | None = None,
                 is_binary_file: bool = False,
                 source_mode: str | None = None,
                 target_mode: str | None = None,
                 diff_line_no: int | None = None) -> None:
        super().__init__()
        self.patch_info = patch_info
        self.source_file = source
        self.source_timestamp = source_timestamp
        self.target_file = target
        self.target_timestamp = target_timestamp
        self.is_binary_file = is_binary_file
        # git file modes (e.g. '100644', '100755', '120000'); None if unknown
        self.source_mode = source_mode
        self.target_mode = target_mode
        # 1-based line number in the diff where this file entry starts; useful
        # to locate files that have no hunks (e.g. binary changes)
        self.diff_line_no = diff_line_no

    def __repr__(self) -> str:
        return f"<PatchedFile: {self.path}>"

    def __str__(self) -> str:
        source = ''
        target = ''
        # patch info is optional
        info = '' if self.patch_info is None else str(self.patch_info)
        if not self.is_binary_file and self:
            source_ts = f'\t{self.source_timestamp}' if self.source_timestamp else ''
            target_ts = f'\t{self.target_timestamp}' if self.target_timestamp else ''
            source = f"--- {self.source_file}{source_ts}\n"
            target = f"+++ {self.target_file}{target_ts}\n"
        hunks = ''.join(str(hunk) for hunk in self)
        return info + source + target + hunks

    def _parse_hunk(self, header: str, diff: Iterator, encoding: str | None,
                    metadata_only: bool) -> None:
        """Parse hunk details."""
        header_info = RE_HUNK_HEADER.match(header)
        assert header_info is not None  # caller guarantees a hunk header
        hunk_info = header_info.groups()
        hunk = Hunk(*hunk_info)

        source_line_no = hunk.source_start
        target_line_no = hunk.target_start
        expected_source_end = source_line_no + hunk.source_length
        expected_target_end = target_line_no + hunk.target_length
        added = 0
        removed = 0

        for diff_line_no, line in diff:
            if encoding is not None:
                line = line.decode(encoding)

            if metadata_only:
                # quick line type detection, no regex required
                line_type = line[0] if line else LINE_TYPE_CONTEXT
                if line_type not in (LINE_TYPE_ADDED,
                                     LINE_TYPE_REMOVED,
                                     LINE_TYPE_CONTEXT,
                                     LINE_TYPE_NO_NEWLINE):
                    raise UnidiffParseError(
                        f'Hunk diff line expected: {line}')

                if line_type == LINE_TYPE_ADDED:
                    target_line_no += 1
                    added += 1
                elif line_type == LINE_TYPE_REMOVED:
                    source_line_no += 1
                    removed += 1
                elif line_type == LINE_TYPE_CONTEXT:
                    target_line_no += 1
                    source_line_no += 1

                # no file content tracking
                original_line = None

            else:
                # parse diff line content
                valid_line = RE_HUNK_BODY_LINE.match(line)
                if not valid_line:
                    valid_line = RE_HUNK_EMPTY_BODY_LINE.match(line)

                if not valid_line:
                    raise UnidiffParseError(
                        f'Hunk diff line expected: {line}')

                line_type = valid_line.group('line_type')
                if line_type == LINE_TYPE_EMPTY:
                    line_type = LINE_TYPE_CONTEXT

                value = valid_line.group('value')
                original_line = Line(value, line_type=line_type)

                if line_type == LINE_TYPE_ADDED:
                    original_line.target_line_no = target_line_no
                    target_line_no += 1
                elif line_type == LINE_TYPE_REMOVED:
                    original_line.source_line_no = source_line_no
                    source_line_no += 1
                elif line_type == LINE_TYPE_CONTEXT:
                    original_line.target_line_no = target_line_no
                    original_line.source_line_no = source_line_no
                    target_line_no += 1
                    source_line_no += 1
                elif line_type == LINE_TYPE_NO_NEWLINE:
                    pass
                else:
                    original_line = None

            # stop parsing if we got past expected number of lines
            if (source_line_no > expected_source_end or
                    target_line_no > expected_target_end):
                raise UnidiffParseError('Hunk is longer than expected')

            if original_line:
                original_line.diff_line_no = diff_line_no
                hunk.append(original_line)

            # if hunk source/target lengths are ok, hunk is complete
            if (source_line_no == expected_source_end and
                    target_line_no == expected_target_end):
                break

        # report an error if we haven't got expected number of lines
        if (source_line_no < expected_source_end or
                target_line_no < expected_target_end):
            raise UnidiffParseError('Hunk is shorter than expected')

        if metadata_only:
            # HACK: set fixed calculated values when metadata_only is enabled
            hunk._added = added
            hunk._removed = removed

        self.append(hunk)

    def _add_no_newline_marker_to_last_hunk(self) -> None:
        if not self:
            raise UnidiffParseError(
                'Unexpected marker:' + LINE_VALUE_NO_NEWLINE)
        last_hunk = self[-1]
        last_hunk.append(
            Line(LINE_VALUE_NO_NEWLINE + '\n', line_type=LINE_TYPE_NO_NEWLINE))

    def _append_trailing_empty_line(self) -> None:
        if not self:
            raise UnidiffParseError('Unexpected trailing newline character')
        last_hunk = self[-1]
        last_hunk.append(Line('\n', line_type=LINE_TYPE_EMPTY))

    @property
    def path(self) -> str:
        """Return the file path abstracted from VCS."""
        filepath = self.source_file
        if filepath in (None, DEV_NULL) or (
                self.is_rename and self.target_file not in (None, DEV_NULL)):
            # if this is a rename, prefer the target filename
            filepath = self.target_file

        quoted = filepath.startswith('"') and filepath.endswith('"')
        if quoted:
            filepath = filepath[1:-1]

        if RE_PATCH_FILE_PREFIX.match(filepath):
            filepath = filepath[2:]

        if quoted:
            filepath = f'"{filepath}"'

        return filepath

    @property
    def added(self) -> int:
        """Return the file total added lines."""
        return sum(hunk.added for hunk in self)

    @property
    def removed(self) -> int:
        """Return the file total removed lines."""
        return sum(hunk.removed for hunk in self)

    @property
    def is_rename(self) -> bool:
        return (self.source_file != DEV_NULL
            and self.target_file != DEV_NULL
            and self.source_file[2:] != self.target_file[2:])

    @property
    def is_added_file(self) -> bool:
        """Return True if this patch adds the file."""
        if self.source_file == DEV_NULL:
            return True
        return (len(self) == 1 and self[0].source_start == 0 and
                self[0].source_length == 0)

    @property
    def is_removed_file(self) -> bool:
        """Return True if this patch removes the file."""
        if self.target_file == DEV_NULL:
            return True
        return (len(self) == 1 and self[0].target_start == 0 and
                self[0].target_length == 0)

    @property
    def is_modified_file(self) -> bool:
        """Return True if this patch modifies the file."""
        return not (self.is_added_file or self.is_removed_file)

    @property
    def is_symlink(self) -> bool:
        """Return True if the patched file is a symbolic link."""
        # prefer the target mode; fall back to the source mode (e.g. a
        # removed symlink only carries the old mode)
        mode = self.target_mode if self.target_mode is not None else self.source_mode
        return mode == SYMLINK_FILE_MODE


class PatchSet(list[PatchedFile]):
    """A list of PatchedFiles."""

    def __init__(self, f: StringIO | str | bytes | Iterable[str],
                 encoding: str | None = None,
                 metadata_only: bool = False) -> None:
        super().__init__()

        # convert str/bytes inputs to StringIO objects (bytes are decoded,
        # defaulting to UTF-8 when no encoding is given)
        if isinstance(f, (str, bytes)):
            f = self._convert_string(f, encoding)
            # the data has already been decoded into text
            encoding = None

        # make sure we pass an iterator object to parse
        data = iter(f)
        # if encoding is None, assume we are reading unicode data
        # when metadata_only is True, only perform a minimal metadata parsing
        # (ie. hunks without content) which is around 2.5-6 times faster;
        # it will still validate the diff metadata consistency and get counts
        self._parse(data, encoding=encoding, metadata_only=metadata_only)

    def __repr__(self) -> str:
        return f'<PatchSet: {super().__repr__()}>'

    def __str__(self) -> str:
        return ''.join(str(patched_file) for patched_file in self)

    def _parse(self, diff: Iterable, encoding: str | None,
               metadata_only: bool) -> None:
        current_file = None
        patch_info = None

        diff_lines = enumerate(diff, 1)
        for diff_line_no, line in diff_lines:
            if encoding is not None:
                line = line.decode(encoding)

            # check for a git file rename
            is_diff_git_header = RE_DIFF_GIT_HEADER.match(line) or \
                RE_DIFF_GIT_HEADER_URI_LIKE.match(line) or \
                RE_DIFF_GIT_HEADER_NO_PREFIX.match(line)
            if is_diff_git_header:
                patch_info = PatchInfo()
                source_file = is_diff_git_header.group('source')
                target_file = is_diff_git_header.group('target')
                current_file = PatchedFile(
                    patch_info, source_file, target_file, None, None,
                    diff_line_no=diff_line_no)
                self.append(current_file)
                patch_info.append(line)
                continue

            # check for a git new file
            is_diff_git_new_file = RE_DIFF_GIT_NEW_FILE.match(line)
            if is_diff_git_new_file:
                if current_file is None or patch_info is None:
                    raise UnidiffParseError(f'Unexpected new file found: {line}')
                current_file.source_file = DEV_NULL
                current_file.target_mode = is_diff_git_new_file.group('mode')
                patch_info.append(line)
                continue

            # check for a git deleted file
            is_diff_git_deleted_file = RE_DIFF_GIT_DELETED_FILE.match(line)
            if is_diff_git_deleted_file:
                if current_file is None or patch_info is None:
                    raise UnidiffParseError(f'Unexpected deleted file found: {line}')
                current_file.target_file = DEV_NULL
                current_file.source_mode = is_diff_git_deleted_file.group('mode')
                patch_info.append(line)
                continue

            # check for git file mode change / index lines (extract the mode
            # but keep the line as patch info so the diff still round-trips)
            if current_file is not None and patch_info is not None:
                is_diff_git_old_mode = RE_DIFF_GIT_OLD_MODE.match(line)
                if is_diff_git_old_mode:
                    current_file.source_mode = is_diff_git_old_mode.group('mode')
                    patch_info.append(line)
                    continue

                is_diff_git_new_mode = RE_DIFF_GIT_NEW_MODE.match(line)
                if is_diff_git_new_mode:
                    current_file.target_mode = is_diff_git_new_mode.group('mode')
                    patch_info.append(line)
                    continue

                is_diff_git_index = RE_DIFF_GIT_INDEX.match(line)
                if is_diff_git_index:
                    # an unchanged index mode applies to both source and target
                    mode = is_diff_git_index.group('mode')
                    if current_file.source_mode is None:
                        current_file.source_mode = mode
                    if current_file.target_mode is None:
                        current_file.target_mode = mode
                    patch_info.append(line)
                    continue

            # check for source file header
            is_source_filename = RE_SOURCE_FILENAME.match(line)
            if is_source_filename:
                source_file = is_source_filename.group('filename')
                source_timestamp = is_source_filename.group('timestamp')
                # reset current file, unless we are processing a rename
                # (in that case, source files should match)
                if current_file is not None and current_file.source_file != source_file:
                    current_file = None
                elif current_file is not None:
                    current_file.source_timestamp = source_timestamp
                continue

            # check for target file header
            is_target_filename = RE_TARGET_FILENAME.match(line)
            if is_target_filename:
                target_file = is_target_filename.group('filename')
                target_timestamp = is_target_filename.group('timestamp')
                if current_file is not None and not (current_file.target_file == target_file):
                    raise UnidiffParseError(f'Target without source: {line}')
                if current_file is None:
                    # add current file to PatchSet
                    current_file = PatchedFile(
                        patch_info, source_file, target_file,
                        source_timestamp, target_timestamp,
                        diff_line_no=diff_line_no)
                    self.append(current_file)
                    patch_info = None
                else:
                    current_file.target_timestamp = target_timestamp
                continue

            # check for hunk header
            is_hunk_header = RE_HUNK_HEADER.match(line)
            if is_hunk_header:
                patch_info = None
                if current_file is None:
                    raise UnidiffParseError(f'Unexpected hunk found: {line}')
                current_file._parse_hunk(line, diff_lines, encoding, metadata_only)
                continue

            # check for no newline marker
            is_no_newline = RE_NO_NEWLINE_MARKER.match(line)
            if is_no_newline:
                if current_file is None:
                    raise UnidiffParseError(f'Unexpected marker: {line}')
                current_file._add_no_newline_marker_to_last_hunk()
                continue

            # sometimes hunks can be followed by empty lines; only attach the
            # empty line to the current file when it actually has hunks,
            # otherwise (e.g. a hunkless rename in git format-patch output) it
            # is just a separator and belongs to the surrounding patch info
            if line == '\n' and current_file:
                current_file._append_trailing_empty_line()
                continue

            # if nothing has matched above then this line is a patch info
            if patch_info is None:
                current_file = None
                patch_info = PatchInfo()

            is_binary_diff = RE_BINARY_DIFF.match(line)
            if is_binary_diff:
                source_file = is_binary_diff.group('source_filename')
                target_file = is_binary_diff.group('target_filename')
                patch_info.append(line)
                if current_file is not None:
                    current_file.is_binary_file = True
                else:
                    current_file = PatchedFile(
                        patch_info, source_file, target_file, is_binary_file=True,
                        diff_line_no=diff_line_no)
                    self.append(current_file)
                patch_info = None
                current_file = None
                continue

            if line == 'GIT binary patch\n':
                if current_file is None:
                    raise UnidiffParseError(f'Unexpected binary patch marker: {line}')
                current_file.is_binary_file = True
                patch_info = None
                current_file = None
                continue

            patch_info.append(line)

    @classmethod
    def from_filename(cls, filename: str, encoding: str = DEFAULT_ENCODING,
                      errors: str | None = None,
                      newline: str | None = None,
                      metadata_only: bool = False) -> PatchSet:
        """Return a PatchSet instance given a diff filename."""
        with pathlib.Path(filename).open(encoding=encoding, errors=errors, newline=newline) as f:
            return cls(f, metadata_only=metadata_only)

    @staticmethod
    def _convert_string(data: str | bytes, encoding: str | None = None,
                        errors: str = 'strict') -> StringIO:
        if isinstance(data, bytes):
            # decode bytes input, defaulting to UTF-8 when no encoding is given
            data = data.decode(encoding or DEFAULT_ENCODING, errors)
        return StringIO(data)

    @classmethod
    def from_string(cls, data: str | bytes, encoding: str | None = None,
                    errors: str = 'strict', metadata_only: bool = False) -> PatchSet:
        """Return a PatchSet instance given a diff string."""
        return cls(cls._convert_string(data, encoding, errors),
                   metadata_only=metadata_only)

    @property
    def added_files(self) -> list[PatchedFile]:
        """Return patch added files as a list."""
        return [f for f in self if f.is_added_file]

    @property
    def removed_files(self) -> list[PatchedFile]:
        """Return patch removed files as a list."""
        return [f for f in self if f.is_removed_file]

    @property
    def modified_files(self) -> list[PatchedFile]:
        """Return patch modified files as a list."""
        return [f for f in self if f.is_modified_file]

    @property
    def added(self) -> int:
        """Return the patch total added lines."""
        return sum(f.added for f in self)

    @property
    def removed(self) -> int:
        """Return the patch total removed lines."""
        return sum(f.removed for f in self)
