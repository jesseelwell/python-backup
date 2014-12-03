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

import datetime
import os
import re
import subprocess

# Simple class to handle output, each output type can be redirected to possibly
# different streams. Streams only need to support a write(str) method. Tested
# using sys.stdout and sys.stderr, but should also support logging by using
# files instead. Eventually this should be removed and replaced with exceptions
class backup_printer:

    # Constructor(s)
    def __init__(self, warn=None, info=None, debug=None, error=None, fatal=None):
        self.__warn = warn
        self.__info = info
        self.__deb = debug
        self.__err = error
        self.__fat = fatal

    def __repr__(self):
        return 'warn={}; info={}; debug={}; error={}; fatal={};'.format(
                self.__warn.name, self.__info.name, self.__deb.name,
                self.__err.name, self.__fat.name)

    def __write(self, msg, s, stream):
        if stream is not None:
            stream.write('{0}{1}'.format(msg, s))

    def warn(self, s):
        self.__write('WARNING: ', s, self.__warn)

    def info(self, s):
        self.__write('INFO: ', s, self.__info)

    def debug(self, s):
        self.__write('DEBUG: ', s, self.__deb)

    def error(self, s):
        self.__write('ERROR: ', s, self.__err)

    def fatal(self, s, exit_code):
        self.__write('FATAL: ', s, self.__fat)
        exit(exit_code)

