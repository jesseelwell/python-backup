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

## \package backup.BackupManager
#
# A module that provides the `backup_manager` class to create and remove backups

from backup.BackupPrinter import backup_printer
from backup.BackupExceptions import *

import os
import re
import subprocess

from datetime import datetime

## \class backup.BackupManager.backup_manager
#  A class to create and remove backups
#
# A class to effeciently create and manage remote backups using `rsync` and
# `ssh`. This includes creating new backups named using a prefix and timestamp
# and removing old backups.
class backup_manager:

    ## Creates a `backup_manager` object to use to create and remove backups.
    #
    #  For more information about one of the parameters refer to the
    #  corrensponding member variable's documentation.
    #  \param src Source directory to back up
    #  \param host Destination (remote) host
    #  \param dest Destination directory (on `host`)
    #  \param user Username to use to connect to `host`
    #  \param num_backups Number of backups to keep
    #  \param rsync_bin Path to `rsync` binary to use
    #  \param rsync_flags Flags to use with rsync
    #  \param exclude Exclude file for `rsync`
    #  \param ssh_bin Path to `ssh` binary to use
    #  \param ssh_key Path to ssh identity to use
    #  \param prefix Backup prefix
    #  \param dry_run Execute dry run(s)
    #  \param log_excludes Log excluded files with backup
    #  \param printer An existing `backup_printer` object to use for output
    def __init__(self, src, host, dest, user=None, num_backups=1,
            rsync_bin='rsync', rsync_flags='-az', exclude=None, ssh_bin='ssh',
            ssh_key=None, prefix=None, dry_run=False, log_excludes=False,
            printer=backup_printer()):
        ## `backup_printer` to use for output
        self.printer = printer
        ## source directory
        self.src = src
        ## user on remote host
        self.user = user
        ## remote host
        self.host = host
        ## destination directory on remote host
        self.dest = dest
        ## number of backups to keep
        self.num_backups = num_backups
        ## path to rsync binary
        self.rsync_bin = rsync_bin
        ## rsync flags
        #
        #  Only flags that can be specified as a single group may be specified
        #  here, for example: -a -z -v and -n can be passed as one group: -azvn.
        #  They will be passed to ``rsync`` as a single command-line argument.
        #  (Note -n and -v are handled explicitly and do not need to be
        #  specified)
        self.rsync_flags = rsync_flags
        ## rsync exclude file
        self.exclude = exclude
        ## path to ssh binary
        self.ssh_bin = ssh_bin
        ## path to ssh identity
        self.ssh_key = ssh_key
        ## backup prefix
        self.prefix = prefix
        ## dry run flag
        self.dry_run = dry_run
        ## log excluded files flag
        self.log_excludes = log_excludes
        ## timestamp format string
        self._date_fmt_str = '%m-%d-%Y-%H:%M:%S'
        # Perhaps make this configurable? If they can change this then the regex
        # to list backups also has to change though and that might be a mess

    # Getters / setters --------------------------------------------------------

    ## \name Getters and Setters
    #  Getter and setter functions for all public members. All getters return
    #  the corresponding member and all setters take a single argument and
    #  assign it to the corresponding member.
    ##@{

    ## Get `printer`
    @property
    def printer(self):
        return self._out
    ## Set `printer`
    @printer.setter
    def printer(self, p):
        self._out = p

    ## Get `src`
    @property
    def src(self):
        return self._src
    ## Set `src`
    @src.setter
    def src(self, s):
        self._src = s

    ## Get `user`
    @property
    def user(self):
        return self._user
    ## Set `user`
    @user.setter
    def user(self, v):
        self._user = v

    ## Set `host`
    @property
    def host(self):
        return self._host
    ## Get `host`
    @host.setter
    def host(self, v):
        self._host = v

    ## Set `dest`
    @property
    def dest(self):
        return self._dest
    ## Get `dest`
    @dest.setter
    def dest(self, v):
        self._dest = v

    ## Get `num_backups`
    @property
    def num_backups(self):
        return self._backups
    ## Set `num_backups`
    @num_backups.setter
    def num_backups(self, v):
        i = int(v)
        if i < 1:
            self._out.warn('Number of backups must be >= 1, {} specified, using'
            ' 1 instead\n'.format(v))
            ## numer of backups to keep
            self._backups = 1
            return
        self._backups = i

    ## Get `rsync_bin`
    @property
    def rsync_bin(self):
        return self._rsync_bin
    ## Set `rsync_bin`
    @rsync_bin.setter
    def rsync_bin(self, v):
        self._rsync_bin = v

    ## Get `rsync_flags`
    @property
    def rsync_flags(self):
        return self._rsync_flags
    ## Set `rsync_flags`
    @rsync_flags.setter
    def rsync_flags(self, v):
        ## rsync flags
        self._rsync_flags = v

    ## Get `exclude`
    @property
    def exclude(self):
        return self._exclude
    ## Set `exclude`
    @exclude.setter
    def exclude(self, v):
        self._exclude = v

    ## Get `ssh_bin`
    @property
    def ssh_bin(self):
        return self._ssh_bin
    ## Set `ssh_bin`
    @ssh_bin.setter
    def ssh_bin(self, v):
        self._ssh_bin = v

    ## Get `ssh_key`
    @property
    def ssh_key(self):
        return self._ssh_key
    ## Set `ssh_key`
    @ssh_key.setter
    def ssh_key(self, v):
        self._ssh_key = v

    ## Get `prefix`
    @property
    def prefix(self):
        return self._prefix
    ## Set `prefix`
    @prefix.setter
    def prefix(self, v):
        if v is None:
            self._prefix = ''
            return
        self._prefix = v

    ## Get `dry_run`
    @property
    def dry_run(self):
        return self._dry_run
    ## Set `dry_run`
    @dry_run.setter
    def dry_run(self, v):
        self._dry_run = v

    ## Get `log_excludes`
    @property
    def log_excludes(self):
        return self._log_excludes
    ## Set `log_excludes`
    @log_excludes.setter
    def log_excludes(self, v):
        self._log_excludes = v
    ##@}

    ## Runs a single command.
    #  \param cmd List of command-line elements to pass to Popen
    #  \returns command's exit status
    #  \returns command's stdout
    #  \returns command's stderr
    #
    # Runs a single command displaying it and its return code, stdout and stderr
    # on the debugging stream.
    def _run_cmd(self, cmd):
        self._out.debug('CMD : {0}\n'.format(' '.join(cmd)))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = proc.communicate()
        self._out.debug('EXIT: {0}\n'.format(proc.returncode))
        self._out.debug('OUT : {0}\n'.format(o.decode().rstrip()))
        self._out.debug('ERR : {0}\n'.format(e.decode().rstrip()))
        return proc.returncode, o.decode(), e.decode()


    ## Generate a backup name using prefix and a timestamp
    #  \returns Backup name (string)
    #
    # This function is used to generate backup names and is directly tied to the
    # `_sort_backup_names()` function. If one changes, the other must change
    # such that `_sort_backup_names()` sorts a list of backup names generated
    # by this function into chronological order (oldest first).
    # (This can be done easily by using the same API to generate and sort the
    # dates)
    def _generate_backup_name(self):
        timestamp = datetime.now().strftime(self._date_fmt_str)
        return '{0}{1}'.format(self._prefix, timestamp)

    ## Sort a list of backup names into chronological order (oldest first)
    #  \param backups List of backup names to sort
    #  \returns `backups` parameter sorted into chronological order
    #
    # This function is used to sort backup names and is directly tied to the
    # `_generate_backup_name()` function. If one changes, the other must change
    # such that this function sorts a list of backup names generated
    # by `_generate_backup_name()` into chronological order (oldest first).
    def _sort_backup_names(self, backups):
        ts = lambda s: datetime.strptime(s, self._date_fmt_str)
        backups.sort(key=lambda x: ts(x.lstrip(self._prefix)))
        return backups

    ## Builds base ssh command
    #  \returns List containing base ssh command
    #
    # Builds the base of an ssh command into a list using the ssh_bin, ssh_key,
    # user, and host members. This list is designed to be extended with the
    # specifics of an ssh command execution and passed to `_run_cmd()`
    def _ssh_cmd(self):
        r = [self._ssh_bin]
        if self._ssh_key is not None:
            r.extend(['-i', self._ssh_key])
        if self._user is not None:
            r.append('{}@{}'.format(self._user, self._host))
        else:
            r.append(self._host)
        return r

    ## Builds base rsync command
    #  \returns List containing base rsync command
    #
    # Builds the base of an rsync command into a list using the rsync_bin,
    # rsync_flags, dry_run, and ssh_key members. This list is designed to be
    # extended with the specifics of an rsync command exection and passed to
    # `_run_cmd()`
    def _rsync_cmd(self):
        r = [self._rsync_bin, '-v', self._rsync_flags]
        if self._dry_run:
            r.append('-n')
        if self._ssh_key is not None:
            r.extend(['-e', '{} -i {}'.format(self._ssh_bin, self._ssh_key)])
        return r

    ## Test connection to host
    #  \returns True if the test command is successful, False otherwise
    #
    # Performs a test ssh command to make sure we can reach host
    def check_host(self):
        res, _, _ = self._run_cmd(self._ssh_cmd() + ['exit 0'])
        return (res == 0)

    ## Check if the destination directory exists
    #
    # Check to see if the destination directory exists on the remote machine. If
    # the destination directory doesn't exist, create it (unless this is a dry
    # run) and then either way make sure we can write there
    def check_dest(self):
        # Existence
        o = 'Destination directory: {0} does not exist {1}\n'
        res, _ , _ = self._run_cmd(self._ssh_cmd() + ['test -d {}'.format(self._dest)])
        if res != 0:
            if self._dry_run:
                self._out.info(o.format(self._dest, '(DRY-RUN)'))
                return
            self._out.info(o.format(self._dest, 'attempting to create'))
            res, _ , e = self._run_cmd(self._ssh_cmd() + ['mkdir', '-p', self._dest])
            if res != 0:
                raise DestDirError('Cannot create destination directory: {}'.format(e))
            self._out.info('Destination directory created successfully\n')
        # Writability
        res, _, _ = self._run_cmd(self._ssh_cmd() + ['test -w {}'.format(self._dest)])
        if res != 0:
            raise DestDirError('Destination directory is not writable')
        return

    ## List backups in destination directory
    #  \returns List of backups in the destination directory (sorted)
    #
    # Lists the files in the destination directory and then passes them through
    # a regex to isolate only backups, then sorts that list.
    def list_dest_backups(self):
        res, o, e = self._run_cmd(self._ssh_cmd() + ['ls {0}'.format(self._dest)])
        if res != 0:
            raise DestDirError("'{}' does not exist".format(self._dest))
        regex = self._prefix + '\d{2}-\d{2}-\d{4}-\d{2}:\d{2}:\d{2}'
        e = re.compile(regex)
        backups = [f for f in o.split() if e.search(f)]
        return self._sort_backup_names(backups)

    ## Find the most recent backup in the list of backups
    #  \returns The name of the most recent backup (string)
    #
    # Finds the most recent backup in the list `backups`. Assumes that the list
    # of backups is already sorted since that's how `list_dest_backups()`
    # returns it.
    def most_recent_backup(self, backups):
        if len(backups) == 0:
            return None
        else:
            return backups[-1]

    ## Create a new backup
    #
    #  Create a new backup based on the values of all of the attributes. This
    #  includes generating a backup name, ensuring that the backup doesn't
    #  aleady exist, and then setting up and executing the actual rsync command
    #  to create the backup.
    def create_backup(self):
        # Get a name for the backup
        name = self._generate_backup_name()
        self._out.info('Attempting to creating backup: {0}\n'.format(name))

        # Check to make sure the backup doesn't already exist
        backups = self.list_dest_backups()
        if name in backups:
            raise BackupError('Backup: {0} already exists'.format(name))

        # Build the rsync command for the backup
        rsync_backup = self._rsync_cmd()

        # Exclude
        if self._exclude is not None:
            rsync_backup.append('--exclude-from={0}'.format(self._exclude))

        # Link-dest (feed in list of backups from above to avoid extra ssh)
        link = self.most_recent_backup(backups)
        if link is not None:
            lp = os.path.join(self._dest, link)
            self._out.info('Most recent backup (link-dest): {0}\n'.format(lp))
            rsync_backup.append('--link-dest={0}'.format(lp))
        else:
            self._out.info('No backups were found, creating initial backup\n')

        # Source and destination
        rsync_backup.append(self._src)
        if self._user is not None:
            rsync_backup.append('{0}@{1}:{2}'.format(self._user, self._host,
                os.path.join(self._dest, name)))
        else:
            rsync_backup.append('{0}:{1}'.format(self._host,
                os.path.join(self._dest, name)))

        # Execute the rsync command
        res, o, e = self._run_cmd(rsync_backup)
        if res != 0:
            raise RsyncError(e)
        else:
            if not self._dry_run:
                self._out.info('Backup: {} created successfully\n'.format(name))

    ## Removes old backups
    #  \returns The number of backups removed
    #
    # Removes the oldest backups if the number of exisiting backups is greater
    # than the number specified to keep
    # FIXME: Return the actual list of backups removed successfully and remove
    # output from here.
    def remove_backups(self):
        self._out.info('Attempting to remove old backups\n')
        backups = self.list_dest_backups()
        if len(backups) <= self._backups:
            self._out.info('{0}/{1} backups exist, no removal necessary.\n'.format(
                len(backups), self._backups))
            return 0
        backups.reverse()
        to_remove = backups[self._backups:]
        if self._dry_run:
            self._out.info('Would have removed backup(s): {0} '
                '(DRY-RUN)\n'.format(' '.join(to_remove)))
            return 0
        self._out.info('Removing backup(s): {0}\n'.format(' '.join(to_remove)))
        res, _, e = self._run_cmd(self._ssh_cmd() +
                ['rm -r {0}'.format(
                    ' '.join([os.path.join(self._dest,x) for x in to_remove])
                    )
                ]
            )
        if res != 0:
            self._out.error('Unable to remove backup(s): {0}\n'.format(e))
        self._out.info('Successfully removed {0} backup(s)\n'.format(len(to_remove)))
        return len(to_remove)
