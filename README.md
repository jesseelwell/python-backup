python-backup
=============

A Python package/script to create efficient backups using ssh and rsync

# Basics

## Building the environment
### (Currently only needed for testing)
Requirements: pip, virtualenv
To create the virtual environment and install any necessary packages:
1. `virtualenv -p /path/to/python3 localenv`
2. `source localenv/bin/activate`
3. `pip install -r requirements`

## Create Backup Script
This script uses the `backup_manager` class to create a single backup and remove
any old backups according to command-line options and configuration files.

### To use "create_backup":
1. To list available command-line options use: `create_backup -h`
2. A sample configuration file is included as: `sample.conf`
3. Configure create_backup by using a combination of command-line options and/or
   configuration files

While the create_backup script is designed to be used as a cron job, it might
not be a bad idea to watch/log the first few to make sure that the configuration
is correct.

## Documentation
Documentation can be found in the source code and compiled using Doxygen. To
build HTML documentation (assuming Doxygen is installed):
### To build documentation:
1. `cd docs/`
2. `make`

## Testing
In progress. To run all tests, make sure you have the environment set up
properly, and then:
1. `source localenv/bin/activate` (if needed)
2. `cd testing/`
3. `python -m unittest`
