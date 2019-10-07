# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

"""
File for running tests programmatically.
"""

import os
import pytest
import matplotlib as mpl
mpl.use('Qt5Agg')
os.environ['GWHAT_PYTEST'] = 'True'


def main():
    """
    Run pytest tests.
    """
    errno = pytest.main(['-x', 'gwhat', '-v', '-rw', '--durations=10',
                         '--cov=gwhat'])
    if errno != 0:
        raise SystemExit(errno)


if __name__ == '__main__':
    main()
