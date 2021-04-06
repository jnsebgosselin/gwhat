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
os.environ['GWHAT_PYTEST'] = 'True'

# ---- Third party imports
import numpy as np
import pytest

# ---- Local imports
from gwhat.common.utils import save_content_to_file
from gwhat.projet.reader_projet import ProjetReader
from gwhat.projet.manager_projet import (
    ProjetManager, QFileDialog, QMessageBox, CONF)
from gwhat.projet.reader_waterlvl import WLDataFrame
from gwhat.utils.math import nan_as_text_tolist

NAME = "test @ prô'jèt!"
LAT = 45.40
LON = 73.15


# =============================================================================
# ---- Pytest Fixtures
# =============================================================================
@pytest.fixture
def testfile(tmp_path):
    """Create  a testfile containing a waterlevel dataset."""
    columns = ['Date', 'WL(mbgs)']
    n_data = 33000
    time_data = np.arange(1000, n_data + 1000)
    wl_data = np.random.rand(n_data)
    datastack = np.vstack([time_data, wl_data]).transpose()

    filename = osp.join(tmp_path, 'waterlvl_testfile.csv')
    fcontent = [
        ['Well ID', 3040002],
        ['Latitude', 45.74581],
        ['Longitude', -73.28024],
        ['Altitude', 19.51],
        ['Province', 'QC'],
        ['', '']]
    fcontent.append(columns)
    fcontent.extend(nan_as_text_tolist(datastack))
    save_content_to_file(filename, fcontent)

    return filename


@pytest.fixture
def projectpath(tmpdir):
    """A path to a non existing project file."""
    return osp.join(str(tmpdir), NAME, NAME + '.gwt')


@pytest.fixture
def projectfile(projectpath):
    """A path to a valid existing project file."""
    project = ProjetReader(projectpath)
    assert osp.exists(projectpath)

    project.name = NAME
    project.author = NAME
    project.lat = LAT
    project.lon = LON

    project.close()

    return projectpath


@pytest.fixture
def bakfile(projectfile):
    """A path to a valid project backup file."""
    project = ProjetReader(projectfile)
    project.backup_project_file()
    project.close()
    assert osp.exists(projectfile + '.bak')
    return projectfile + '.bak'


@pytest.fixture
def project(projectfile):
    """Create a generic GWHAT project at the specified path."""
    project = ProjetReader(projectfile)
    return project


@pytest.fixture
def projmanager(qtbot):
    # We need to reset the configs to defaults after each test to make sure
    # they can be run independently one from another.
    CONF.reset_to_defaults()

    projmanager = ProjetManager()
    projmanager.new_projet_dialog.setModal(False)
    qtbot.addWidget(projmanager)
    qtbot.addWidget(projmanager.new_projet_dialog)
    projmanager.show()

    return projmanager


# =============================================================================
# ---- Tests
# =============================================================================
def test_create_new_projet(projmanager, mocker, projectpath):
    """
    Test the creation of a new project.
    """
    # Show new project dialog windows and fill the fields.
    projmanager.show_newproject_dialog()
    new_projet_dialog = projmanager.new_projet_dialog

    # Fill the project dialog fields.
    new_projet_dialog.name.setText(NAME)
    new_projet_dialog.author.setText(NAME)
    new_projet_dialog.lat_spinbox.setValue(LAT)
    new_projet_dialog.lon_spinbox.setValue(LON)

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
    assert osp.exists(projectpath)
    assert osp.exists(projectpath + '.bak')
    assert projmanager.project_selector.text() == NAME + '.gwt'
    assert projmanager.project_selector.recent_projects() == [
        projectpath]
    assert len(projmanager.project_selector.menu.actions()) == 4

    # Close the project.
    projmanager.close_projet()


