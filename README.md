python-backup
=============

A Python module to create efficient backups using ssh and rsync

# Basics
## Backup class
This class is designed to be used to configure, create, and remove backups. It
could be used to develop a Python program that does backups periodically and is
used in the `create_backup` script.

## Create Backup Script
This script uses the `backup` class to create a single backup and remove any old
backups according to command-line options and configuration files.

### To use "create_backup":
1. To list available command-line options use: `create_backup -h`
2. A sample configuration file is included as: `sample.conf`
3. Configure create_backup by using a combination of command-line options and/or
   configuration files

While the create_backup script is designed to be used as a cron job, it might
not be a bad idea to watch/log the first few to make sure that the configuration
is correct.
