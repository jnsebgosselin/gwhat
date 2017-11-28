# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

import pytest

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Local imports
from gwhat.projet.reader_projet import ProjetReader                    # nopep8
from gwhat.projet.manager_projet import (ProjetManager, QFileDialog)   # nopep8


# Qt Test Fixtures
# --------------------------------


@pytest.fixture
def projet_manager_bot(qtbot):
    manager = ProjetManager()
    manager.new_projet_dialog.setModal(False)
    qtbot.addWidget(manager)
    qtbot.addWidget(manager.new_projet_dialog)
    data_input = {'name': "@ new-prô'jèt!",
                  'latitude': 45.40,
                  'longitude': 73.15}

    return manager, data_input, qtbot

# Tests
# -------------------------------


@pytest.mark.run(order=1)
def test_create_new_projet(projet_manager_bot, mocker):
    manager, data_input, qtbot = projet_manager_bot
    manager.show()

    projetpath = os.path.join(
            os.getcwd(), data_input['name'], data_input['name']+'.gwt')

    # Delete project folder and its content if it already exist.
    if os.path.exists(os.path.join(os.getcwd(), data_input['name'])):
        import shutil
        shutil.rmtree(os.path.join(os.getcwd(), data_input['name']))

    # Show new project dialog windows and fill the fields.
    manager.show_newproject_dialog()
    manager.new_projet_dialog.name.setText(data_input['name'])
    manager.new_projet_dialog.author.setText(data_input['name'])
    manager.new_projet_dialog.lat_spinbox.setValue(data_input['latitude'])
    manager.new_projet_dialog.lon_spinbox.setValue(data_input['longitude'])

    # Mock the file dialog window so that we can specify programmatically
    # the path where the project will be saved.
    mocker.patch.object(QFileDialog, 'getExistingDirectory',
                        return_value=os.getcwd())

    # Select the path where the project will be saved.
    manager.new_projet_dialog.browse_saveIn_folder()

    # Create and save the new project and asser that its name is correctly
    # displayed in the UI and that the project file has been created.
    manager.new_projet_dialog.save_project()

    assert manager.project_display.text() == data_input['name']
    assert os.path.exists(projetpath)


@pytest.mark.run(order=1)
def test_load_projet(projet_manager_bot, mocker):
    manager, data_input, qtbot = projet_manager_bot
    manager.show()
    manager.show_newproject_dialog()

    projetpath = os.path.join(
            os.getcwd(), data_input['name'], data_input['name']+'.gwt')

    # Mock the file dialog window so that we can specify programmatically
    # the path of the project.
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(projetpath, '*.gwt'))

    # Select and load the project.
    manager.select_project()

    # Assert that the project has been loaded correctly and that its name is
    # displayed correctly in the UI.

    assert manager.project_display.text() == data_input['name']
    assert type(manager.projet) is ProjetReader
    assert manager.projet.name == data_input['name']
    assert manager.projet.author == data_input['name']
    assert manager.projet.lat == data_input['latitude']
    assert manager.projet.lon == data_input['longitude']


if __name__ == "__main__":
    # pytest.main([os.path.basename(__file__)])
    pytest.main()
