Unidiff
=======

Simple Python library to parse and interact with unified diff data.

.. image:: https://www.travis-ci.com/matiasb/python-unidiff.svg?branch=master
    :target: https://travis-ci.com/matiasb/python-unidiff

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

As a quick example of what can be done, check bin/unidiff file.

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

Notice the (optional) :code:`encoding` parameter. If not specified, unicode input will be expected. Or alternatively:

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


References
----------

* https://en.wikipedia.org/wiki/Diff_utility
* https://www.artima.com/weblogs/viewpost.jsp?thread=164293
