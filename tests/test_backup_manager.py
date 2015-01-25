#!../venv/bin/python3

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
    def create_def_backup_obj(self):
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'num_backups':2,
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

    # Create random/named files
    def create_random_files(self, dest, num=5):
        for i in range(num):
            with open(os.path.join(dest, 'rand_{}'.format(i)), 'w+b') as f:
                f.write(bytes([random.randrange(256) for j in range(4096)]))
    def create_named_files(self, dest, files):
        for i in files:
            with open(os.path.join(dest, i), 'w+b') as f:
                f.write(bytes([random.randrange(256) for j in range(4096)]))

    # Create/cleanup a source directory with a few random files to test with
    def create_test_src_dir(self, dest=None, rand_files=5):
        if dest is None: dest = self.bm.src
        os.mkdir(dest)
        self.create_random_files(dest, num=rand_files)
    def cleanup_test_src_dir(self):
        if os.access(self.bm.src, os.F_OK):
            shutil.rmtree(self.bm.src)

    # Create/cleanup a destination directory, possibly with some junk in there
    # to start with
    def create_test_dest_dir(self, dest=None, named_files=[], rand_files=0):
        if dest is None: dest = self.bm.dest
        os.mkdir(dest)
        self.create_random_files(dest, rand_files)
        self.create_named_files(dest, named_files)
    def cleanup_test_dest_dir(self):
        if os.access(self.bm.dest, os.F_OK):
            if not os.access(self.bm.dest, os.W_OK):
                os.chmod(self.bm.dest, 777)
            shutil.rmtree(self.bm.dest)

    # Check a specific backup dir
    def check_backup_dir(self, backup_dir):
        backup_dir = os.path.join(self.bm.dest, backup_dir)
        ret = os.listdir(backup_dir)
        self.assertIn(os.path.basename(self.bm.src), ret)
        ret = sorted(os.listdir(os.path.join(backup_dir, self.bm.src)))
        self.assertEqual(ret,
            ['rand_0','rand_1','rand_2','rand_3','rand_4',]
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
class MinCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], self.bm.host)

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')

class UserCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.bm.user = 'user'

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1],
            '{}@{}'.format(self.bm.user, self.bm.host))

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')

class SSHKeyCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.bm.ssh_key = '~/.ssh/id_rsa'

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], '-i')
        self.assertEqual(r[2], self.bm.ssh_key)
        self.assertEqual(r[3], self.bm.host)

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')
        self.assertEqual(r[3], '-e')
        self.assertEqual(r[4], 'ssh -i {}'.format(self.bm.ssh_key))

class UserSSHKeyCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.bm.user = 'user',
        self.bm.ssh_key = '~/.ssh/id_rsa'

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], '-i')
        self.assertEqual(r[2], self.bm.ssh_key)
        self.assertEqual(r[3],
            '{}@{}'.format(self.bm.user, self.bm.host))

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')
        self.assertEqual(r[3], '-e')
        self.assertEqual(r[4], 'ssh -i {}'.format(self.bm.ssh_key))

class RsyncBinCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.create_test_dest_dir()
        self.bm.rsync_bin = 'RSYNC_BIN'

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], self.bm.host)

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'RSYNC_BIN')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')

    def test_create_backup(self):
        self.assertRaises(FileNotFoundError, self.bm.create_backup)

    def tearDown(self):
        self.cleanup_test_dest_dir()

class SSHBinKeyCmdBldingTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.bm.ssh_bin = 'SSH_BIN'
        self.bm.ssh_key = 'SSH_KEY'

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'SSH_BIN')
        self.assertEqual(r[1], '-i')
        self.assertEqual(r[2], self.bm.ssh_key)
        self.assertEqual(r[3], self.bm.host)

    def test_rsync_cmd(self):
        r = self.bm._rsync_cmd()
        self.assertEqual(r[0], 'rsync')
        self.assertEqual(r[1], '-v')
        self.assertEqual(r[2], '-az')
        self.assertEqual(r[3], '-e')
        self.assertEqual(r[4], 'SSH_BIN -i {}'.format(self.bm.ssh_key))

    def test_check_host(self):
        self.assertRaises(FileNotFoundError, self.bm.check_host)

