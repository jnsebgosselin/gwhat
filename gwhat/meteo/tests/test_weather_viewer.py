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

# ---- Third party imports
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

# ---- Local library imports
from gwhat.meteo.weather_reader import WXDataFrame
from gwhat.meteo.weather_viewer import WeatherViewer, QFileDialog


# =============================================================================
# ---- Pytest Fixtures
# =============================================================================
@pytest.fixture
def savepath(tmpdir):
    return osp.join(str(tmpdir))


@pytest.fixture
def wxdataset():
    return WXDataFrame(osp.join(
        osp.dirname(__file__), "sample_weather_datafile.xlsx"))


@pytest.fixture()
def weather_viewer(qtbot, wxdataset):
    weather_viewer = WeatherViewer()
    weather_viewer.set_weather_dataset(wxdataset)
    weather_viewer.show()
    qtbot.addWidget(weather_viewer)
    qtbot.waitForWindowShown(weather_viewer)

    return weather_viewer


# =============================================================================
# ---- Tests
# =============================================================================
def test_weather_viewer_init(weather_viewer):
    """
    Test that the weather viewer is initialized as expected.
    """
    assert weather_viewer


def test_save_graph_weather_normals(weather_viewer, mocker, tmpdir):
    """
    Test that saving the weather normal graph to a file is working as
    expected.
    """
    filepath = osp.join(str(tmpdir), 'weather_normals')
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepath, '*.pdf'))
    filepath += '.pdf'

    assert not osp.exists(filepath)
    weather_viewer.save_graph()
    assert osp.exists(filepath)


def test_save_normals_to_file(weather_viewer, mocker, tmpdir):
    """
    Test that saving the weather normals to a file is working as
    expected.
    """
    filepath = osp.join(str(tmpdir), 'weather_normals.csv')
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepath, '*.csv'))

    assert not osp.exists(filepath)
    weather_viewer.save_normals()
    assert osp.exists(filepath)


def test_copyfig_figure_to_clipboard(weather_viewer, qtbot):
    """
    Test that copying the weather normals figure to the clipboard is
    working as expected.
    """
    QApplication.clipboard().clear()
    assert QApplication.clipboard().image().isNull()

    qtbot.mouseClick(weather_viewer.btn_copy, Qt.LeftButton)
    assert not QApplication.clipboard().image().isNull()


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
