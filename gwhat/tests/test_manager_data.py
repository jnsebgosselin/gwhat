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

# Local imports
from gwhat.projet.reader_projet import ProjetReader                    # nopep8
from gwhat.projet.manager_data import DataManager                      # nopep8

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
def test_load_weather_data(data_manager_bot, mocker):
    data_manager, qtbot = data_manager_bot
    data_manager.new_weather_win.setModal(False)
    data_manager.show()

    output_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Output")
    filenames = [os.path.join("IBERVILLE (7023270)",
                              "IBERVILLE (7023270)_2000-2010.out"),
                 os.path.join("L'ACADIE (702LED4)",
                              "L'ACADIE (702LED4)_2000-2010.out"),
                 os.path.join("MARIEVILLE (7024627)",
                              "MARIEVILLE (7024627)_2000-2010.out")
                 ]

    # Assert that the weather datafile exists.
    for fname in filenames:
        assert os.path.exists(os.path.join(output_dir, fname))


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
