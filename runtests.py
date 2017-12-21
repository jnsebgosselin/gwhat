# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
#

"""
File for running tests programmatically.
"""

import os
import pytest
import matplotlib as mpl
mpl.use('Qt5Agg')


def main():
    """
    Run pytest tests.
    """
    if os.name == 'nt':
        errno = pytest.main(['-x', 'gwhat',  '-v', '-rw', '--durations=10',
                             '--cov=gwhat'])
    else:
        errno = pytest.main(['-x', 'gwhat',  '-v', '-rw', '--durations=10'])

    if errno != 0:
        raise SystemExit(errno)


if __name__ == '__main__':
    main()
