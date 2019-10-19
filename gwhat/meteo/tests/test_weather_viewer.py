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
        osp.dirname(__file__), "sample_weather_datafile.csv"))


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
    filepath = osp.join(str(tmpdir), 'weather_normals.pdf')
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepath, '*.pdf'))

    assert not osp.exists(filepath)
    weather_viewer.save_graph()
    assert osp.exists(filepath)


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
