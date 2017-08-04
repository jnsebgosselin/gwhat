# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

import pytest

import sys
import os.path
sys.path.append(os.pathdirname(os.pathdirname(os.pathrealpath(__file__))))
    
# Local imports
from projet.reader_projet import ProjetReader



def test_projet_load_correctly():
    dirname = os.pathdirname(os.pathrealpath(__file__))
    fname = os.path.join(dirname, "Example.what")
    pr = ProjetReader(fname)
    
    assert pr.name == 'Example'    

    
if __name__ == "__main__":
    pytest.main()
