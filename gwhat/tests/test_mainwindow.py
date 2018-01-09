# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: Standard Libraries

import sys
import os
import os.path as osp

# ---- Imports: Tird Party Imports

import pytest
from PyQt5.QtCore import Qt

# ---- Imports: Local Imports

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.mainwindow import MainWindow
from gwhat.projet.manager_projet import QMessageBox


# Qt Test Fixtures
# --------------------------------


PROJETPATH = osp.join(os.getcwd(), "@ new-prô'jèt!", "@ new-prô'jèt!.gwt")
WORKDIR = os.getcwd()


@pytest.fixture
def mainwindow_bot(qtbot):
    mainwindow = MainWindow()
    qtbot.addWidget(mainwindow)

    return mainwindow, qtbot


# Test MainWindow
# -------------------------------

@pytest.mark.run(order=11)
def test_mainwindow_init(qtbot, mocker):
    # Since the project Example does not exist, we need to mock QMessageBox
    # to close the warning message that will appears on startup.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)
    default_project_path = osp.join('..', 'Projects', 'Example', 'Example.gwt')
    if osp.exists(osp.join(WORKDIR, 'WHAT.pref')):
        os.remove(osp.join(WORKDIR, 'WHAT.pref'))

    # Start GWHAT.
    mainwindow = MainWindow()
    qtbot.addWidget(mainwindow)

    assert mainwindow
    assert mainwindow.whatPref.projectfile == default_project_path
    assert mainwindow.pmanager.projet is None

    # Load a project file that is not valid. For the puspose of this test, we
    # will use water_level_datafile.xlsx.
    mainwindow.pmanager.load_project(
            osp.join(WORKDIR, 'water_level_datafile.xlsx'))
    assert mainwindow.whatPref.projectfile == default_project_path
    assert mainwindow.pmanager.projet is None

    # Load the valid project file that was created in the previous tests.
    mainwindow.pmanager.load_project(PROJETPATH)
    assert mainwindow.pmanager.projet is not None
    assert mainwindow.whatPref.projectfile == PROJETPATH


@pytest.mark.run(order=11)
def test_restart_mainwindow(qtbot, mocker):
    mainwindow = MainWindow()
    qtbot.addWidget(mainwindow)

    assert osp.abspath(mainwindow.whatPref.projectfile) == PROJETPATH
    assert mainwindow.pmanager.projet is not None
    assert osp.abspath(mainwindow.pmanager.projet.filename) == PROJETPATH
    assert osp.abspath(mainwindow.pmanager.projet.dirname) == osp.dirname(PROJETPATH)


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
#     pytest.main()
