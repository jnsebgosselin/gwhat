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
from gwhat.projet.reader_projet import ProjetReader
from gwhat.projet.manager_projet import (ProjetManager, QFileDialog)
from gwhat.projet.manager_projet import QMessageBox

NAME = "test @ prô'jèt!"
LAT = 45.40
LON = 73.15


# ---- Pytest Fixtures
@pytest.fixture
def projectpath(tmpdir):
    return osp.join(str(tmpdir), NAME, NAME + '.gwt')


@pytest.fixture
def projmanager(qtbot):
    projmanager = ProjetManager()
    projmanager.new_projet_dialog.setModal(False)
    qtbot.addWidget(projmanager)
    qtbot.addWidget(projmanager.new_projet_dialog)
    projmanager.show()

    return projmanager


# ---- Helpers
def create_project_at(projectpath):
    """Create a generic GWHAT project at the specified path."""
    project = ProjetReader(projectpath)
    project.name = NAME
    project.author = NAME
    project.lat = LAT
    project.lon = LON
    project.close_projet()


# ---- Tests
def test_create_new_projet(projmanager, mocker, projectpath):
    """
    Test the creation of a new project.
    """
    # Show new project dialog windows and fill the fields.
    projmanager.show_newproject_dialog()
    new_projet_dialog = projmanager.new_projet_dialog

    # Fill the project dialog fields.
    new_projet_dialog.name.setText(NAME)
    new_projet_dialog.author.setText(NAME)
    new_projet_dialog.lat_spinbox.setValue(LAT)
    new_projet_dialog.lon_spinbox.setValue(LON)

    # Mock the file dialog window so that we can specify programmatically
    # the path where the project will be saved.
    mocker.patch.object(
        QFileDialog, 'getExistingDirectory',
        return_value=osp.dirname(osp.dirname(projectpath)))

    # Select the path where the project will be saved.
    projmanager.new_projet_dialog.browse_saveIn_folder()

    # Create and save the new project, assert that its name is correctly
    # displayed in the UI, and check that the project file and a backup file
    # have been created.
    projmanager.new_projet_dialog.save_project()
    assert projmanager.project_display.text() == NAME
    assert osp.exists(projectpath)
    assert osp.exists(projectpath + '.bak')

    # Close the project.
    projmanager.close_projet()


def test_load_projet(projmanager, mocker, projectpath):
    """
    Test loading a valid existing project.
    """
    create_project_at(projectpath)

    # Select and load the project.
    mocker.patch.object(
        QFileDialog, 'getOpenFileName', return_value=(projectpath, '*.gwt'))
    projmanager.select_project()
    assert osp.exists(projectpath + '.bak')

    # Assert that the project has been loaded correctly and that its name is
    # displayed correctly in the UI.
    assert projmanager.project_display.text() == NAME
    assert type(projmanager.projet) is ProjetReader
    assert projmanager.projet.name == NAME
    assert projmanager.projet.author == NAME
    assert projmanager.projet.lat == LAT
    assert projmanager.projet.lon == LON

    projmanager.close_projet()


def test_load_non_existing_project(projmanager, mocker):
    """Test trying to open a project when the .gwt file does not exist."""
    mock_qmsgbox_ = mocker.patch.object(
        QMessageBox, 'exec_', return_value=QMessageBox.Ok)
    projmanager.load_project("non_existing_project.gwt")

    assert mock_qmsgbox_.call_count == 1
    assert projmanager.projet is None


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