class backup:

    # Constructor(s)
    def __init__(self, src, host, dest, user = None, num_backups=1,
            rsync_bin='rsync', rsync_flags='-az', exclude=None, ssh_bin='ssh',
            ssh_key=None, prefix=None, dry_run=False, log_excludes=False,
            printer=backup_printer()):
        self.printer = printer
        self.src = src
        self.user = user
        self.host = host
        self.dest = dest
        self.num_backups = num_backups
        self.rsync_bin = rsync_bin
        self.rsync_flags = rsync_flags
        self.exclude = exclude
        self.ssh_bin = ssh_bin
        self.ssh_key = ssh_key
        self.prefix = prefix
        self.dry_run = dry_run
        self.log_excludes = log_excludes
        # Perhaps make this configurable? If they can change this then the regex
        # to list backups also has to change though and that might be a mess
        self.__date_fmt_str = '%m-%d-%Y-%H:%M:%S'

    # Getters / setters
    @property
    def printer(self):
        return self.__out
    @printer.setter
    def printer(self, v):
        self.__out = v

    @property
    def src(self):
        return self.__src
    @src.setter
    def src(self, v):
        if not os.path.exists(v):
            self.__out.warn('Source directory: {0} does not exist\n'.format(v))
        self.__src = v

    @property
    def user(self):
        return self.__user
    @user.setter
    def user(self, v):
        self.__user = v

    # Host and dest are checked by calling check_host() and check_dest()
    # explicitly since they make connections to the remote machine
    @property
    def host(self):
        return self.__host
    @host.setter
    def host(self, v):
        self.__host = v

    @property
    def dest(self):
        return self._dest
    @dest.setter
    def dest(self, v):
        self.__dest = v

    @property
    def num_backups(self):
        return self.__backups
    @num_backups.setter
    def num_backups(self, v):
        i = int(v)
        if i < 1:
            self.__out.warn('Number of backups must be >= 1, {} specified, using'
            ' 1 instead\n'.format(v))
            self.__backups = 1
            return
        self.__backups = i

    @property
    def rsync_bin(self):
        return self.__rsync_bin
    @rsync_bin.setter
    def rsync_bin(self, v):
        if not os.path.exists(v):
            self.__out.warn('rsync binary: {} does not exist IGNORED\n'.format(v))
            self.__rsync_bin = 'rsync'
            return
        self.__rsync_bin = v

    @property
    def rsync_flags(self):
        return self.__rsync_flags
    @rsync_flags.setter
    def rsync_flags(self, v):
        self.__rsync_flags = v

    @property
    def exclude(self):
        return self.__exclude
    @exclude.setter
    def exclude(self, v):
        if v is not None and not os.path.exists(v):
            self.__out.warn('Exclude file: {0} does not exist IGNORED\n'.format(v))
            self.__exclude = None
            return
        self.__exclude = v

    @property
    def ssh_bin(self):
        return self.__ssh_bin
    @ssh_bin.setter
    def ssh_bin(self, v):
        if not os.path.exists(v):
            self.__out.warn('SSH binary: {} does not exist IGNORED\n'.format(v))
            self.__ssh_bin = 'ssh'
            return
        self.__ssh_bin = v

    @property
    def ssh_key(self):
        return self.__ssh_key
    @ssh_key.setter
    def ssh_key(self, v):
        if v is not None and not os.path.exists(v):
            self.__out.warn('SSH Key file: {0} does not exist IGNORED\n'.format(v))
            self.__ssh_key = None
            return
        self.__ssh_key = v

    @property
    def prefix(self):
        return self.__prefix
    @prefix.setter
    def prefix(self, v):
        if v is None:
            self.__out.warn('Backup prefix not specified, only the timestamp will be used\n')
            self.__prefix = ''
            return
        self.__prefix = v

    @property
    def dry_run(self):
        return self.__dry_run
    @dry_run.setter
    def dry_run(self, v):
        self.__dry_run = v

    @property
    def log_excludes(self):
        return self.__log_excludes
    @log_excludes.setter
    def log_excludes(self, v):
        self.__log_excludes = v

    # Runs a single command displaying it and its ireturn code, stdout and
    # stderr on the debugging stream. Returns the error code, stdout, and stderr
    def run_cmd(self, cmd):
        self.__out.debug('CMD : {0}\n'.format(' '.join(cmd)))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = proc.communicate()
        self.__out.debug('EXIT: {0}\n'.format(proc.returncode))
        self.__out.debug('OUT : {0}\n'.format(o.decode().rstrip()))
        self.__out.debug('ERR : {0}\n'.format(e.decode().rstrip()))
        return proc.returncode, o.decode(), e.decode()

    # The following two functions will be used to generate names for backups and
    # sort a list of backup names. If one is changed the other must be changed
    # such that sort_backups() sorts a list of filenames generated by
    # generate_backup_name() into chronological order.
    # (This can be done easily by using the same objects to generate and sort
    # the dates as is done below)
    def generate_backup_name(self):
        timestamp = datetime.datetime.now().strftime(self.__date_fmt_str)
        return '{0}{1}'.format(self.__prefix, timestamp)

    def sort_backups(self, backups):
        # Change to use lstrip to remove prefix since it doesn't need to be
        # conditional
        ts = lambda s: datetime.datetime.strptime(s, self.__date_fmt_str)
        backups.sort(key=lambda x: ts(x.lstrip(self.__prefix)))
        return backups

    # The following two functions are used internally to generate appropriate
    # ssh and rsync commands using the correct ssh key, user, and host
    # Builds base ssh command
    def __ssh_cmd(self):
        r = [self.__ssh_bin]
        if self.__ssh_key is not None:
            r.extend(['-i', self.__ssh_key])
        if self.__user is not None:
            r.append('{}@{}'.format(self.__user, self.__host))
        else:
            r.append(self.__host)
        return r

    # Builds base rsync command
    def __rsync_cmd(self):
        r = [self.__rsync_bin, self.__rsync_flags, '-v']
        if self.__dry_run:
            r.append('-n')
        if self.__ssh_key is not None:
            r.extend(['-e', 'ssh -i {}'.format(self.__ssh_key)])
        return r

    # Performs a test ssh command to make sure we can reach host
    def check_host(self):
        res, _, _ = self.run_cmd(self.__ssh_cmd() + ['exit 0'])
        if res != 0:
            self.__out.fatal('Unable to reach host: {}'.format(self.__host))

    # If the destination directory doesn't exist on the remote machine create it
    # (unless this is a dry run) and then either way make sure we can write
    # there
    def check_dest(self):
        # Existence
        outs = 'Destination directory: {0} does not exist {1}\n'
        res, _ , _ = self.run_cmd(self.__ssh_cmd() + ['test -d {}'.format(self.__dest)])
        if res != 0:
            if self.__dry_run:
                self.__out.info(outs.format(self.__dest, '(DRY-RUN)'))
                return
            self.__out.info(outs.format(self.__dest, 'attempting to create'))
            res, _ , e = self.run_cmd(self.__ssh_cmd() + ['mkdir', '-p', self.__dest])
            if res != 0:
                self.__out.fatal('Unable to create destination directory: {0}\n'.format(e))
            self.__out.info('Destination directory created successfully\n')
        # Writability
        red, _, _ = self.run_cmd(self.__ssh_cmd() + ['test -w {}'.format(self.__dest)])
        if res != 0:
            self.__out.fatal('Destination directory is not writable\n')

    # Lists the files in the destination directory and then pass them through a
    # regex to isolate only backups
    def list_dest_backups(self):
        res, o, e = self.run_cmd(self.__ssh_cmd() + ['ls {0}'.format(self.__dest)])
        if res != 0:
            self.__out.fatal('Unable to list files in destination directory: {0}\n'.format(e), 1)
        regex = self.__prefix + '\d{2}-\d{2}-\d{4}-\d{2}:\d{2}:\d{2}'
        e = re.compile(regex)
        backups = [f for f in o.split() if e.search(f)]
        return self.sort_backups(backups)

    # Function to find the most recent backup in the destination directory or in
    # the list of backups passed as the backups argument
    def most_recent_backup(self, backups=None):
        if backups is None:
            backups = self.list_dest_backups()
        else:
            backups = self.sort_backups(backups)
        if len(backups) == 0:
            return None
        else:
            return backups[-1]

    # Create a new backup with the given settings
    def create_backup(self):
        # Get a n ame for the backup
        name = self.generate_backup_name()
        self.__out.info('Attempting to creating backup: {0}\n'.format(name))

        # Check to make sure the backup doesn't already exist
        backups = self.list_dest_backups()
        if name in backups:
            self.__out.fatal('Backup: {0} already exists\n'.format(name))

        # Build the rsync command for the backup
        rsync_backup = self.__rsync_cmd()

        # Exclude
        if self.__exclude is not None:
            rsync_backup.append('--exclude-from={0}'.format(self.__exclude))

        # Link-dest (feed in list of backups from above to avoid extra ssh)
        link = self.most_recent_backup(backups)
        if link is not None:
            lp = os.path.join(self.__dest, link)
            self.__out.info('Most recent backup (link-dest): {0}\n'.format(lp))
            rsync_backup.append('--link-dest={0}'.format(lp))
        else:
            self.__out.info('No backups were found, creating initial backup\n')

        # Source and destination
        rsync_backup.append(self.__src)
        rsync_backup.append('{0}@{1}:{2}'.format(self.__user, self.__host,
            os.path.join(self.__dest, name)))

        # Execute the rsync command
        res, o, e = self.run_cmd(rsync_backup)
        if res != 0:
            self.__out.fatal('Unable to create backup: {0}\n'.format(e), 2)
        else:
            if not self.__dry_run:
                self.__out.info('Backup: {} created successfully\n'.format(name))

    # Removes any old backups if the number of exisiting backups is greater than the
    # number specified to keep
    def remove_backups(self):
        self.__out.info('Attempting to remove old backups\n')
        backups = self.list_dest_backups()
        if len(backups) <= self.__backups:
            self.__out.info('{0}/{1} backups exist, no removal necessary.\n'.format(
                len(backups), self.__backups))
            return
        backups.reverse()
        to_remove = backups[self.__backups:]
        if self.__dry_run:
            self.__out.info('Would have removed backup(s): {0} '
                '(DRY-RUN)\n'.format(' '.join(to_remove)))
            return
        self.__out.info('Removing backup(s): {0}\n'.format(' '.join(to_remove)))
        res, _, e = self.run_cmd(self.__ssh_cmd() +
                ['rm -r {0}'.format(
                    ' '.join([os.path.join(self.__dest,x) for x in to_remove])
                    )
                ]
            )
        if res != 0:
            self.__out.error('Unable to remove backup(s): {0}\n'.format(e))
        self.__out.info('Successfully removed {0} backup(s)\n'.format(len(to_remove)))

