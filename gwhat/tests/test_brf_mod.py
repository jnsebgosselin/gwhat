# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import sys
import os

# Third party imports
import pytest
from PyQt5.QtCore import Qt

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.brf_mod.kgs_gui import BRFManager, KGSBRFInstaller


# Qt Test Fixtures
# --------------------------------

@pytest.fixture
def brf_manager_bot(qtbot):
    brf_manager = BRFManager(None)
    qtbot.addWidget(brf_manager)

    return brf_manager, qtbot


# Test WLCalc
# -------------------------------

@pytest.mark.run(order=9)
def test_install_kgs_brf(brf_manager_bot):
    brf_manager, qtbot = brf_manager_bot
    brf_manager.show()
    assert brf_manager
    assert brf_manager.kgs_brf_installer

    # Install the KGS_BRF software and assert that it was correctly
    # installed and that the kgs_brf installer was uninstalled correctly.
    qtbot.mouseClick(brf_manager.kgs_brf_installer.install_btn, Qt.LeftButton)
    qtbot.waitSignal(brf_manager.kgs_brf_installer.sig_kgs_brf_installed)

    assert brf_manager.kgs_brf_installer is None
    assert KGSBRFInstaller().kgsbrf_is_installed()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
