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
## Common Setup Functions                                                     ##
## Setup that is common to more than one test case should be put into         ##
## functions in this section to be used in those test cases.                  ##
##                                                                            ##
################################################################################
################################################################################
def create_test_backup_dir(bck_man):
    d = bck_man.src
    os.mkdir(d)
    # Write a few random files of data into there
    for i in range(5):
        with open(os.path.join(d, 'rand_file_{}'.format(i)), 'w+b') as f:
            by = [random.randrange(256) for j in range(4096)]
            f.write(bytes(by))

################################################################################
################################################################################
## Command Building Tests                                                     ##
## Tests to ensure that the base ssh and rsync commands are built correctly   ##
## under various circumstances.                                               ##
##                                                                            ##
################################################################################
################################################################################

class MinimalBackupManagerCommandBuildingTestCase(unittest.TestCase):
    def setUp(self):
        # Create a minimal backup_manager object to work with
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
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

class BackupManagerUserCommandBuildingTestCase(unittest.TestCase):
    def setUp(self):
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'user':'user',
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
            }
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

class BackupManagerSSHKeyCommandBuildingTestCase(unittest.TestCase):
    def setUp(self):
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'ssh_key':'~/.ssh/id_rsa',
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
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

class BackupManagerUserSSHKeyCommandBuildingTestCase(unittest.TestCase):
    def setUp(self):
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'user':'user',
            'ssh_key':'~/.ssh/id_rsa',
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
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

class BackupManagerRsyncBinCommandBuildingTestCase(unittest.TestCase):
    def setUp(self):
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'rsync_bin': 'RSYNC_BIN',
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
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

class BackupManagerSSHBinKeyCommandBuildingTestCase(unittest.TestCase):
    def setUp(self):
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'ssh_bin': 'SSH_BIN',
            'ssh_key': '~/.ssh/id_rsa',
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
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

class NonExistentSourceDirTestCase(unittest.TestCase):
    def setUp(self):
        # Create a minimal backup_manager object to work with
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Make sure source directory doesn't exist
        if os.access(self.args['src'], os.F_OK):
            shutil.rmtree(self.args['src'])

        # The destination directory should exist to avoid any errors from that
        if not os.access(self.args['dest'], os.W_OK):
            if os.access(self.args['dest'], os.F_OK):
                shutil.rmtree(self.args['dest'])
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

class NonExistentDestinationDirTestCase(unittest.TestCase):
    def setUp(self):
        # Create a minimal backup_manager object to work with
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory, removing it if it already exists
        os.mkdir(self.args['src'])

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
        shutil.rmtree(self.args['src'])
        if os.access(self.args['dest'], os.F_OK):
            shutil.rmtree(self.args['dest'])

class BadDestinationDirTestCase(unittest.TestCase):
    def setUp(self):
        # Create a minimal backup_manager object to work with
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory
        os.mkdir(self.args['src'])

    def test_check_host(self):
        self.assertTrue(self.bm.check_host())

    def test_check_dest(self):
        self.bm.check_dest()
        self.assertTrue(os.access(self.args['dest'], os.W_OK))

    def test_cannot_create_dest(self):
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
        shutil.rmtree(self.args['src'])
        if os.access(self.args['dest'], os.F_OK):
            if not os.access(self.args['dest'], os.W_OK):
                os.chmod(self.args['dest'], 777)
            shutil.rmtree(self.args['dest'])

# Destination directory exists but is empty
class EmptyDestinationDirTestCase(unittest.TestCase):
    def setUp(self):
        self.r = Replacer()
        self.r.replace('backup.BackupManager.datetime',
            test_datetime(2015, 1, 1, 12, 0, 0, delta=1))
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory
        os.mkdir(self.args['src'])

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
        self.assertEqual(self.bm.list_dest_backups(), ['01-01-2015-12:00:00'])

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(self.bm.list_dest_backups(), [])

    def tearDown(self):
        # Remove any directories that were created
        shutil.rmtree(self.args['src'])
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.r.restore()

# Destination directory exists and has only backups in it
class PopulatedDestinationDirBackupsOnlyTestCase(unittest.TestCase):
    def setUp(self):
        self.r = Replacer()
        self.r.replace('backup.BackupManager.datetime',
            test_datetime(2015, 1, 1, 12, 0, 0, delta=1))
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'num_backups':5,
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory
        create_test_backup_dir(self.bm)

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
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            ]
        )

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:02')

    def test_create_backup(self):
        self.bm.create_backup()
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            '01-01-2015-12:00:03',
            ]
        )

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            ]
        )

    def tearDown(self):
        shutil.rmtree(self.args['src'])
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.r.restore()

