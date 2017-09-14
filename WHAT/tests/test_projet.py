# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

import pytest

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Third party imports
from PyQt5.QtCore import Qt                                            # nopep8

# Local imports
from projet.reader_projet import ProjetReader                          # nopep8
from projet.manager_projet import (ProjetManager, QFileDialog)         # nopep8


# Qt Test Fixtures
# --------------------------------


@pytest.fixture
def projet_manager_bot(qtbot):
    manager = ProjetManager()
    manager.new_projet_dialog.setModal(False)
    qtbot.addWidget(manager)
    qtbot.addWidget(manager.new_projet_dialog)

    data = {}
    data['name'] = 'New_Projet'  # "Ñew­prÔ'jÈt!"
    data['latitude'] = 45.40
    data['longitude'] = 73.15

    return manager, data, qtbot

# Tests
# -------------------------------


@pytest.mark.run(order=1)
def test_create_new_projet(projet_manager_bot, mocker):
    manager, data, qtbot = projet_manager_bot
    manager.show()

    expected_name = data['name']
    expected_path = os.path.join(
            os.getcwd(), expected_name, expected_name+'.what')

    # Delete project folder and its content if it already exist.
    if os.path.exists(os.path.join(os.getcwd(), expected_name)):
        import shutil
        shutil.rmtree(os.path.join(os.getcwd(), expected_name))

    # Show new project dialog windows and fill the fields.
    manager.show_newproject_dialog()
    keys = [Qt.Key_Ntilde, Qt.Key_E, Qt.Key_W, Qt.Key_hyphen, Qt.Key_P,
            Qt.Key_R, Qt.Key_Ocircumflex, Qt.Key_Apostrophe, Qt.Key_J,
            Qt.Key_Egrave, Qt.Key_T, Qt.Key_Exclam]
    for key in keys:
        qtbot.keyClick(manager.new_projet_dialog.name, key)
        qtbot.keyClick(manager.new_projet_dialog.author, key)
    manager.new_projet_dialog.lat_spinbox.setValue(data['latitude'])
    manager.new_projet_dialog.lon_spinbox.setValue(data['longitude'])

    # Mock the file dialog window so that we can specify programmatically
    # the path where the project will be saved.
    mocker.patch.object(QFileDialog, 'getExistingDirectory',
                        return_value=os.getcwd())

    # Select the path where the project will be saved.
    manager.new_projet_dialog.browse_saveIn_folder()

    # Create and save the new project and asser that its name is correctly
    # displayed in the UI and that the project file has been created.
    manager.new_projet_dialog.save_project()

    assert manager.project_display.text() == expected_name
    assert os.path.exists(expected_path)


@pytest.mark.run(order=1)
def test_load_projet(projet_manager_bot, mocker):
    manager, data, qtbot = projet_manager_bot
    manager.show()
    manager.show_newproject_dialog()

    expected_name = data['name']
    expected_lat = data['latitude']
    expected_lon = data['longitude']
    expected_path = os.path.join(
            os.getcwd(), expected_name, expected_name+'.what')

    # Mock the file dialog window so that we can specify programmatically
    # the path of the project.
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(expected_path, '*.what'))

    # Select and load the project.
    manager.select_project()

    # Assert that the project has been loaded correctly and that its name is
    # displayed correctly in the UI.

    assert manager.project_display.text() == expected_name
    assert type(manager.projet) is ProjetReader
    assert manager.projet.name == expected_name
    assert manager.projet.author == expected_name
    assert manager.projet.lat == expected_lat
    assert manager.projet.lon == expected_lon


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
    # pytest.main()