def test_load_projet(projmanager, mocker, projectfile):
    """
    Test loading a valid existing project.
    """
    # Select and load the project.
    assert not osp.exists(projectfile + '.bak')
    mocker.patch.object(
        QFileDialog, 'getOpenFileName', return_value=(projectfile, '*.gwt'))
    projmanager.select_project()
    assert osp.exists(projectfile + '.bak')

    # Assert that the project has been loaded correctly and that its name is
    # displayed correctly in the UI.
    assert isinstance(projmanager.projet, ProjetReader)
    assert projmanager.projet.name == NAME
    assert projmanager.projet.author == NAME
    assert projmanager.projet.lat == LAT
    assert projmanager.projet.lon == LON
    assert projmanager.project_selector.text() == NAME + '.gwt'
    assert projmanager.project_selector.recent_projects() == [
        projectfile]
    assert len(projmanager.project_selector.menu.actions()) == 4

    projmanager.close_projet()


def test_load_non_existing_project(projmanager, mocker, projectpath):
    """
    Test trying to open a project when the .gwt file does not exist.
    """
    assert not osp.exists(projectpath)
    mock_qmsgbox = mocker.patch.object(
        QMessageBox, 'exec_', returned_value=QMessageBox.Ok)
    result = projmanager.load_project(projectpath)

    assert mock_qmsgbox.call_count == 1
    assert result is False
    assert projmanager.projet is None
    assert projmanager.project_selector.text() == ''
    assert projmanager.project_selector.recent_projects() == []
    assert len(projmanager.project_selector.menu.actions()) == 3


def test_load_invalid_project(projmanager, mocker, projectpath):
    """
    Test loading an invalid project when no backup exists.
    """
    # Create an invalid project file.
    os.makedirs(osp.dirname(projectpath))
    with open(projectpath, 'w') as f:
        f.write('empty file')
    assert osp.exists(projectpath)

    mock_qmsgbox = mocker.patch.object(QMessageBox, 'exec_')
    mock_qmsgbox.return_value = QMessageBox.Ok
    result = projmanager.load_project(projectpath)

    assert mock_qmsgbox.call_count == 1
    assert result is False
    assert projmanager.projet is None
    assert projmanager.project_selector.text() == ''
    assert projmanager.project_selector.recent_projects() == []
    assert len(projmanager.project_selector.menu.actions()) == 3


def test_load_corrupt_project_continue(projmanager, mocker, projectfile):
    """
    Test loading a corrupt project when no backup exists and click to
    load it anyway.
    """
    assert osp.exists(projectfile)
    assert not osp.exists(projectfile + '.bak')

    mock_checkproj = mocker.patch.object(
        ProjetReader, 'check_project_file', return_value=False)
    mock_qmsgbox = mocker.patch.object(
        QMessageBox, 'exec_', return_value=QMessageBox.Yes)

    result = projmanager.load_project(projectfile)
    assert mock_checkproj.call_count == 1
    assert mock_qmsgbox.call_count == 1

    assert result is True
    assert isinstance(projmanager.projet, ProjetReader)
    assert projmanager.projet.name == NAME
    assert projmanager.projet.author == NAME
    assert projmanager.projet.lat == LAT
    assert projmanager.projet.lon == LON
    assert projmanager.project_selector.text() == NAME + '.gwt'
    assert projmanager.project_selector.recent_projects() == [
        projectfile]
    assert len(projmanager.project_selector.menu.actions()) == 4

    # Backup file are not generated when the project is corrupt.
    assert not osp.exists(projectfile + '.bak')


def test_load_corrupt_project_cancel(projmanager, mocker, projectfile):
    """
    Test loading a corrupt project when no backup exists and click to
    cancel the operation so that no project is loaded.
    """
    assert osp.exists(projectfile)
    assert not osp.exists(projectfile + '.bak')

    mock_checkproj = mocker.patch.object(
        ProjetReader, 'check_project_file', return_value=False)
    mock_qmsgbox = mocker.patch.object(
        QMessageBox, 'exec_', return_value=QMessageBox.Cancel)

    result = projmanager.load_project(projectfile)
    assert mock_checkproj.call_count == 1
    assert mock_qmsgbox.call_count == 1

    assert result is False
    assert projmanager.projet is None
    assert projmanager.project_selector.text() == ''
    assert projmanager.project_selector.recent_projects() == []
    assert len(projmanager.project_selector.menu.actions()) == 3

    # Backup file are not generated when the project is corrupt.
    assert not osp.exists(projectfile + '.bak')


