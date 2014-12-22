#!/usr/bin/env python3

# Copyright (c) 2014, Jesse Elwell
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of python-backup nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import unittest

sys.path.append('../')

from backup.BackupManager import backup_manager

class MinimumBackupManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.bm = backup_manager('/home', 'host', '/backups')

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], 'host')

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertIn('-v', r)
        self.assertIn('-az', r)

    def tearDown(self):
        pass

class BackupManagerWithUserTestCase(unittest.TestCase):
    def setUp(self):
        self.bm = backup_manager('/home', 'host', '/backups/', user='user')

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], 'user@host')

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertIn('-v', r)
        self.assertIn('-az', r)

    def tearDown(self):
        pass
