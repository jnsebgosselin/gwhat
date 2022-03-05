# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import os
import os.path as osp
os.environ['GWHAT_PYTEST'] = 'True'

# ---- Third party imports
import pytest

# ---- Local imports
from gwhat import __rootdir__
from gwhat.config.ospath import get_path_from_configs
from gwhat.mainwindow import MainWindow
from gwhat.projet.manager_projet import QMessageBox
from gwhat.projet.reader_projet import ProjetReader

WORKDIR = os.getcwd()


# =============================================================================
# ---- Pytest Fixtures
# =============================================================================
@pytest.fixture(scope="module")
def project(tmp_path_factory):
    basetemp = tmp_path_factory.getbasetemp()
    return ProjetReader(osp.join(basetemp, "mainwindow_test.gwt"))


@pytest.fixture
def mainwindow(qtbot, mocker):
    """A fixture for Sardes main window."""
    # Since the project Example does not exist on the github repo, we need
    # to mock QMessageBox to close the warning message that will appears
    # on startup.
    mocker.patch.object(QMessageBox, 'exec_', return_value=QMessageBox.Ok)

    mainwindow = MainWindow()
    # qtbot.addWidget(mainwindow)
    mainwindow.show()
    qtbot.waitExposed(mainwindow)

    return mainwindow


# =============================================================================
# ---- Tests
# =============================================================================
def test_mainwindow_init(mainwindow, project):
    """
    Tests that the MainWindow opens correctly and throws an error message
    since the project Example does not exist. Asserts that GWHAT throws an
    error message correctly when the project file is not valid. Finally,
    tests that a valid project is loaded correctly.
    """
    assert mainwindow

    default_project_path = osp.normpath(osp.abspath(osp.join(
        osp.dirname(__rootdir__), 'Projects', 'Example', 'Example.gwt')))
    assert (get_path_from_configs('main', 'last_project_filepath') ==
            default_project_path)

    # Load a project file that is not valid. For the puspose of this test, we
    # will use water_level_datafile.xlsx.
    mainwindow.pmanager.load_project(
        osp.join(WORKDIR, 'water_level_datafile.xlsx'))
    assert mainwindow.pmanager.projet is None
    assert (get_path_from_configs('main', 'last_project_filepath') ==
            default_project_path)

    # Load the valid project file that was created in the previous tests.
    mainwindow.pmanager.load_project(project.filename)
    assert mainwindow.pmanager.projet.filename == project.filename
    assert (get_path_from_configs('main', 'last_project_filepath') ==
            project.filename)


def test_restart_mainwindow(mainwindow, qtbot, mocker, project):
    """
    Tests that the last opened valid project in the last session is loaded
    correctly from the config file.
    """
    assert mainwindow.pmanager.projet.filename == project.filename
    assert (get_path_from_configs('main', 'last_project_filepath') ==
            project.filename)


if __name__ == "__main__":
    pytest.main(['-x', osp.basename(__file__), '-v', '-rw'])
