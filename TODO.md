# TODO
* Fix remaining return/exception behaviors to make everything consistent
  * check functions should never raise exceptions and always return a value
  * functions that actually do work should return some value when they are
    successful and raise an exception otherwise
  * `create_backup()` might be the only one that remains
* Add `create_directory()` function to `backup_manager` class
* Add exclude logging functionality
* More testing, possibly for `create_backup.py`
* Write configuration generation script for `create_backup.py`
