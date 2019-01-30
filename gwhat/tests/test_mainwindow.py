# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports
import os
import os.path as osp

# ---- Third party imports
import pytest

# ---- Local imports
from gwhat.mainwindow import MainWindow
from gwhat.projet.manager_projet import QMessageBox
from gwhat.projet.reader_projet import ProjetReader

WORKDIR = os.getcwd()


# ---- Pytest Fixtures
@pytest.fixture(scope="module")
def project(tmp_path_factory):
    # Create a project and add add the wldset to it.
    basetemp = tmp_path_factory.getbasetemp()
    return ProjetReader(osp.join(basetemp, "mainwindow_test.gwt"))


# ---- Test MainWindow
def test_mainwindow_init(qtbot, mocker, project):
    """
    Tests that the MainWindow opens correctly and throws an error message
    since the project Example does not exist. Asserts that GWHAT throws an
    error message correctly when the project file is not valide. Finally,
    tests that a valid project is loaded correctly.
    """
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
    mainwindow.pmanager.load_project(project.filename)
    assert mainwindow.pmanager.projet is not None
    assert mainwindow.whatPref.projectfile == project.filename


def test_restart_mainwindow(qtbot, mocker, project):
    """
    Tests that the last opened valid project in the last session is loaded
    correctly from the config file.
    """
    mainwindow = MainWindow()
    qtbot.addWidget(mainwindow)

    assert osp.abspath(mainwindow.whatPref.projectfile) == project.filename
    assert mainwindow.pmanager.projet is not None
    assert osp.abspath(mainwindow.pmanager.projet.filename) == project.filename
    assert osp.abspath(mainwindow.pmanager.projet.dirname) == (
        osp.dirname(project.filename))


if __name__ == "__main__":
    pytest.main(['-x', osp.basename(__file__), '-v', '-rw'])
