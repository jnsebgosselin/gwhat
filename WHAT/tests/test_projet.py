# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

import pytest

def func(x):
    return x + 1

def test_answer():
    assert func(3) == 4
    
if __name__ == "__main__":
    pytest.main()