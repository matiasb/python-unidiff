# -*- coding: utf-8 -*-
# Author: Matías Bordese


"""Useful constants and regexes used by the module."""

import re

RE_SOURCE_FILENAME = re.compile(r'^--- (?P<filename>[^\t]+)')
RE_TARGET_FILENAME = re.compile(r'^\+\+\+ (?P<filename>[^\t]+)')

# @@ (source offset, length) (target offset, length) @@
RE_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?\ @@")

#   kept line (context)
# + added line
# - deleted line
# \ No newline case (ignore)
RE_HUNK_BODY_LINE = re.compile(r'^([- \+\\])')

