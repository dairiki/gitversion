# -*- coding: utf-8 -*-
""" Compute a valid PEP440 version number based on git history.

If possible, the version is computed from the output of ``git describe``.
If that is successful, the version string is written to the file
``RELEASE-VERSION``.

If ``git describe`` fails (most likely because we’re in an unpacked
copy of an sdist rather than in a git working copy) then we fall back
on reading the contents of the ``RELEASE-VERSION`` file.

Usage
=====

Copy this file into your source directory, then use the ``get_version``
function to compute the package version in your ``setup.py``::

    from gitversion import get_version

    setup(
        version=get_version(),
        # ... all the rest ...
    )

The Version Cache
-----------------

The version cache file, ``RELEASE-VERSION``, should *not* be checked
into ``git`` — please add it to your top-level ``.gitignore``.

You will probably want to distribute ``RELEASE-VERSION`` in your
sdist tarballs. To do that, add the following line to your ``MANIFEST.in``:

    include RELEASE-VERSION

Author
======

:Originally by:
    Douglas Creager <dcreager@dcreager.net>
:Modified by:
    Jeff Dairiki <dairiki@dairiki.org>

This file is placed into the public domain.

"""


import errno
import re
from tempfile import TemporaryFile
from subprocess import Popen, PIPE

__version__ = '1.0'
__all__ = ("get_version")

# Name of file in which the version number is cached
VERSION_CACHE = 'RELEASE-VERSION'

class GitError(Exception):
    pass

class GitNotFound(GitError):
    """ The ``git`` command was not found.
    """

class GitFailed(GitError):
    def __str__(self):
        return "{cmd!r} failed with exit status {code!r}:\n{output}".format(
            cmd=' '.join(self.cmd),
            code=self.returncode,
            output=self.detail)

    @property
    def cmd(self):
        return self.args[0]

    @property
    def returncode(self):
        return self.args[1]

    @property
    def detail(self):
        return self.args[2]


GIT_DESCRIPION_re = re.compile(
    r'''\A \s*
        (?P<release>.*?)
        (?:
           -(?P<post>\d+)
           -g(?:[\da-f]+)               # SHA
        )?
        (?P<dirty>-dirty)?
        \s* \Z''', re.X)

# Valid PEP440 release versions
RELEASE_VERSION_re = re.compile(r'\A\d+(\.\d+)*((?:a|b|c|rc)\d+)?\Z')

def get_version(**kwargs):
    """ Calculate a valid PEP440 version number based on git history.

    If possible the version is computed from the output of ``git describe``.
    If that is successful, the version string is written to the file
    ``RELEASE-VERSION``.

    If ``git describe`` fails (most likely because we’re in an unpacked
    copy of an sdist rather than in a git working copy) then we fall back
    on reading the contents of the ``RELEASE-VERSION`` file.

    """
    cached_version = get_cached_version()
    git_version = get_git_version(**kwargs)

    if git_version is None:
        if cached_version is None:
            raise RuntimeError("can not determine version number")
        return cached_version

    if cached_version != git_version:
        set_cached_version(git_version)
    return git_version

def get_git_version(**kwargs):
    try:
        run_git('rev-parse', '--is-inside-work-tree', **kwargs)
    except GitError:
        # not a git repo, or 'git' command not found
        return None
    try:
        output = run_git('describe', '--dirty', **kwargs)
    except GitFailed as ex:
        if ex.returncode != 128:
            raise
        # No releases have been tagged
        return '0.dev%d' % get_number_of_commits_in_head(**kwargs)

    output = ''.join(output).strip()
    m = GIT_DESCRIPION_re.match(output)
    if not m:
        raise GitError(
            "can not parse the output of git describe (%r)" % output)

    release, post, dirty = m.groups()
    post = int(post) if post else 0

    if not RELEASE_VERSION_re.match(release):
        raise GitError("invalid release version (%r)" % release)

    version = release
    if dirty:
        version += ".post%d.dev0" % (post + 1)
    elif post:
        version += '.post%d' % post
    return version

def get_number_of_commits_in_head(**kwargs):
    try:
        return len(run_git('rev-list', 'HEAD', **kwargs))
    except GitFailed as ex:
        if ex.returncode != 128:
            raise
        return 0

def run_git(*args, **kwargs):
    git_cmd = kwargs.get('git_cmd', 'git')
    cwd = kwargs.get('cwd')
    cmd = (git_cmd,) + args
    stderr = TemporaryFile()
    try:
        proc = Popen(cmd, stdout=PIPE, stderr=stderr, cwd=cwd)
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            raise GitNotFound("%r not found in PATH" % git_cmd)
        raise

    output = proc.stdout.readlines()
    if proc.wait() != 0:
        stderr.seek(0)
        raise GitFailed(cmd, proc.returncode, stderr.read().rstrip())
    return output



def get_cached_version():
    try:
        with file(VERSION_CACHE) as f:
            return f.read().strip()
    except IOError as ex:
        if ex.errno == errno.ENOENT:
            return None
        raise

def set_cached_version(version):
    with file(VERSION_CACHE, "w") as f:
        return f.write(version + "\n")

if __name__ == "__main__":
    print get_version()
