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


INPUTDATA = {'name': "test @ prô'jèt!", 'latitude': 45.40, 'longitude': 73.15}


# ---- Pytest Fixtures
@pytest.fixture(scope="module")
def projectpath(tmp_path_factory):
    basetemp = tmp_path_factory.getbasetemp()
    return osp.join(
        basetemp, INPUTDATA['name'], INPUTDATA['name'] + '.gwt')


@pytest.fixture
def projmanager(qtbot):
    projmanager = ProjetManager()
    projmanager.new_projet_dialog.setModal(False)
    qtbot.addWidget(projmanager)
    qtbot.addWidget(projmanager.new_projet_dialog)

    return projmanager


# ---- Tests
def test_create_new_projet(projmanager, mocker, projectpath):
    """Test the creation of a new project."""
    projmanager.show()

    # Show new project dialog windows and fill the fields.
    projmanager.show_newproject_dialog()
    new_projet_dialog = projmanager.new_projet_dialog

    # Fill the project dialog fields.
    new_projet_dialog.name.setText(INPUTDATA['name'])
    new_projet_dialog.author.setText(INPUTDATA['name'])
    new_projet_dialog.lat_spinbox.setValue(INPUTDATA['latitude'])
    new_projet_dialog.lon_spinbox.setValue(INPUTDATA['longitude'])

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
    assert projmanager.project_display.text() == INPUTDATA['name']
    assert osp.exists(projectpath)
    assert osp.exists(projectpath + '.bak')

    # Close the project.
    projmanager.close_projet()


def test_load_projet(projmanager, mocker, projectpath):
    """Test loading and existing project."""
    projmanager.show()
    projmanager.show_newproject_dialog()

    # Mock the file dialog window so that we can specify programmatically
    # the path of the project.
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(projectpath, '*.gwt'))

    # Select and load the project.
    projmanager.select_project()

    # Assert that the project has been loaded correctly and that its name is
    # displayed correctly in the UI.
    assert projmanager.project_display.text() == INPUTDATA['name']
    assert type(projmanager.projet) is ProjetReader
    assert projmanager.projet.name == INPUTDATA['name']
    assert projmanager.projet.author == INPUTDATA['name']
    assert projmanager.projet.lat == INPUTDATA['latitude']
    assert projmanager.projet.lon == INPUTDATA['longitude']

    projmanager.close_projet()


def test_load_non_existing_project(projmanager, mocker, projectpath):
    """Test trying to open a project when the .gwt file does not exist."""
    mock_qmsgbox_ = mocker.patch.object(
        QMessageBox, 'exec_', return_value=QMessageBox.Ok)
    projmanager.load_project("non_existing_project.gwt")

    assert mock_qmsgbox_.call_count == 1
    assert projmanager.projet is None


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