# End of class code ------------------------------------------------------------
# The following is script to create backups using the backup class above

# Parses the command line into a dictionary. Does not include anything with a
# value of None
#def parse_command_line():
#    parser = argparse.ArgumentParser(description='Creates and rotates remote backups')
#    parser.add_argument('-v', '--verbose', action='count', default=0,
#            help='Verbose output')
#    parser.add_argument('-n', '--dry-run', action='store_true',
#            help='Do not actually create backup')
#    parser.add_argument('-c', '--config-file', type=str, metavar='FILE',
#            help='Configuration file to use')
#    parser.add_argument('-b', '--num-backups', type=int, metavar='N',
#            help='Number of backups to keep')
#    parser.add_argument('-s', '--source-dir', type=str, dest='src',
#            metavar='DIR', help='Source directory (local)')
#    parser.add_argument('-d', '--dest-dir', type=str, metavar='DIR',
#            dest='dest', help='Destination directory (remote)')
#    parser.add_argument('-m', '--remote-machine', type=str, metavar='MACHINE',
#            dest='host', help='Destination host')
#    parser.add_argument('-u', '--user', type=str,
#            help='Username on destination machine')
#    parser.add_argument('-k', '--key', type=str, dest='ssh_key',
#            help='SSH key to use')
#    parser.add_argument('-e', '--exclude-file', type=str, metavar='FILE',
#            help="File to use as rsync's exclude file")
#    parser.add_argument('-l', '--log-excludes', action='store_true',
#            help='Store a log of the excluded files')
#    parser.add_argument('-p', '--prefix', type=str, dest='prefix',
#            help='String to use as prefix for backup')
#    args = parser.parse_args()
#    return {key: value for key, value in vars(args).items()
#            if value is not None}