def test_restore_invalid_project(projmanager, mocker, projectfile, bakfile):
    """
    Test restoring an invalid project from backup.
    """
    # Override the project file with an invalid project file.
    with open(projectfile, 'w') as f:
        f.write('empty file')

    # Try loading the invalid project and Cancel restore from backup.
    mock_qmsgbox = mocker.patch.object(QMessageBox, 'exec_')
    mock_qmsgbox.return_value = QMessageBox.Cancel
    result = projmanager.load_project(projectfile)

    assert mock_qmsgbox.call_count == 1
    assert result is False
    assert projmanager.projet is None
    assert projmanager.project_selector.text() == ''
    assert projmanager.project_selector.recent_projects() == []
    assert len(projmanager.project_selector.menu.actions()) == 3

    # Try loading the corrupt project and accept to restore from backup.
    mock_qmsgbox.return_value = QMessageBox.Yes
    result = projmanager.load_project(projectfile)

    assert mock_qmsgbox.call_count == 2
    assert result is True
    assert isinstance(projmanager.projet, ProjetReader)
    assert projmanager.projet.name == NAME
    assert projmanager.projet.author == NAME
    assert projmanager.projet.lat == LAT
    assert projmanager.projet.lon == LON
    assert projmanager.project_selector.text() == NAME + '.gwt'
    assert projmanager.project_selector.recent_projects() == [
        projectfile]
    assert len(projmanager.project_selector.menu.actions()) == 4


def test_restore_invalid_project_from_invalid_backup(projmanager, mocker,
                                                     projectpath):
    """
    Test restoring an invalid project when the backup is also invalid.
    """
    # Create an invalid project file and backup file.
    os.makedirs(osp.dirname(projectpath))
    with open(projectpath, 'w') as f:
        f.write('empty file')
    with open(projectpath + '.bak', 'w') as f:
        f.write('empty backup file')

    # Try loading the invalid project and accept to restore from the
    # invalid backup.
    mock_qmsgbox = mocker.patch.object(QMessageBox, 'exec_')
    mock_qmsgbox.return_value = QMessageBox.Yes
    result = projmanager.load_project(projectpath)

    assert mock_qmsgbox.call_count == 2
    assert result is False
    assert projmanager.projet is None
    assert projmanager.project_selector.text() == ''
    assert projmanager.project_selector.recent_projects() == []
    assert len(projmanager.project_selector.menu.actions()) == 3


def test_restore_corrupt_project(projmanager, mocker, projectfile, bakfile):
    """
    Test restoring a corrupt project from backup.
    """
    mock_checkproj = mocker.patch.object(ProjetReader, 'check_project_file')
    mock_checkproj.side_effect = [False, True, True]

    mock_qmsgbox = mocker.patch.object(QMessageBox, 'exec_')

    # Try loading the corrupt project and click Cancel.
    mock_qmsgbox.return_value = QMessageBox.Cancel

    result = projmanager.load_project(projectfile)
    assert mock_qmsgbox.call_count == 1
    assert mock_checkproj.call_count == 1
    assert result is False
    assert projmanager.projet is None
    assert projmanager.project_selector.text() == ''
    assert projmanager.project_selector.recent_projects() == []
    assert len(projmanager.project_selector.menu.actions()) == 3

    # Try loading the corrupt project and click Ignore.
    mock_checkproj.reset_mock()
    mock_checkproj.side_effect = [False, True, True]
    mock_qmsgbox.return_value = QMessageBox.Ignore

    result = projmanager.load_project(projectfile)
    assert mock_qmsgbox.call_count == 2
    assert mock_checkproj.call_count == 1
    assert result is True
    assert isinstance(projmanager.projet, ProjetReader)
    assert projmanager.project_selector.text() == NAME + '.gwt'
    assert projmanager.project_selector.recent_projects() == [
        projectfile]
    assert len(projmanager.project_selector.menu.actions()) == 4

    # Try loading the corrupt project and click Yes.
    mock_checkproj.reset_mock()
    mock_checkproj.side_effect = [False, True, True]
    mock_qmsgbox.return_value = QMessageBox.Yes

    result = projmanager.load_project(projectfile)
    assert mock_qmsgbox.call_count == 3
    assert mock_checkproj.call_count == 3
    assert result is True
    assert isinstance(projmanager.projet, ProjetReader)
    assert projmanager.project_selector.text() == NAME + '.gwt'
    assert projmanager.project_selector.recent_projects() == [
        projectfile]
    assert len(projmanager.project_selector.menu.actions()) == 4