################################################################################
################################################################################
## Check Host Tests                                                           ##
## Tests related to the check_host() function.                                ##
##                                                                            ##
################################################################################
################################################################################
class CheckHostReachableTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

class CheckHostUnreachableTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.bm = backup_manager(**self.args)

    def test_check_host(self):
        with patch.object(self.bm, '_run_cmd', return_value=(1, '', '')) as mm:
            self.assertFalse(self.bm.check_host())

################################################################################
################################################################################
## Check Dest Tests                                                           ##
## Tests related to the check_dest() function.                                ##
##                                                                            ##
################################################################################
################################################################################

class CheckDestTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.create_test_src_dir()

# Destination exists -----
    def test_dest_exists_writable(self):
        self.create_test_dest_dir()
        self.assertEqual(self.bm.check_dest(), (True, True))
        self.assertTrue(os.access(self.bm.dest, os.W_OK))

    def test_dest_exists_not_writable(self):
        os.mkdir(self.bm.dest, 555)
        self.assertEqual(self.bm.check_dest(), (True, False))
        self.assertFalse(os.access(self.bm.dest, os.W_OK))

# Destination does not exist -----
    def test_dest_doesnt_exist(self):
        self.assertEqual(self.bm.check_dest(), (False, False))
        self.assertFalse(os.access(self.bm.dest, os.F_OK))

    def tearDown(self):
        self.cleanup_test_src_dir()
        self.cleanup_test_dest_dir()

################################################################################
################################################################################
## Create Dest Tests                                                          ##
## Tests related to the create_dest() function.                               ##
##                                                                            ##
################################################################################
################################################################################
# FIXME: Not implemented yet!
@unittest.skip('Not implemented yet!')
class CreateDestTestCase(BackupManagerTestCase):
    def setUp(self):
        pass

    def test_dest_doesnt_exist_create_ok(self):
        self.bm.create_dest()
        self.assertTrue(os.access(self.bm.dest, os.W_OK))

    def test_dest_doesnt_exist_create_fail(self):
        with patch.object(self.bm, '_run_cmd', return_value=(1, '', '')) as mm:
            self.assertRaises(DestDirError, self.bm.create_dest)
            self.assertFalse(os.access(self.bm.dest, os.F_OK))

    def tearDown(self):
        pass

################################################################################
################################################################################
## List Backups Tests                                                         ##
## Tests related to the list_dest_backups() function.                         ##
##                                                                            ##
################################################################################
################################################################################
class ListDestBackupsTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.replace_datetime()
        self.create_test_src_dir()
        self.create_test_dest_dir()

    def test_dest_dir_nonexistent(self):
        self.cleanup_test_dest_dir()
        self.assertRaises(DestDirError, self.bm.list_dest_backups)

    def test_dest_dir_empty(self):
        self.assertEqual(self.bm.list_dest_backups(), [])

    def test_dest_dir_backups_only(self):
        for i in range(self.bm.num_backups):
            self.bm.create_backup()
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01'])

    def test_dest_dir_mixed_content(self):
        self.bm.prefix = 'test-'
        for i in range(self.bm.num_backups):
            self.bm.create_backup()
        self.create_named_files(self.bm.dest, [self.bm.prefix])
        self.create_random_files(self.bm.dest, 3)
        self.assertEqual(self.bm.list_dest_backups(),
            ['test-01-01-2015-12:00:00', 'test-01-01-2015-12:00:01',])

    def tearDown(self):
        self.cleanup_test_dest_dir()
        self.cleanup_test_src_dir()
        self.restore_datetime()

################################################################################
################################################################################
## Most Recent Backup Tests                                                   ##
## Tests related to the most_recent_backup() function.                        ##
##                                                                            ##
################################################################################
################################################################################
class MostRecentBackupTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()

    def test_backup_list_empty(self):
        self.assertIsNone(self.bm.most_recent_backup([]))

    def test_backup_list_populated(self):
        self.assertEqual(self.bm.most_recent_backup(
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01'
            '01-01-2015-12:00:02', '01-01-2015-12:00:03']
        ), '01-01-2015-12:00:03')

