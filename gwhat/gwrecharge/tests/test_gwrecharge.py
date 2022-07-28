# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import os.path as osp
from shutil import copyfile

# ---- Third party imports
import pytest
from PyQt5.QtCore import Qt

# ---- Local library imports
from gwhat import __rootdir__
from gwhat.projet.reader_projet import ProjetReader
from gwhat.gwrecharge.gwrecharge_gui import RechgEvalWidget


# =============================================================================
# ---- Pytest Fixtures
# =============================================================================
@pytest.fixture
def project(tmp_path):
    fsrc = osp.join(
        __rootdir__, 'gwrecharge', 'tests', 'test_gwrecharge_project.gwt')
    fdst = osp.join(
        tmp_path, 'test_gwrecharge_project.gwt')
    copyfile(fsrc, fdst)
    return ProjetReader(fdst)


@pytest.fixture()
def gwrecharge_widget(qtbot, project):
    gwrecharge_widget = RechgEvalWidget()
    gwrecharge_widget.set_wldset(project.get_wldset('3040002_15min'))
    gwrecharge_widget.set_wxdset(project.get_wxdset('Marieville'))

    qtbot.addWidget(gwrecharge_widget)
    gwrecharge_widget.show()
    qtbot.waitExposed(gwrecharge_widget)

    return gwrecharge_widget


# =============================================================================
# ---- Tests
# =============================================================================
def test_calc_gwrecharge(gwrecharge_widget, project, qtbot):
    """
    Test that calculating groundwater recharge is working as expected.
    """
    gwrecharge_widget.wldset.clear_glue()
    assert gwrecharge_widget.wldset.glue_count() == 0

    with qtbot.waitSignal(gwrecharge_widget.sig_new_gluedf, timeout=5000):
        qtbot.mouseClick(gwrecharge_widget.calc_rechg_btn, Qt.LeftButton)

    assert gwrecharge_widget.wldset.glue_count() == 1


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