def test_store_mrc(project, testfile):
    """
    Test that MRC data and results are saved and retrieved as expected
    in GWHAT project files.
    """
    project.add_wldset('dataset_test', WLDataFrame(testfile))
    wldset = project.get_wldset('dataset_test')
    assert wldset.mrc_exists() is False

    # Add MRC data to the test dataset.
    A = 1
    B = 2
    periods = [(2, 100), (30000, 33000)]
    recess_time = np.arange(0, 1000, 0.1).tolist()
    recess_wlvl = np.random.rand(len(recess_time)).tolist()

    wldset.set_mrc(A, B, periods, recess_time, recess_wlvl)
    assert wldset.mrc_exists() is True

    mrc_data = wldset.get_mrc()
    assert mrc_data['params'] == [A, B]
    assert mrc_data['peak_indx'] == periods
    assert mrc_data['time'].tolist() == recess_time
    assert mrc_data['recess'].tolist() == recess_wlvl


def test_mrc_backward_compatibility(project, testfile):
    """
    Test that converting mrc peak_indx data from int16 to int64 is
    working as expected.

    This is a test to ensure backward compatibility with projects created
    with GWHAT version 0.5.0 and older.

    See jnsebgosselin/gwhat#370.
    See jnsebgosselin/gwhat#377.
    """
    # Add the dataset to the test project.
    project.add_wldset('dataset_test', WLDataFrame(testfile))
    wldset = project.get_wldset('dataset_test')

    # Make sure that the namespace was created automatically for the mrc
    # and that the peak_indx has the right dtype.
    assert wldset['mrc/peak_indx'].tolist() == []
    assert wldset['mrc/peak_indx'].dtype == np.dtype('float64')

    # Save peak_indx data to the project file as int16 to reproduce a
    # project file created with GWHAT version 0.5.0 and older.
    del wldset.dset['mrc/peak_indx']
    wldset.dset.file.flush()

    peak_indx = [2, 17, 100, 30000, 33000]
    wldset.dset['mrc'].create_dataset(
        'peak_indx', data=np.array([]), dtype='int16', maxshape=(None,))
    wldset.dset['mrc/peak_indx'].resize(np.shape(peak_indx))
    wldset.dset['mrc/peak_indx'][:] = np.array(peak_indx)
    wldset.dset.file.flush()

    assert wldset['mrc/peak_indx'].dtype == np.dtype('int16')
    assert wldset['mrc/peak_indx'].tolist() == [2, 17, 100, 30000, 32767]
    # Note that the maximum value that can be stored in a int16 is 32767. This
    # is why the 33000 was clipped to 32767.

    # Fetch the test waterlevel dataset again from the project and make sure
    # that the peak_indx data were converted as expected to float64 and as
    # xls numerical dates instead of time indexes of the time series.
    wldset = project.get_wldset('dataset_test')
    assert wldset['mrc/peak_indx'].dtype == np.dtype('float64')
    assert wldset['mrc/peak_indx'].tolist() == wldset.xldates[
        [2, 17, 100, 30000, 32767]].tolist()

    # Make sure the data are formatted as expected when fetched.
    mrc_data = wldset.get_mrc()
    assert np.isnan(mrc_data['params']).tolist() == [True, True]
    assert mrc_data['peak_indx'] == [
        (wldset.xldates[2], wldset.xldates[17]),
        (wldset.xldates[100], wldset.xldates[30000])]

    assert mrc_data['time'].tolist() == []
    assert mrc_data['recess'].tolist() == []


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw',
                 '-k', 'test_mrc_backward_compatibility'])
