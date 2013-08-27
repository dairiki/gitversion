=======
Changes
=======

Version 1.0.1
=============

Bug Fixes
---------

- To avoid generating bogus version number when run, e.g., by tox in a
  subdirectory of a git working tree for some altogether different package,
  don’t generate a git-based version unless running from the top-level
  directory of a git working tree.