# Destination directory exists and there are backups and other stuff in there
class PopulatedDestinationDirMixedTestCase(unittest.TestCase):
    def setUp(self):
        self.r = Replacer()
        self.r.replace('backup.BackupManager.datetime',
            test_datetime(2015, 1, 1, 12, 0, 0, delta=1))
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'num_backups':5,
            'prefix':'test-',
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory
        create_test_backup_dir(self.bm)

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
        self.assertEqual(self.bm.list_dest_backups(),
            ['test-01-01-2015-12:00:00',
            'test-01-01-2015-12:00:01',
            'test-01-01-2015-12:00:02',
            ]
        )

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                'test-01-01-2015-12:00:02')

    def test_create_backup(self):
        self.bm.create_backup()
        self.assertEqual(self.bm.list_dest_backups(),
            ['test-01-01-2015-12:00:00',
            'test-01-01-2015-12:00:01',
            'test-01-01-2015-12:00:02',
            'test-01-01-2015-12:00:03',
            ]
        )

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        bcks = self.bm.list_dest_backups()
        self.assertEqual(bcks,
            ['test-01-01-2015-12:00:00',
            'test-01-01-2015-12:00:01',
            'test-01-01-2015-12:00:02',
            ]
        )
        a = os.listdir(self.args['dest'])
        other = [x for x in a
                if x not in bcks]
        for o in other:
            self.assertTrue(os.access(os.path.join(self.args['dest'], o), os.F_OK))

    def tearDown(self):
        shutil.rmtree(self.args['src'])
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.r.restore()

# Destination directory exists, duplicate backup testing
class PopulatedDestinationDirDuplicateTestCase(unittest.TestCase):
    def setUp(self):
        self.r = Replacer()
        # Use a datetime object that doesn't advance
        self.r.replace('backup.BackupManager.datetime',
            test_datetime(2015, 1, 1, 12, 0, 0, delta=0))
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'num_backups':5,
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory
        create_test_backup_dir(self.bm)

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
        self.assertEqual(self.bm.list_dest_backups(), ['01-01-2015-12:00:00',])

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:00')

    def test_create_backup(self):
        self.assertRaises(BackupError, self.bm.create_backup)
        self.assertEqual(self.bm.list_dest_backups(), ['01-01-2015-12:00:00',])

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(self.bm.list_dest_backups(), ['01-01-2015-12:00:00',])

    def tearDown(self):
        shutil.rmtree(self.args['src'])
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.r.restore()

# Destination directory exists and contains the maximum number of backups
class PopulatedDestinationDirMaxBackupsTestCase(unittest.TestCase):
    def setUp(self):
        self.r = Replacer()
        self.r.replace('backup.BackupManager.datetime',
            test_datetime(2015, 1, 1, 12, 0, 0, delta=1))
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'num_backups':3,
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory
        create_test_backup_dir(self.bm)

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
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            ]
        )

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:02')

    def test_create_backup(self):
        self.bm.create_backup()
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            '01-01-2015-12:00:03',
            ]
        )

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            ]
        )

    def tearDown(self):
        shutil.rmtree(self.args['src'])
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.r.restore()

# Destination directory exists and contains the maximum number of backups, plus
# one new one to test that it is removed correctly
class PopulatedDestinationDirNewBackupTestCase(unittest.TestCase):
    def setUp(self):
        self.r = Replacer()
        self.r.replace('backup.BackupManager.datetime',
            test_datetime(2015, 1, 1, 12, 0, 0, delta=1))
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'num_backups':3,
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory
        create_test_backup_dir(self.bm)

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
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            '01-01-2015-12:00:03',
            ]
        )

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:03')

    def test_create_backup(self):
        self.bm.create_backup()
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            '01-01-2015-12:00:03',
            '01-01-2015-12:00:04',
            ]
        )

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(),
            self.nb - self.args['num_backups'])
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            '01-01-2015-12:00:03',
            ]
        )

    def tearDown(self):
        shutil.rmtree(self.args['src'])
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.r.restore()

# Destination directory exists and contains double the maximum number of
# backups to test that all the old ones are removed
class PopulatedDestinationDirDoubleMaxTestCase(unittest.TestCase):
    def setUp(self):
        self.r = Replacer()
        self.r.replace('backup.BackupManager.datetime',
            test_datetime(2015, 1, 1, 12, 0, 0, delta=1))
        self.args = {
            'host':'localhost',
            'src':os.path.join(os.getcwd(), 'test_src'),
            'dest':os.path.join(os.getcwd(), 'test_dest'),
            'num_backups':3,
            'printer':backup_printer(),
            # To debug tests, this will print all commands etc to stdout
            #'printer':backup_printer(sys.stdout, sys.stdout, sys.stdout,
            #    sys.stdout, sys.stdout),
        }
        self.bm = backup_manager(**self.args)

        # Setup source directory
        create_test_backup_dir(self.bm)

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
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            '01-01-2015-12:00:03',
            '01-01-2015-12:00:04',
            '01-01-2015-12:00:05',
            ]
        )

    def test_most_recent_backup(self):
        # Three backups were made above 12:00:0{0,1,2}, so 12:00:02 should be
        # the most recent
        self.assertEqual(self.bm.most_recent_backup(self.bm.list_dest_backups()),
                '01-01-2015-12:00:05')

    def test_create_backup(self):
        self.bm.create_backup()
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:00',
            '01-01-2015-12:00:01',
            '01-01-2015-12:00:02',
            '01-01-2015-12:00:03',
            '01-01-2015-12:00:04',
            '01-01-2015-12:00:05',
            '01-01-2015-12:00:06',
            ]
        )

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(),
            self.nb - self.args['num_backups'])
        self.assertEqual(self.bm.list_dest_backups(),
            ['01-01-2015-12:00:03',
            '01-01-2015-12:00:04',
            '01-01-2015-12:00:05',
            ]
        )

    def tearDown(self):
        shutil.rmtree(self.args['src'])
        shutil.rmtree(self.args['dest'])
        # Restore mocked stuff
        self.r.restore()
