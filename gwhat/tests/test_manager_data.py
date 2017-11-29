# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

import pytest

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt

# Local imports
from gwhat.projet.reader_projet import ProjetReader                    # nopep8
from gwhat.projet.manager_data import DataManager, QFileDialog, QMessageBox

projetpath = os.path.join(os.getcwd(), "@ new-prô'jèt!", "@ new-prô'jèt!.gwt")


# Qt Test Fixtures
# --------------------------------

@pytest.fixture
def data_manager_bot(qtbot):
    data_manager = DataManager(projet=ProjetReader(projetpath))
    qtbot.addWidget(data_manager)

    return data_manager, qtbot

# Tests
# -------------------------------


@pytest.mark.run(order=7)
def test_load_projet(data_manager_bot):
    data_manager, qtbot = data_manager_bot
    data_manager.show()
    assert data_manager


@pytest.mark.run(order=7)
def test_import_weather_data(data_manager_bot, mocker):
    data_manager, qtbot = data_manager_bot
    data_manager.new_weather_win.setModal(False)
    data_manager.show()

    # Assert that the weather datafile exists.
    output_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Output")
    filename = os.path.join(output_dir, "IBERVILLE (7023270)",
                            "IBERVILLE (7023270)_2000-2010.out")
    assert os.path.exists(filename)

    # Mock the QFileDialog to return the path of the file.
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(filename, '*.out'))

    # Open the dialog window to import a weather dataset.
    qtbot.mouseClick(data_manager.btn_load_meteo, Qt.LeftButton)
    data_manager.new_weather_win.select_dataset()
    qtbot.mouseClick(data_manager.new_weather_win.btn_ok, Qt.LeftButton)

    # Assert that a weather dataset was added to the project and is currently
    # selected.
    assert data_manager.wxdataset_count() == 1
    assert data_manager.wxdsets_cbox.currentText() == "IBERVILLE"


@pytest.mark.run(order=7)
def test_delete_weather_data(data_manager_bot, mocker):
    data_manager, qtbot = data_manager_bot
    data_manager.show()

    # Mock the QMessageBox to return Yes, delete the weather dataset, and
    # assert that it was removed from the project.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(data_manager.btn_del_wxdset, Qt.LeftButton)
    assert data_manager.wxdataset_count() == 0


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
