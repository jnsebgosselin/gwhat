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


@pytest.mark.run(order=1)
def test_load_projet(data_manager_bot):
    data_manager, qtbot = data_manager_bot
    data_manager.show()

    assert data_manager


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__), '-v', '-rw', '--cov=gwhat'])
    # pytest.main()
