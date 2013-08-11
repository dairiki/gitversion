==========
Gitversion
==========

Description
===========

This ``gitversion.py`` provides a function which computes a version
number from the output of ``git describe --dirty``.  The idea comes
from this `blog entry`__ by Douglas Creager: releases are tagged with
annotated git tags.  This version has been modified to produce PEP440_
compliant version numbers.

__ http://dcreager.net/2010/02/10/setuptools-git-version-numbers/
.. _PEP440: http://www.python.org/dev/peps/pep-0440/

Some example version identifier which may be produced by this ``get_version``
are:

    1.1rc2

       The git working tree is clean, and the HEAD is tagged with an
       annotated tag named ``1.1rc2``

    1.1.post3

       The git working tree is clean, and the most recent annotated
       tag is ``1.1`` on ``HEAD~3``.

    1.1.post1.dev0

       The git working tree is dirty, and the HEAD is tagged with an
       annotated tag named ``1.1``.


Usage
=====

Setup
~~~~~

**1. Adjust your ``setup.py``**


    Copy gitversion.py_ into your source directory, then do something like
    this to compute the package version in your ``setup.py``::

        from gitversion import get_version

        # ...
        setup(
            version=get_version(),
            # ...
        )


**2. Adjust your ``.gitignore``**

    The version cache file, ``RELEASE-VERSION`` is automatically
    updated by ``get_version``.  It should **not** be checked into
    ``git``.  Please add it to your top-level ``.gitignore``.

**3. Adjust your ``MANIFEST.in``**

    You should most likely distribute the ``RELEASE-VERSION`` file in
    your *sdist* tarballs. To do that, add ``include RELEASE-VERSION``
    to your ``MANIFEST.in``.

.. _gitversion.py:
     https://raw.github.com/dairiki/gitversion/master/gitversion.py


Marking Releases
~~~~~~~~~~~~~~~~

When you make a release of your package, create an annotated tag.  The
name of the tag must be equal to the release version.  It must match
the regular expression ``[0-9]+(\.[0-9]+)*((a|b|c|rc)[0-9]+)?``.



Author
======

:Originally by:
    Douglas Creager <dcreager@dcreager.net>
:Modified by:
    Jeff Dairiki <dairiki@dairiki.org>
