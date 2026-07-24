Unidiff
=======

Simple Python library to parse and interact with unified diff data.

.. image:: https://github.com/matiasb/python-unidiff/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/matiasb/python-unidiff/actions/workflows/ci.yml

Installing unidiff
------------------

::

    $ pip install unidiff


Quick start
-----------

.. code-block:: python

    >>> import urllib.request
    >>> from unidiff import PatchSet
    >>> diff = urllib.request.urlopen('https://github.com/matiasb/python-unidiff/pull/3.diff')
    >>> encoding = diff.headers.get_charsets()[0]
    >>> patch = PatchSet(diff, encoding=encoding)
    >>> patch
    <PatchSet: [<PatchedFile: .gitignore>, <PatchedFile: unidiff/patch.py>, <PatchedFile: unidiff/utils.py>]>
    >>> patch[0]
    <PatchedFile: .gitignore>
    >>> patch[0].is_added_file
    True
    >>> patch[0].added
    6
    >>> patch[1]
    <PatchedFile: unidiff/patch.py>
    >>> patch[1].added, patch[1].removed
    (20, 11)
    >>> len(patch[1])
    6
    >>> patch[1][2]
    <Hunk: @@ 109,14 110,21 @@ def __repr__(self):>
    >>> patch[2]
    <PatchedFile: unidiff/utils.py>
    >>> print(patch[2])
    diff --git a/unidiff/utils.py b/unidiff/utils.py
    index eae63e6..29c896a 100644
    --- a/unidiff/utils.py
    +++ b/unidiff/utils.py
    @@ -37,4 +37,3 @@
     # - deleted line
     # \ No newline case (ignore)
     RE_HUNK_BODY_LINE = re.compile(r'^([- \+\\])')
    -


Load unified diff data by instantiating :code:`PatchSet` with a file-like object as
argument, or using :code:`PatchSet.from_filename` class method to read diff from file.

A :code:`PatchSet` is a list of files updated by the given patch. For each :code:`PatchedFile`
you can get stats (if it is a new, removed or modified file; the source/target
lines; etc), besides having access to each hunk (also like a list) and its
respective info.

At any point you can get the string representation of the current object, and
that will return the unified diff data of it.

As a quick example of what can be done, check the unidiff/__main__.py file.

Also, once installed, unidiff provides a command-line program that displays
information from diff data (a file, or stdin). For example:

::

    $ git diff | unidiff
    Summary
    -------
    README.md: +6 additions, -0 deletions

    1 modified file(s), 0 added file(s), 0 removed file(s)
    Total: 6 addition(s), 0 deletion(s)


Load a local diff file
----------------------

To instantiate :code:`PatchSet` from a local file, you can use:

.. code-block:: python

    >>> from unidiff import PatchSet
    >>> patch = PatchSet.from_filename('tests/samples/bzr.diff', encoding='utf-8')
    >>> patch
    <PatchSet: [<PatchedFile: added_file>, <PatchedFile: modified_file>, <PatchedFile: removed_file>]>

Notice the (optional) :code:`encoding` parameter. If not specified, unicode input will be expected (or, when the data is :code:`bytes`, it is decoded using :code:`encoding`, defaulting to UTF-8). Or alternatively:

.. code-block:: python

    >>> import codecs
    >>> from unidiff import PatchSet
    >>> with codecs.open('tests/samples/bzr.diff', 'r', encoding='utf-8') as diff:
    ...     patch = PatchSet(diff)
    ...
    >>> patch
    <PatchSet: [<PatchedFile: added_file>, <PatchedFile: modified_file>, <PatchedFile: removed_file>]>

Finally, you can also instantiate :code:`PatchSet` passing any iterable (and encoding, if needed):

.. code-block:: python

    >>> from unidiff import PatchSet
    >>> with open('tests/samples/bzr.diff', 'r') as diff:
    ...     data = diff.readlines()
    ...
    >>> patch = PatchSet(data)
    >>> patch
    <PatchSet: [<PatchedFile: added_file>, <PatchedFile: modified_file>, <PatchedFile: removed_file>]>

