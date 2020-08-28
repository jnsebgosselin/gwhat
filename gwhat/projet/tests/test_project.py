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
import pytest

# ---- Local imports
from gwhat.projet.reader_projet import ProjetReader
from gwhat.projet.manager_projet import (
    ProjetManager, QFileDialog, QMessageBox, CONF)

NAME = "test @ prô'jèt!"
LAT = 45.40
LON = 73.15


# ---- Pytest Fixtures
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


# ---- Tests
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


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
