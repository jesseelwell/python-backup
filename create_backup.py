#!venv/bin/python3

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

## \file create_backup.py
#
# A script that uses `backup` to create and remove backups

from backup.BackupManager import backup_manager
from backup.BackupPrinter import backup_printer

import argparse
import configparser
import os
import sys

# Parses the command line into a dictionary. Does not include anything with a
# value of None

## Parses a command-line (or similar list) for use constructing `backup` objects
#  \param args list of command-line arguments
#
# Parses a list, usually the command-line, into a dictionary that is suitable
# for use in constructing `backup` objects. This includes getting rid of any
# Nones (i.e. unspecififed settings without default values)
def parse_command_line(l):
    parser = argparse.ArgumentParser(description='Creates and rotates remote backups')
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help='Verbose output')
    parser.add_argument('-n', '--dry-run', action='store_true',
            help='Do not actually create backup')
    parser.add_argument('-c', '--config-file', type=str, metavar='FILE',
            help='Configuration file to use')
    parser.add_argument('-b', '--num-backups', type=int, metavar='N',
            help='Number of backups to keep')
    parser.add_argument('-s', '--source-dir', type=str, dest='src',
            metavar='DIR', help='Source directory (local)')
    parser.add_argument('-d', '--dest-dir', type=str, metavar='DIR',
            dest='dest', help='Destination directory (remote)')
    parser.add_argument('-m', '--remote-machine', type=str, metavar='MACHINE',
            dest='host', help='Destination host')
    parser.add_argument('-u', '--user', type=str,
            help='Username on destination machine')
    parser.add_argument('-k', '--key', type=str, dest='ssh_key',
            help='SSH key to use')
    parser.add_argument('-e', '--exclude-file', type=str, metavar='FILE',
            help="File to use as rsync's exclude file")
    parser.add_argument('-l', '--log-excludes', action='store_true',
            help='Store a log of the excluded files')
    parser.add_argument('-p', '--prefix', type=str, dest='prefix',
            help='String to use as prefix for backup')
    args = parser.parse_args(l)
    return {key: value for key, value in vars(args).items()
            if value is not None}

## Parses a list of configuration files
#  \param list of config files to parse
#  \param `backup_printer` to use for output
#
# Parses a list of configuration files (in order). Each configuration file
# overrides settings from previously read files, so they can cascade.
def parse_config_files(files, out):
    config = configparser.SafeConfigParser()
    config_files = config.read(files)
    settings = dict()
    for s in config.sections():
        for o in config.options(s):
            #if config.get(s, o) is not None:
            if o == 'num_backups':
                try:
                    settings[o] = config.getint(s, o)
                except ValueError:
                    out.error('Invalid int value specified in configuration'
                        ' file: {0} using 1 instead\n'.format(config.get(s, o)))
                    settings[o] = 1
            else:
                settings[o] = config.get(s, o)
    # Remove anything with a value of None before returning
    return {k: v for k, v in settings.items() if v is not None}, config_files

## Create and rotate a backup according to settings
#
# Creates a single backup and removes oldest backups according to the settings
# specified via configuration files and command-line options. A breif outline of
# the funciton is:
# 1. Parse command-line argument(s)
# 2. Create `backup_printer` according to command-line
# 3. Read configuration file(s)
# 4. Create `backup` object according to all settings
# 5. Create backup and remove backup(s) using this object
def main():
    # Read command-line arguments ----------------------------------------------
    cl_settings = parse_command_line(sys.argv[1:])

    # Set up object to display output based on the verbose level we got --------
    s = {}
    # Always show warnings on stdout
    s['warn'] = sys.stdout
    # If we got no -v show nothing
    if cl_settings['verbose'] < 1:
        s['info'] = s['debug'] = None
    # if we got -v only show info messages on stdout
    elif cl_settings['verbose'] < 2:
        s['info'] = sys.stdout
        s['debug'] = None
    # if we got -vv show everything on stdout
    else:
        s['info'] = s['debug'] = sys.stdout
    # Always show errors and fatal messages on stderr
    s['error'] = sys.stderr
    s['fatal'] = sys.stderr
    # Add printer to cl_settings so it gets picked up by backup object
    cl_settings['printer'] = backup_printer(**s)
    # Remove the verbose level from the dictionary
    del cl_settings['verbose']

    # Or we could log the output somewhere with something like this:
    #with open('./backup.log', 'w') as log:
    #    s = {}
    #    s['warn'] = s['info'] = s['debug'] = s['error'] = s['fatal'] = log
    #    cl_settings['printer'] = backup.backup_printer(**s)

    # Read config files --------------------------------------------------------
    # Default paths to read
    config_files = ['/etc/backup.conf', os.path.expanduser('~/.backup.conf')]
    # If a config file is specified on the command line add it to the list and
    # remove it from settings
    if 'config_file' in cl_settings:
        config_files.append(cl_settings.pop('config_file'))
    settings, cf_read = parse_config_files(config_files, cl_settings['printer'])

    # Merge and output the settings and the files read to get them -------------
    # Merge the command line settings with the configuration file settings
    # (command-line overrides configuration values if both specified)
    settings.update(cl_settings)

    # List any configuration files used before checking settings so if there is
    # an error the user has some recourse to find it
    settings['printer'].info('Configuration file(s) read: {0}\n'.format(' '.join(cf_read)))

    # Output all settings for debugging (sorted for sanity)
    settings['printer'].debug('SETTINGS DUMP:\n{0}\n'.format(
            '\n'.join(sorted(['{0}={1}'.format(x, settings[x]) for x in settings]))
            )
            )

    # Do work ------------------------------------------------------------------

    # Create a backup object to work with
    bck = backup_manager(**settings)

    if bck.dry_run:
        settings['printer'].info('Performing a dry run...\n')

    # Make sure we can get to host
    bck.check_host()

    # Check that the destination directory exists and if this isn't a dry run,
    # have it created
    bck.check_dest()

    # Create the new backup
    bck.create_backup()

    # Get rid of old backups
    bck.remove_backups()

if __name__ == '__main__':
    main()
