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
import shutil
import sys
import unittest

sys.path.append('../')

from backup.BackupManager import backup_manager
from backup.BackupPrinter import backup_printer
from backup.BackupExceptions import *

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
                'dest':os.path.join(os.getcwd(), 'test_dest')
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

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
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], '{}@{}'.format(self.args['user'], self.args['host']))

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
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

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
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

    def test_ssh_cmd(self):
        r = self.bm._ssh_cmd()
        self.assertEqual(r[0], 'ssh')
        self.assertEqual(r[1], '-i')
        self.assertEqual(r[2], self.args['ssh_key'])
        self.assertEqual(r[3], '{}@{}'.format(self.args['user'], self.args['host']))

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
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

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
                'ssh_key': '~/.ssh/id_rsa'
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

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
                'dest':os.path.join(os.getcwd(), 'test_dest')
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

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
                'dest':os.path.join(os.getcwd(), 'test_dest')
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

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
        r = self.bm.most_recent_backup([])
        self.assertIsNone(r)

    def test_create_backup(self):
        self.assertRaises(DestDirError, self.bm.create_backup)

    def test_remove_backups(self):
        self.assertRaises(DestDirError, self.bm.remove_backups)

    def tearDown(self):
        # Remove any directories that may have been created
        shutil.rmtree(self.args['src'])
        if os.access(self.args['dest'], os.F_OK):
            shutil.rmtree(self.args['dest'])

# Destination directory exists but is empty
class EmptyDestinationDirTestCase(unittest.TestCase):
    def setUp(self):
        self.args = {
                'host':'localhost',
                'src':os.path.join(os.getcwd(), 'test_src'),
                'dest':os.path.join(os.getcwd(), 'test_dest')
            }
        p = backup_printer()
        # To debug tests, this will print all commands etc to stdout
        #p = backup_printer(sys.stdout, sys.stdout, sys.stdout, sys.stdout, sys.stdout)
        self.bm = backup_manager(printer=p,**self.args)

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
        r = self.bm.list_dest_backups()
        self.assertEqual(r, [])

    def test_most_recent_backup(self):
        r = self.bm.most_recent_backup([])
        self.assertIsNone(r)

    def test_create_backup(self):
        self.bm.create_backup()
        self.assertEqual(len(os.listdir(self.args['dest'])), 1)

    def test_remove_backups(self):
        self.assertEqual(self.bm.remove_backups(), 0)
        self.assertEqual(len(os.listdir(self.args['dest'])), 0)

    def tearDown(self):
        # Remove any directories that were created
        shutil.rmtree(self.args['src'])
        shutil.rmtree(self.args['dest'])

# Destination directory exists and has only backups in it
#class PopulatedDestinationDirBackupsOnlyTestCase(unittest.TestCase):

# Destination directory exists and there are backups and other stuff in there
#class PopulatedDestinationDirMixedTestCase(unittest.TestCase):