# Parses a list of configuration files (in order) overriding anything read
# previously
#def parse_config_files(files, out):
#    config = configparser.SafeConfigParser()
#    config_files = config.read(files)
#    settings = dict()
#    for s in config.sections():
#        for o in config.options(s):
#            #if config.get(s, o) is not None:
#            if o == 'num_backups':
#                try:
#                    settings[o] = config.getint(s, o)
#                except ValueError:
#                    out.error('Invalid int value specified in configuration'
#                        ' file: {0} using 1 instead\n'.format(config.get(s, o)))
#                    settings[o] = 1
#            else:
#                settings[o] = config.get(s, o)
#    # Remove anything with a value of None before returning
#    return {k: v for k, v in settings.items() if v is not None}, config_files

# Main program to create backups using configuration files and command line
# arguments
#def main():
#    # Read command-line arguments ----------------------------------------------
#    cl_settings = parse_command_line()
#
#    # Set up object to display output based on the verbose level we got --------
#    s = {}
#    # Always show warnings on stdout
#    s['warn'] = sys.stdout
#    # If we got no -v show nothing
#    if cl_settings['verbose'] < 1:
#        s['info'] = s['debug'] = None
#    # if we got -v only show info messages on stdout
#    elif cl_settings['verbose'] < 2:
#        s['info'] = sys.stdout
#        s['debug'] = None
#    # if we got -vv show everything on stdout
#    else:
#        s['info'] = s['debug'] = sys.stdout
#    # Always show errors and fatal messages on stderr
#    s['error'] = sys.stderr
#    s['fatal'] = sys.stderr
#    # Add printer to cl_settings so it gets picked up by backup object
#    cl_settings['printer'] = backup_printer(**s)
#    # Remove the verbose level from the dictionary
#    del cl_settings['verbose']
#
#    # Read config files --------------------------------------------------------
#    # Default paths to read
#    config_files = ['/etc/backup.conf', os.path.expanduser('~/.backup.conf')]
#    # If a config file is specified on the command line add it to the list and
#    # remove it from the settings dict()
#    if 'config_file' in cl_settings:
#        config_files.append(cl_settings.pop('config_file'))
#    settings, cf_read = parse_config_files(config_files, cl_settings['printer'])
#
#    # Merge the command line settings with the configuration file settings
#    # (command-line overrides configuration values if both specified)
#    settings.update(cl_settings)
#
#    # List any configuration files used before checking settings so if there is
#    # an error the user has some recourse to find it
#    settings['printer'].info('Configuration file(s) read: {0}\n'.format(' '.join(cf_read)))
#
#    # Output all settings for debugging (sorted for sanity)
#    settings['printer'].debug('SETTINGS DUMP:\n{0}\n'.format(
#            '\n'.join(sorted(['{0}={1}'.format(x, settings[x]) for x in settings]))
#            )
#            )
#
#    # Create a backup object to work with
#    bck = backup(**settings)
#
#    if bck.dry_run:
#        settings['printer'].info('Performing a dry run...\n')
#
#    # Make sure we can get to host
#    bck.check_host()
#
#    # Check that the destination directory exists and if this isn't a dry run,
#    # have it created
#    bck.check_dest()
#
#    # Create the new backup
#    bck.create_backup()
#
#    # Get rid of old backups
#    bck.remove_backups()

if __name__ == '__main__':
    main()
