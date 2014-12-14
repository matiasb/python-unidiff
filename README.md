Unidiff
=======

Simple Python library to parse and interact with unified diff data.

[![Build Status](https://travis-ci.org/matiasb/python-unidiff.png?branch=master)](https://travis-ci.org/matiasb/python-unidiff)


Installing unidiff
------------------

    $ pip install unidiff


Quick start
-----------

    >>> import urllib2
    >>> from unidiff import PatchSet
    >>> diff = urllib2.urlopen('https://github.com/matiasb/python-unidiff/pull/3.diff')
    >>> patch = PatchSet(diff)
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
    >>> print patch[2]
    --- a/unidiff/utils.py
    +++ b/unidiff/utils.py
    @@ -37,4 +37,3 @@ 
    # - deleted line
    # \ No newline case (ignore)
    RE_HUNK_BODY_LINE = re.compile(r'^([- \+\\])')
    -

Load unified diff data by instantiating PatchSet with a file-like object as
argument, or using PatchSet.from_filename class method to read diff from file.

A PatchSet is a list of files updated by the given patch. For each PatchedFile
you can get stats (if it is a new, removed or modified file; the source/target
lines; etc), besides having access to each hunk (also like a list) and its
respective info.

At any point you can get the string representation of the current object, and
that will return the unified diff data of it.

As a quick example of what can be done, check bin/unidiff file.

Also, once installed, unidiff provides a command-line program that displays
information from diff data (a file, or stdin). For example:

    $ git diff | unidiff
    Summary
    -------
    README.md: +6 additions, -0 deletions

    1 modified file(s), 0 added file(s), 0 removed file(s)
    Total: 6 addition(s), 0 deletion(s)


References
----------

 * http://en.wikipedia.org/wiki/Diff_utility
 * http://www.artima.com/weblogs/viewpost.jsp?thread=164293
