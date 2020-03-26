# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module with all value transformation functions.

E.g., if you specify `value_transform=int` to `filter_tasks()`, then the comparison
value will be converted using `value = int(value)`.

This module just imports all value transformation functions into a single module/namespace.

"""

from builtins import *  # provides int, float, eval (!), etc.
from datetime import time, datetime
from dateutil.parser import parse as parse_dateutil
from dateparser import parse as parse_dateparser

parse_date = parse_dateutil




