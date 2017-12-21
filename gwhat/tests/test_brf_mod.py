# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import sys
import os

# Third party imports
import pytest
from PyQt5.QtCore import Qt

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.brf_mod.kgs_gui import BRFManager, KGSBRFInstaller, QMessageBox
from gwhat.projet.reader_projet import ProjetReader


# Qt Test Fixtures
# --------------------------------

@pytest.fixture
def brf_manager_bot(qtbot):
    brf_manager = BRFManager(None)
    qtbot.addWidget(brf_manager)
    qtbot.addWidget(brf_manager.viewer)

    return brf_manager, qtbot


# Test BRFManager
# -------------------------------

@pytest.mark.run(order=9)
def test_install_kgs_brf(brf_manager_bot, mocker):
    brf_manager, qtbot = brf_manager_bot
    brf_manager.show()
    assert brf_manager
    assert brf_manager.kgs_brf_installer

    # In Linux, a warning message will popup telling the user that this
    # feature is not supported for their system.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)

    # Install the KGS_BRF software and assert that it was correctly
    # installed and that the kgs_brf installer was uninstalled correctly.
    qtbot.mouseClick(brf_manager.kgs_brf_installer.install_btn, Qt.LeftButton)

    qtbot.waitUntil(lambda: brf_manager.kgs_brf_installer is None)
    assert KGSBRFInstaller().kgsbrf_is_installed()


@pytest.mark.run(order=9)
@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_run_kgs_brf(brf_manager_bot):
    brf_manager, qtbot = brf_manager_bot
    brf_manager.show()

    # Set the water level dataset and assert the expected values are displayed
    # correctly in the GUI.
    projet = ProjetReader(os.path.join(os.getcwd(),
                                       "@ new-prô'jèt!", "@ new-prô'jèt!.gwt"))
    wldset = projet.get_wldset(projet.wldsets[0])
    brf_manager.set_wldset(wldset)

    assert brf_manager.lagBP == 300
    assert brf_manager.lagET == 300
    assert brf_manager.detrend == 'Yes'
    assert brf_manager.correct_WL == 'No'
    assert brf_manager.brfperiod == (41241.0, 41584.0)

    brf_manager.set_datarange((41300.0, 41400.0))
    assert brf_manager.brfperiod == (41300.0, 41400.0)

    # Calcul the brf and assert the the results are plotted as expected.
    assert brf_manager.viewer.current_brf.value() == 0
    brf_manager.calc_brf()
    assert brf_manager.viewer.current_brf.value() == 1


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