################################################################################
################################################################################
## Create Backup Tests                                                        ##
## Tests related to the all important create_backup() function. This will     ##
## likely be the meat of the tests.                                           ##
##                                                                            ##
################################################################################
################################################################################
# FIXME: Check a return value, the name of the backup created?
class CreateBackupTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.replace_datetime()
        self.create_test_src_dir()
        self.create_test_dest_dir()

    def test_nonexistent_src_dir(self):
        self.cleanup_test_src_dir()
        self.assertRaises(RsyncError, self.bm.create_backup)

    def test_nonexistent_dest_dir(self):
        self.cleanup_test_dest_dir()
        self.assertRaises(DestDirError, self.bm.create_backup)

    def test_nonexistent_dest_dir_dry_run(self):
        self.cleanup_test_dest_dir()
        self.bm.dry_run = True
        self.assertRaises(DestDirError, self.bm.create_backup)

    def test_dest_dir_not_writable(self):
        self.cleanup_test_dest_dir()
        os.mkdir(self.bm.dest, 555)
        self.assertRaises(DestDirError, self.bm.create_backup)

    def test_empty_dest_dir(self):
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00'])
        for d in ret:
            self.check_backup_dir(d)

    def test_empty_dest_dir_dry_run(self):
        self.bm.dry_run = True
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, [])

    def test_dest_dir_backups_only(self):
        # Populate
        for i in range(self.bm.num_backups):
            self.bm.create_backup()
        # Check
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_dest_dir_backups_only_dry_run(self):
        for i in range(self.bm.num_backups * 2):
            self.bm.create_backup()
        self.bm.dry_run = True
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',
            ]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_dest_dir_mixed_content(self):
        self.bm.prefix = 'test-'
        for i in range(self.bm.num_backups):
            self.bm.create_backup()
        self.create_named_files(self.bm.dest, [self.bm.prefix])
        self.create_random_files(self.bm.dest, 3)
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['test-01-01-2015-12:00:00', 'test-01-01-2015-12:00:01',
            'test-01-01-2015-12:00:02',]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_duplicate_backup(self):
        self.restore_datetime()
        self.replace_datetime(dl=0)
        self.bm.create_backup()
        self.assertRaises(BackupError, self.bm.create_backup)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00',])
        for d in ret:
            self.check_backup_dir(d)

    def test_double_max_backups(self):
        # Create double maximum number of backups
        for i in range(self.bm.num_backups * 2):
            self.bm.create_backup()
        # Make sure we got all of those
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',
            '01-01-2015-12:00:04',]
        )
        for d in ret:
            self.check_backup_dir(d)

    def test_exclude_file(self):
        self.bm.exclude = os.path.join(os.getcwd(), 'test_exclude')
        with open(self.bm.exclude, 'w') as f:
            f.write('rand_3\n')
            f.write('rand_4\n')
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00'])
        files = sorted(os.listdir(os.path.join(self.bm.dest, ret[0], 'test_src')))
        self.assertEqual(files, ['rand_0', 'rand_1', 'rand_2',])
        os.remove(self.bm.exclude)

    # FIXME: Not implemented yet!
    @unittest.skip('Not implemented yet!')
    def test_exclude_logging(self):
        self.bm.exclude = os.path.join(os.getcwd(), 'test_exclude')
        with open(self.bm.exclude, 'w') as f:
            f.write('rand_3\n')
            f.write('rand_4\n')
        self.bm.create_backup()
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, [''])
        backup = os.path.join(self.bm.dest, ret[0])
        files = sorted(os.listdir(os.path.join(backup, 'test_src')))
        self.assertEqual(files, ['rand_0', 'rand_1', 'rand_2',])
        files = os.listdir(backup)
        self.assertIn('01-01-2015-12:00:00.excluded', files)
        # Check content of excluded file to make sure it listed everything
        os.remove(self.bm.exclude)

    def test_exclude_doesnt_exist(self):
        self.bm.exclude = os.path.join(os.getcwd(), 'test_exclude')
        self.assertRaises(RsyncError, self.bm.create_backup)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, [])

    def tearDown(self):
        self.cleanup_test_dest_dir()
        self.cleanup_test_src_dir()
        self.restore_datetime()

