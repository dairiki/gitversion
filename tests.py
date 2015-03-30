# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

from contextlib import contextmanager
import os
import shutil
from subprocess import check_call, Popen, PIPE, STDOUT
import sys
import tempfile
import unittest

PY3 = sys.version_info[0] == 3
if PY3:                         # pragma: no cover
    string_types = str
else:
    string_types = basestring


@contextmanager
def in_directory(directory):
    save_cwd = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(save_cwd)


class _TestBase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def touch(self, filename, content='\n'):
        with open(os.path.join(self.dir, filename), "a") as f:
            f.write(content)

    def run_git(self, *args):
        cmd = ['git']
        cmd.extend(args)
        git = Popen(cmd, cwd=self.dir, stdout=PIPE, stderr=STDOUT)
        try:
            output = git.stdout.read()
            if git.wait() != 0:
                self.fail("git failed with status %r:\n%s"
                          % (git.returncode, output))
        finally:
            git.stdout.close()

    def git_init(self):
        self.run_git('init')

    def make_commit(self, tag=None):
        self.touch('f')
        self.run_git('add', 'f')
        self.run_git('commit', '-m', 'test', 'f')
        if tag is not None:
            self.make_tag(tag)

    def make_tag(self, tag):
        self.run_git('tag', '-a', '-m', 'test', tag)

    def get_version(self):
        from gitversion import get_version
        with in_directory(self.dir):
            return get_version()

    def get_cached_version(self):
        from gitversion import get_cached_version
        with in_directory(self.dir):
            return get_cached_version()

    def set_cached_version(self, version):
        from gitversion import set_cached_version
        with in_directory(self.dir):
            return set_cached_version(version)


class Test_get_git_version(_TestBase):
    def call_it(self, **kwargs):
        from gitversion import get_git_version
        cwd = kwargs.pop('cwd', self.dir)
        with in_directory(cwd):
            return get_git_version(**kwargs)

    def test_released(self):
        self.git_init()
        self.make_commit(tag='1.0')
        self.assertEqual(self.call_it(), '1.0')

    def test_post(self):
        self.git_init()
        self.make_commit(tag='1.0rc1')
        self.make_commit()
        self.assertEqual(self.call_it(), '1.0rc1.post1')

    def test_dirty(self):
        self.git_init()
        self.make_commit(tag='2.1.2')
        self.touch('f')
        self.assertEqual(self.call_it(), '2.1.2.post1.dev0')

    def test_post_dirty(self):
        self.git_init()
        self.make_commit(tag='13')
        self.make_commit()
        self.make_commit()
        self.touch('f')
        self.assertEqual(self.call_it(), '13.post3.dev0')

    def test_git_not_initialized(self):
        self.assertEqual(self.call_it(), None)

    def test_git_not_installed(self):
        self.assertEqual(self.call_it(git_cmd='/no/such/file'), None)

    def test_no_commit(self):
        self.git_init()
        self.assertEqual(self.call_it(), '0.dev0')

    def test_no_tag(self):
        self.git_init()
        self.make_commit()
        self.assertEqual(self.call_it(), '0.dev1')

    def test_ignores_non_annotated_tag(self):
        self.git_init()
        self.make_commit(tag='42')
        self.make_commit()
        self.run_git('tag', '42.2')     # non-annotated tag
        self.assertEqual(self.call_it(), '42.post1')

    def test_no_git_version_if_run_from_subdirectory(self):
        self.git_init()
        subdir = os.path.join(self.dir, 'subdir')
        os.mkdir(subdir)
        self.assertEqual(self.call_it(cwd=subdir), None)


class Test_get_version(_TestBase):
    def test_updates_cache(self):
        self.git_init()
        self.make_commit(tag='1.0')
        self.assertEqual(self.get_cached_version(), None)
        self.get_version()
        self.assertEqual(self.get_cached_version(), '1.0')
        self.make_commit()
        self.get_version()
        self.assertEqual(self.get_cached_version(), '1.0.post1')

    def test_uses_cache_if_git_unavailable(self):
        self.set_cached_version('42')
        self.assertEqual(self.get_version(), '42')

    def test_raises_runtime_error(self):
        self.assertRaises(RuntimeError, self.get_version)


class Test_get_number_of_commits_in_head(_TestBase):
    def call_it(self, **kw):
        from gitversion import get_number_of_commits_in_head
        with in_directory(self.dir):
            return get_number_of_commits_in_head(**kw)

    def test_returns_zero(self):
        self.run_git('init')
        self.assertEqual(self.call_it(), 0)

    def test_returns_one(self):
        self.run_git('init')
        self.touch('f')
        self.run_git('add', 'f')
        self.run_git('commit', '-m', 'bar')
        self.assertEqual(self.call_it(), 1)

    def test_raises_git_failed(self):
        from gitversion import GitFailed
        self.assertRaises(GitFailed, self.call_it, git_cmd='false')


class Test_run_git(_TestBase):
    def call_it(self, *args, **kw):
        from gitversion import run_git
        with in_directory(self.dir):
            return run_git(*args, **kw)

    def test_returns_output(self):
        output = self.call_it('init')
        self.assertTrue(
            output[0].startswith('Initialized empty Git repository '))
        assert isinstance(output[0], string_types)

    def test_raises_git_not_found(self):
        from gitversion import GitNotFound
        self.assertRaises(GitNotFound, self.call_it,
                          git_cmd=os.path.join(self.dir, 'does-not-exist'))

    def test_raises_oserror(self):
        # errno=EISDIR
        self.assertRaises(OSError, self.call_it, git_cmd=self.dir)

    def test_raises_git_failed(self):
        from gitversion import GitFailed
        try:
            self.call_it()
        except GitFailed as exc:
            assert isinstance(exc.detail, string_types)
        else:
            self.fail("GitFailed not raised")


class Test_get_cached_version(_TestBase):
    def call_it(self):
        from gitversion import get_cached_version
        with in_directory(self.dir):
            return get_cached_version()

    def test_returns_none(self):
        self.assertEqual(self.call_it(), None)

    def test_returns_version(self):
        with open(os.path.join(self.dir, 'RELEASE-VERSION'), 'w') as f:
            f.write('foo\n')
        self.assertEqual(self.call_it(), 'foo')

    def test_raises_error(self):
        os.mkdir(os.path.join(self.dir, 'RELEASE-VERSION'))
        self.assertRaises(IOError, self.call_it)  # errno=EISDIR


class TestGitFailed(unittest.TestCase):
    def make_one(self, cmd, returncode, detail):
        from gitversion import GitFailed
        return GitFailed(cmd, returncode, detail)

    def test_stringification(self):
        ex = self.make_one(('foo',), 42, 'DETAIL')
        self.assertEqual(str(ex), "'foo' failed with exit status 42:\nDETAIL")


class Test_run_as_script(unittest.TestCase):
    def test_run_it(self):
        with tempfile.TemporaryFile() as stdout:
            check_call((sys.executable, 'gitversion.py'), stdout=stdout)


if __name__ == '__main__':
    unittest.main()
