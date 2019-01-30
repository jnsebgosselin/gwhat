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


INPUTDATA = {'name': "test @ prô'jèt!", 'latitude': 45.40, 'longitude': 73.15}


# ---- Pytest Fixtures
@pytest.fixture(scope="module")
def projectpath(tmp_path_factory):
    basetemp = tmp_path_factory.getbasetemp()
    return osp.join(
        basetemp, INPUTDATA['name'], INPUTDATA['name'] + '.gwt')


@pytest.fixture
def project_manager(qtbot):
    project_manager = ProjetManager()
    project_manager.new_projet_dialog.setModal(False)
    qtbot.addWidget(project_manager)
    qtbot.addWidget(project_manager.new_projet_dialog)

    return project_manager


# ---- Tests
def test_create_new_projet(project_manager, mocker, projectpath):
    """Test the creation of a new project."""
    project_manager.show()

    # Show new project dialog windows and fill the fields.
    project_manager.show_newproject_dialog()
    new_projet_dialog = project_manager.new_projet_dialog

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
    project_manager.new_projet_dialog.browse_saveIn_folder()

    # Create and save the new project and asser that its name is correctly
    # displayed in the UI and that the project file has been created.
    project_manager.new_projet_dialog.save_project()

    assert project_manager.project_display.text() == INPUTDATA['name']
    assert osp.exists(projectpath)

    project_manager.close_projet()


def test_load_projet(project_manager, mocker, projectpath):
    project_manager.show()
    project_manager.show_newproject_dialog()

    # Mock the file dialog window so that we can specify programmatically
    # the path of the project.
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(projectpath, '*.gwt'))

    # Select and load the project.
    project_manager.select_project()

    # Assert that the project has been loaded correctly and that its name is
    # displayed correctly in the UI.

    assert project_manager.project_display.text() == INPUTDATA['name']
    assert type(project_manager.projet) is ProjetReader
    assert project_manager.projet.name == INPUTDATA['name']
    assert project_manager.projet.author == INPUTDATA['name']
    assert project_manager.projet.lat == INPUTDATA['latitude']
    assert project_manager.projet.lon == INPUTDATA['longitude']

    project_manager.close_projet()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
