# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

from contextlib import contextmanager
import os
import shutil
from subprocess import Popen, PIPE, STDOUT
import tempfile
import unittest

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

    def touch(self, filename):
        with file(os.path.join(self.dir, filename), "a") as f:
            f.write('\n')

    def run_git(self, *args):
        cmd = ['git']
        cmd.extend(args)
        git = Popen(cmd, cwd=self.dir, stdout=PIPE, stderr=STDOUT)
        output = git.stdout.read()
        if git.wait() != 0:
            self.fail("git failed with status %r:\n%s"
                      % (git.returncode, output))

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

    def get_git_version(self, **kwargs):
        from gitversion import get_git_version
        with in_directory(self.dir):
            return get_git_version(**kwargs)

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
    def test_released(self):
        self.git_init()
        self.make_commit(tag='1.0')
        self.assertEqual(self.get_git_version(), '1.0')

    def test_post(self):
        self.git_init()
        self.make_commit(tag='1.0rc1')
        self.make_commit()
        self.assertEqual(self.get_git_version(), '1.0rc1.post1')

    def test_dirty(self):
        self.git_init()
        self.make_commit(tag='2.1.2')
        self.touch('f')
        self.assertEqual(self.get_git_version(), '2.1.2.post1.dev0')

    def test_post_dirty(self):
        self.git_init()
        self.make_commit(tag='13')
        self.make_commit()
        self.make_commit()
        self.touch('f')
        self.assertEqual(self.get_git_version(), '13.post3.dev0')

    def test_no_git(self):
        self.assertEqual(self.get_git_version(git_cmd='/no/such/file'), None)

    def test_no_commit(self):
        self.git_init()
        self.assertEqual(self.get_git_version(), '0.dev0')

    def test_no_tag(self):
        self.git_init()
        self.make_commit()
        self.assertEqual(self.get_git_version(), '0.dev1')

    def test_ignores_non_annotated_tag(self):
        self.git_init()
        self.make_commit(tag='42')
        self.make_commit()
        self.run_git('tag', '42.2')     # non-annotated tag
        self.assertEqual(self.get_git_version(), '42.post1')

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

class TestGitFailed(unittest.TestCase):
    def make_one(self, cmd, returncode, detail):
        from gitversion import GitFailed
        return GitFailed(cmd, returncode, detail)

    def test_stringification(self):
        ex = self.make_one(('foo',), 42, 'DETAIL')
        self.assertEqual(str(ex), "'foo' failed with exit status 42:\nDETAIL")

if __name__ == '__main__':
    unittest.main()