################################################################################
################################################################################
## Remove Backups Tests                                                       ##
## Tests related to remove_backups().                                         ##
##                                                                            ##
################################################################################
################################################################################
class RemoveBackupsTestCase(BackupManagerTestCase):
    def setUp(self):
        self.create_def_backup_obj()
        self.replace_datetime()
        self.create_test_src_dir()
        self.create_test_dest_dir()

    def test_nonexistent_dest_dir(self):
        self.cleanup_test_dest_dir()
        self.assertRaises(DestDirError, self.bm.remove_backups)

    def test_dest_dir_not_writable(self):
        self.cleanup_test_dest_dir()
        os.mkdir(self.bm.dest, 555)
        self.assertRaises(DestDirError, self.bm.remove_backups)

    def test_zero_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)

    def test_less_than_max_backups(self):
        self.bm.create_backup()
        self.assertEqual(self.bm.remove_backups(), 0)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00',])
        for d in ret:
            self.check_backup_dir(d)

    def test_equal_max_backups(self):
        for i in range(self.bm.num_backups):
            self.bm.create_backup()
        self.assertEqual(self.bm.remove_backups(), 0)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00','01-01-2015-12:00:01'])
        for d in ret:
            self.check_backup_dir(d)

    def test_greater_max_backups(self):
        for i in range(self.bm.num_backups + 1):
            self.bm.create_backup()
        self.assertEqual(self.bm.remove_backups(), 1)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:01','01-01-2015-12:00:02'])
        for d in ret:
            self.check_backup_dir(d)

    def test_much_greater_max_backups(self):
        bcks = 10
        for i in range(bcks):
            self.bm.create_backup()
        self.assertEqual(self.bm.remove_backups(), bcks - self.bm.num_backups)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:08', '01-01-2015-12:00:09',])
        for d in ret:
            self.check_backup_dir(d)

    def test_dest_dir_mixed_content(self):
        self.bm.prefix = 'test-'
        for i in range(self.bm.num_backups):
            self.bm.create_backup()
        self.create_named_files(self.bm.dest, [self.bm.prefix])
        self.create_random_files(self.bm.dest, 3)
        self.assertEqual(self.bm.remove_backups(), 0)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret,
            ['test-01-01-2015-12:00:00', 'test-01-01-2015-12:00:01',]
        )
        for d in ret:
            self.check_backup_dir(d)
        # Make sure any non-backup files are intact
        all_files = os.listdir(self.bm.dest)
        non_backup = [x for x in all_files if x not in ret]
        for f in non_backup:
            self.assertTrue(os.access(os.path.join(self.bm.dest, f), os.F_OK))

    def test_populated_dry_run(self):
        bcks = 4
        for i in range(bcks):
            self.bm.create_backup()
        self.bm.dry_run = True
        self.assertEqual(self.bm.remove_backups(), 0)
        ret = self.bm.list_dest_backups()
        self.assertEqual(ret, ['01-01-2015-12:00:00', '01-01-2015-12:00:01',
            '01-01-2015-12:00:02', '01-01-2015-12:00:03',])
        for d in ret:
            self.check_backup_dir(d)

    def test_negative_one_num_backups(self):
        self.bm.num_backups = -1
        for i in range(5):
            self.bm.create_backup()
        for i in range(4, -1, -1):
            self.assertEqual(self.bm.remove_backups(), 1)
            self.assertEqual(len(self.bm.list_dest_backups()), i)

    def test_negative_two_num_backups(self):
        self.bm.num_backups = -2
        for i in range(6):
            self.bm.create_backup()
        for i in range(4, -1, -2):
            self.assertEqual(self.bm.remove_backups(), 2)
            self.assertEqual(len(self.bm.list_dest_backups()), i)

    def tearDown(self):
        self.cleanup_test_dest_dir()
        self.cleanup_test_src_dir()
        self.restore_datetime()
