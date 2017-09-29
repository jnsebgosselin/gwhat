# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
#

"""
File for running tests programmatically.
"""

import pytest


def main():
    """
    Run pytest tests.
    """
    pytest.main(['-x', 'WHAT',  '-v', '-rw', '--durations=10', '--cov=../WHAT'])


if __name__ == '__main__':
    main()
