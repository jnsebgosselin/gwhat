# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
#

"""
File for running tests programmatically.
"""

import pytest
import WHAT


def main():
    """
    Run pytest tests.
    """
    errno = pytest.main(['-x', 'WHAT',  '-v', '-rw', '--durations=10',
                         '--cov=WHAT'])

    if errno != 0:
        raise SystemExit(errno)


if __name__ == '__main__':
    main()