If you don't need to be able to rebuild the original unified diff input, you can pass
:code:`metadata_only=True` (defaults to :code:`False`), which should help making the
parsing more efficient:

.. code-block:: python

    >>> from unidiff import PatchSet
    >>> patch = PatchSet.from_filename('tests/samples/bzr.diff', encoding='utf-8', metadata_only=True)


Inspecting files, hunks and lines
---------------------------------

.. code-block:: python

    >>> from unidiff import PatchSet
    >>> patch = PatchSet.from_string(
    ...     '--- a/story.txt\n'
    ...     '+++ b/story.txt\n'
    ...     '@@ -1,4 +1,4 @@\n'
    ...     ' Once upon a time\n'
    ...     '-there was a bug\n'
    ...     '+there was a fix\n'
    ...     ' the end\n'
    ...     ' really\n')
    >>> patched_file = patch[0]
    >>> patched_file.path
    'story.txt'
    >>> patched_file.is_modified_file
    True
    >>> patched_file.added, patched_file.removed
    (1, 1)
    >>> hunk = patched_file[0]
    >>> hunk.source_start, hunk.target_start
    (1, 1)
    >>> removed = [line for line in hunk if line.is_removed]
    >>> len(removed)
    1
    >>> removed[0].value
    'there was a bug\n'
    >>> removed[0].source_line_no
    2
    >>> added = [line for line in hunk if line.is_added]
    >>> added[0].value, added[0].target_line_no
    ('there was a fix\n', 2)


Git file modes, symlinks and line numbers
------------------------------------------

For git diffs, the file mode is exposed through the :code:`source_mode` and
:code:`target_mode` attributes (e.g. :code:`'100644'`, :code:`'100755'`,
:code:`'120000'`), or :code:`None` when unknown. The :code:`is_symlink`
property is a shortcut to detect symbolic links (mode :code:`120000`):

.. code-block:: python

    >>> from unidiff import PatchSet
    >>> patch = PatchSet.from_filename('tests/samples/git_symlink.diff')
    >>> patched_file = patch[0]
    >>> patched_file.path
    'bin/check'
    >>> patched_file.is_added_file
    True
    >>> patched_file.target_mode
    '120000'
    >>> patched_file.is_symlink
    True

Each :code:`PatchedFile` also exposes :code:`diff_line_no`, the 1-based line
number in the diff where its entry starts. This is useful to locate files that
have no hunks, such as binary changes:

.. code-block:: python

    >>> from unidiff import PatchSet
    >>> patch = PatchSet.from_filename('tests/samples/debdiff.diff')
    >>> [(f.path, f.is_binary_file, f.diff_line_no) for f in patch]
    [('new/added.txt', False, 3), ('/t/p2/a.png', True, 6), ('/t/p2/b.png', True, 7)]


Parsing from bytes
------------------

:code:`PatchSet` and :code:`PatchSet.from_string` also accept :code:`bytes`,
which are decoded using the given :code:`encoding` (defaulting to UTF-8):

.. code-block:: python

    >>> from unidiff import PatchSet
    >>> patch = PatchSet(b'--- a/f\n+++ b/f\n@@ -1,2 +1,2 @@\n hola\n-mundo\n+world\n')
    >>> patch.added, patch.removed
    (1, 1)


Diffs with embedded carriage returns or control characters
----------------------------------------------------------

Diff hunk content may include arbitrary bytes, such as a lone carriage return
(:code:`\\r`) or other control characters (for example the output of some
editors or generated patches). By default Python opens text files in universal
newlines mode, which translates a lone :code:`\\r` into a line break and would
split such content across lines, breaking parsing.

To parse these diffs, read the data without universal-newline translation by
passing :code:`newline='\\n'` (so lines are split only on :code:`\\n`):

.. code-block:: python

    >>> from unidiff import PatchSet
    >>> patch = PatchSet.from_filename('tests/samples/git_cr.diff', newline='\n')

Equivalently, open the file yourself with :code:`newline='\\n'` (or in binary
mode passing the :code:`encoding` argument) before handing it to
:code:`PatchSet`.


References
----------

* https://en.wikipedia.org/wiki/Diff_utility
* https://www.artima.com/weblogs/viewpost.jsp?thread=164293
