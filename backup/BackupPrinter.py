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

## \package backup.BackupPrinter
#
# A module that provides the `backup_printer` class to use to output messages

import datetime
import os
import re
import subprocess

## \class backup.BackupPrinter.backup_printer
#  Temporary class to handle output for `backup` class
#
# A simple class to handle output, each output type can be redirected to
# possibly different streams. Streams only need to support a write(str) method.
# Tested using sys.stdout/sys.stderr to output to a terminal and files to
# support logs. Eventually this should be removed and replaced with exceptions.
class backup_printer:

    ## Creates a `backup_printer` object
    #  \param warn warning stream
    #  \param info info stream
    #  \param debug debugging stream
    #  \param error error stream
    #  \param fatal fatal error stream
    def __init__(self, warn=None, info=None, debug=None, error=None, fatal=None):
        ## warning stream
        self._warn = warn
        ## info stream
        self._info = info
        ## debug stream
        self._deb = debug
        ## error stream
        self._err = error
        ## fatal stream
        self._fat = fatal

    # Used for debugging
    #def __repr__(self):
    #    return 'warn={}; info={}; debug={}; error={}; fatal={};'.format(
    #            self._warn.name, self._info.name, self._deb.name,
    #            self._err.name, self._fat.name)

    ## Writes `msg` and then `s` to `stream`
    #
    # Writes the real message, `s`, preceded by `msg` to `stream`
    def _write(self, msg, s, stream):
        if stream is not None:
            stream.write('{0}{1}'.format(msg, s))

    ## Writes `s` to the warning stream
    #  \param s Object to write (usually a string)
    def warn(self, s):
        self._write('WARNING: ', s, self._warn)

    ## Writes `s` to the info stream
    #  \param s Object to write (usually a string)
    def info(self, s):
        self._write('INFO: ', s, self._info)

    ## Writes `s` to the debugging stream
    #  \param s Object to write (usually a string)
    def debug(self, s):
        self._write('DEBUG: ', s, self._deb)

    ## Writes `s` to the error stream
    #  \param s Object to write (usually a string)
    def error(self, s):
        self._write('ERROR: ', s, self._err)

    ## Writes `s` to the fatal stream and exit
    #  \param s Object to write (usually a string)
    #  \param exit_code exit code
    def fatal(self, s, exit_code):
        self._write('FATAL: ', s, self._fat)
        exit(exit_code)
