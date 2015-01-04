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
import random
import shutil
import sys
import time
import unittest

sys.path.append('../')

from backup.BackupManager import backup_manager
from backup.BackupPrinter import backup_printer
from backup.BackupExceptions import *

# To fake datetime objects for testing
from testfixtures import Replacer,test_datetime
from unittest.mock import patch

random.seed(4083)
################################################################################
################################################################################
## Test Case Base Class                                                       ##
## Base class for all test cases with some basic functions to create a source ##
## directory to work with, and check a backup to make sure all files/dirs are ##
## there.                                                                     ##
##                                                                            ##
################################################################################
################################################################################
class BackupManagerTestCase(unittest.TestCase):
    # Create default arguments used for every test case
    def create_def_args(self):
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }

    # Create/cleanup a source directory with a few random files to test with
    def create_test_src_dir(self):
        d = self.args['src']
        os.mkdir(d)
        # Write a few random files of data into there
        for i in range(5):
            with open(os.path.join(d, 'rand_file_{}'.format(i)), 'w+b') as f:
                by = [random.randrange(256) for j in range(4096)]
                f.write(bytes(by))
    def cleanup_test_src_dir(self):
        shutil.rmtree(self.args['src'])

    # Check a specific backup dir
    def check_backup_dir(self, backup_dir):
        backup_dir = os.path.join(self.args['dest'], backup_dir)
        ret = os.listdir(backup_dir)
        self.assertIn(os.path.basename(self.args['src']), ret)
        ret = sorted(os.listdir(os.path.join(backup_dir, self.args['src'])))
        self.assertEqual(ret,
            ['rand_file_0','rand_file_1','rand_file_2','rand_file_3','rand_file_4',]
        )

    # Mocks/restores the datetime object used by backup_manager
    def replace_datetime(self, dl=1):
        self.rp_datetime = Replacer()
        self.rp_datetime.replace('backup.BackupManager.datetime',
            test_datetime(2015, 1, 1, 12, 0, 0, delta=dl))
    def restore_datetime(self):
        self.rp_datetime.restore()

################################################################################
################################################################################
## Command Building Tests                                                     ##
## Tests to ensure that the base ssh and rsync commands are built correctly   ##
## under various circumstances.                                               ##
##                                                                            ##
################################################################################
################################################################################

class MinBackupManagerCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.bm = backup_manager(**self.args)

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], self.args['host'])

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')

class BackupManagerUserCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.args['user'] = 'user'
        self.bm = backup_manager(**self.args)

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1],
            '{}@{}'.format(self.args['user'], self.args['host']))

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')

class BackupManagerSSHKeyCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.args['ssh_key'] = '~/.ssh/id_rsa'
        self.bm = backup_manager(**self.args)

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], '-i')
        self.assertEqual(r[2], self.args['ssh_key'])
        self.assertEqual(r[3], self.args['host'])

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')
        self.assertEqual(r[3], '-e')
        self.assertEqual(r[4], 'ssh -i {}'.format(self.args['ssh_key']))

class BackupManagerUserSSHKeyCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.args['user'] = 'user',
        self.args['ssh_key'] = '~/.ssh/id_rsa'
        self.bm = backup_manager(**self.args)

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], '-i')
        self.assertEqual(r[2], self.args['ssh_key'])
        self.assertEqual(r[3],
            '{}@{}'.format(self.args['user'], self.args['host']))

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')
        self.assertEqual(r[3], '-e')
        self.assertEqual(r[4], 'ssh -i {}'.format(self.args['ssh_key']))

class BackupManagerRsyncBinCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.args['rsync_bin'] = 'RSYNC_BIN'
        self.bm = backup_manager(**self.args)

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], self.args['host'])

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'RSYNC_BIN')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')

class BackupManagerSSHBinKeyCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.args['ssh_bin'] = 'SSH_BIN'
        self.args['ssh_key'] = '~/.ssh/id_rsa'
        self.bm = backup_manager(**self.args)

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'SSH_BIN')
        self.assertEqual(r[1], '-i')
        self.assertEqual(r[2], self.args['ssh_key'])
        self.assertEqual(r[3], self.args['host'])

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')
        self.assertEqual(r[3], '-e')
        self.assertEqual(r[4], 'SSH_BIN -i {}'.format(self.args['ssh_key']))

################################################################################
################################################################################
## Source Directory Tests                                                     ##
## Tests realted to a non-existent source directory. All tests after this     ##
## will assume that it exists.                                                ##
##                                                                            ##
################################################################################
################################################################################

class NonExistentSrcDirTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.bm = backup_manager(**self.args)

        # Make sure source directory doesn't exist
        if os.access(self.args['src'], os.F_OK):
            shutil.rmtree(self.args['src'])

        # The destination directory should exist to avoid any errors from that
        os.mkdir(self.args['dest'])

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        self.assertEqual(self.bm.list_dest_backups(), [])

    def test_most_recent_backup(self):
        self.assertIsNone(self.bm.most_recent_backup([]))

    def test_create_backup(self):
        self.assertRaises(RsyncError, self.bm.create_backup)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)

    def tearDown(self):
        shutil.rmtree(self.args['dest'])

################################################################################
################################################################################
## Destination Directory Tests                                                ##
## Tests realted to different states of the destination directory.            ##
##                                                                            ##
################################################################################
################################################################################

class NonExistentDestDirTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.bm = backup_manager(**self.args)
        self.create_test_src_dir()

        # Make sure dest directory doesn't exist
        if os.access(self.args['dest'], os.F_OK):
            shutil.rmtree(self.args['dest'])

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        self.assertRaises(DestDirError, self.bm.list_dest_backups)

    def test_most_recent_backup(self):
        self.assertIsNone(self.bm.most_recent_backup([]))

    def test_create_backup(self):
        self.assertRaises(DestDirError, self.bm.create_backup)

    def test_remove_backups(self):
        self.assertRaises(DestDirError, self.bm.remove_backups)

    def tearDown(self):
        # Remove any directories that may have been created
        self.cleanup_test_src_dir()
        if os.access(self.args['dest'], os.F_OK):
            shutil.rmtree(self.args['dest'])

class BadDestDirTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_args()
        self.bm = backup_manager(**self.args)
        self.create_test_src_dir()

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_cannot_create_dest(self):
        with patch.object(self.bm, '_run_cmd', return_value=(1, '', '')) as mm:
            self.assertRaises(DestDirError, self.bm.check_dest)
            self.assertFalse(os.access(self.args['dest'], os.F_OK))

    def test_dest_exists_not_writable(self):
        os.mkdir(self.args['dest'], 555)
        self.assertRaises(DestDirError, self.bm.check_dest)
        self.assertFalse(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        self.assertRaises(DestDirError, self.bm.list_dest_backups)

    def test_most_recent_backup(self):
        self.assertIsNone(self.bm.most_recent_backup([]))

    def test_create_backup(self):
        self.assertRaises(DestDirError, self.bm.create_backup)

    def test_remove_backups(self):
        self.assertRaises(DestDirError, self.bm.remove_backups)

    def tearDown(self):
        # Remove any directories that may have been created
        self.cleanup_test_src_dir()
        if os.access(self.args['dest'], os.F_OK):
            if not os.access(self.args['dest'], os.W_OK):
                os.chmod(self.args['dest'], 777)
            shutil.rmtree(self.args['dest'])

# Destination directory exists but is empty
class EmptyDestDirTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], self.args['host'])

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertIn('-v', r)
        self.assertIn('-az', r)

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        self.assertEqual(self.bm.list_dest_backups(), [])

    def test_most_recent_backup(self):
        self.assertIsNone(self.bm.most_recent_backup([]))

    def test_create_backup(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00'])
        for d in ret:
            self.check_backup_dir(d)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(self.bm.list_dest_backups(), [])

    def tearDown(self):
        # Remove any directories that were created
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.restore_datetime()

# Destination directory exists and has only backups in it
class PopulatedDestDirBackupsOnlyTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.args['num_backups'] = 5
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

        # Create a few backups
        self.nb = 3
        for i in range(self.nb):
            self.bm.create_backup()

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:02')

    def test_create_backup(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',
            ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def tearDown(self):
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.restore_datetime()

# Destination directory exists and there are backups and other stuff in there
class PopulatedDestDirMixedTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.args['num_backups'] = 5
        self.args['prefix'] = 'test-'
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

        # Create a few backups
        self.nb = 3
        for i in range(self.nb):
            self.bm.create_backup()

        # Create a few random files in the destination directory
        # One with prefix in common
        self.nf = 1
        with open(os.path.join(self.args['dest'], self.args['prefix']), 'w+b') as f:
            f.write(bytes([random.randrange(256) for x in range(4096)]))

        # A few random ones
        self.nf += 3
        for i in range(3):
            with open(os.path.join(self.args['dest'], 'random_{}'.format(i)), 'w+b') as f:
                f.write(bytes([random.randrange(256) for x in range(4096)]))

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        # Non-backup files shouldn't be present here.
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['test-01-01-2015-12:00:00', 'test-01-01-2015-12:00:01',
            'test-01-01-2015-12:00:02', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                'test-01-01-2015-12:00:02')

    def test_create_backup(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['test-01-01-2015-12:00:00', 'test-01-01-2015-12:00:01',
            'test-01-01-2015-12:00:02', 'test-01-01-2015-12:00:03',
            ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['test-01-01-2015-12:00:00', 'test-01-01-2015-12:00:01',
            'test-01-01-2015-12:00:02', ]
        )
        for d in ret:
            self.check_backup_dir(d)
        # Make sure any non-backup files are intact
        all_files = os.listdir(self.args['dest'])
        non_backup = [x for x in all_files if x not in ret]
        for f in non_backup:
            self.assertTrue(os.access(os.path.join(self.args['dest'], f), os.F_OK))

    def tearDown(self):
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.restore_datetime()

# Destination directory exists, duplicate backup testing
class PopulatedDestDirDuplicateBackupTestCase(BackupManagerTestCase):
    def setUp(self):
        # Use a datetime object that doesn't advance
        self.replace_datetime(dl=0)
        self.create_def_args()
        self.args['num_backups'] = 5
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

        # Create a backup
        self.nb = 1
        self.bm.create_backup()

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        # Non-backup files shouldn't be present here.
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00',])
        for d in ret:
            self.check_backup_dir(d)

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:00')

    def test_create_backup(self):
        self.assertRaises(BackupError, self.bm.create_backup)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00',])
        for d in ret:
            self.check_backup_dir(d)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00',])
        for d in ret:
            self.check_backup_dir(d)

    def tearDown(self):
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.restore_datetime()

# Destination directory exists and contains the maximum number of backups
class PopulatedDestDirMaxBackupsTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.args['num_backups'] = 3
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

        # Create the maximum number of backups
        self.nb = self.args['num_backups']
        for i in range(self.nb):
            self.bm.create_backup()

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:02')

    def test_create_backup(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',
            ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def tearDown(self):
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.restore_datetime()

# Destination directory exists and contains the maximum number of backups, plus
# one new one to test that it is removed correctly
class PopulatedDestDirNewBackupTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.args['num_backups'] = 3
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

        # Create the maximum number of backups
        self.nb = self.args['num_backups'] + 1
        for i in range(self.nb):
            self.bm.create_backup()

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',
            ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:03')

    def test_create_backup(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',
            '01-01-2015-12:00:04', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(),
            self.nb - self.args['num_backups'])
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:01', '01-01-2015-12:00:02',
            '01-01-2015-12:00:03', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def tearDown(self):
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.restore_datetime()

# Destination directory exists and contains double the maximum number of
# backups to test that all the old ones are removed
class PopulatedDestDirDoubleMaxTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.args['num_backups'] = 3
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

        # Create the maximum number of backups
        self.nb = self.args['num_backups'] + 3
        for i in range(self.nb):
            self.bm.create_backup()

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',
            '01-01-2015-12:00:04', '01-01-2015-12:00:05',
            ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:05')

    def test_create_backup(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',
            '01-01-2015-12:00:04', '01-01-2015-12:00:05',
            '01-01-2015-12:00:06', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(),
            self.nb - self.args['num_backups'])
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:03', '01-01-2015-12:00:04',
            '01-01-2015-12:00:05', ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def tearDown(self):
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.restore_datetime()

################################################################################
################################################################################
## Exclude Tests                                                              ##
## Tests realted to using the exclude file and/or logging.                    ##
##                                                                            ##
################################################################################
################################################################################

class ExcludeFileTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.args['num_backups'] = 3
        self.args['exclude'] = os.path.join(os.getcwd(), 'test_exclude')
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

        # Setup exclude file
        with open(self.args['exclude'], 'w') as f:
            f.write('rand_file_3\n')
            f.write('rand_file_4\n')

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        self.assertEqual(self.bm.list_dest_backups(), [])

    def test_most_recent_backup(self):
        self.assertIsNone(self.bm.most_recent_backup([]))

    def test_create_backup(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00'])
        files = sorted(os.listdir(os.path.join(self.args['dest'], ret[0], 'test_src')))
        self.assertEqual(files, ['rand_file_0', 'rand_file_1', 'rand_file_2',])

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(self.bm.list_dest_backups(), [])

    def tearDown(self):
        # Remove any directories that were created
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Remove exclude file
        os.remove(self.args['exclude'])
        # Restore mocked stuff
        self.restore_datetime()

# FIXME: Add this feature!
@unittest.skip('Not supported yet')
class ExcludeFileLoggingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.args['num_backups'] = 3
        self.args['exclude'] = os.path.join(os.getcwd(), 'test_exclude')
        self.args['log_excludes'] = True
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

        # Setup exclude file
        with open(self.args['exclude'], 'w') as f:
            f.write('rand_file_3\n')
            f.write('rand_file_4\n')

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        self.assertEqual(self.bm.list_dest_backups(), [])

    def test_most_recent_backup(self):
        self.assertIsNone(self.bm.most_recent_backup([]))

    def test_create_backup(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, [''])
        backup = os.path.join(self.args['dest'], ret[0])
        files = sorted(os.listdir(os.path.join(backup, 'test_src')))
        self.assertEqual(files, ['rand_file_0', 'rand_file_1', 'rand_file_2',])
        files = os.listdir(backup)
        self.assertIn('01-01-2015-12:00:00.excluded', files)
        # Check content of excluded file to make sure it listed everything

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(self.bm.list_dest_backups(), [])

    def tearDown(self):
        # Remove any directories that were created
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Remove exclude file
        os.remove(self.args['exclude'])
        # Restore mocked stuff
        self.restore_datetime()

class ExcludeFileDoesntExistTestCase(BackupManagerTestCase):
    def setUp(self):
        self.replace_datetime()
        self.create_def_args()
        self.args['num_backups'] = 3
        self.args['exclude'] = os.path.join(os.getcwd(), 'test_exclude')
        self.bm = backup_manager(**self.args)

        # Setup source directory
        self.create_test_src_dir()

        # Setup destination directory
        os.mkdir(self.args['dest'])

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_list_backups(self):
        self.assertEqual(self.bm.list_dest_backups(), [])

    def test_most_recent_backup(self):
        self.assertIsNone(self.bm.most_recent_backup([]))

    def test_create_backup(self):
        self.assertRaises(RsyncError, self.bm.create_backup)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, [])

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(self.bm.list_dest_backups(), [])

    def tearDown(self):
        # Remove any directories that were created
        self.cleanup_test_src_dir()
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.restore_datetime()
