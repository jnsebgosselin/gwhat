# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the MIT License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import os
import os.path as osp

# ---- Third party imports
import pytest
from PyQt5.QtCore import Qt

# ---- Local imports
from gwhat.projet.project_selector import ProjectSelector


# ---- Pytest Fixtures
@pytest.fixture
def projectfiles(tmp_path):
    """A path to a non existing project file."""
    filenames = []
    for i in range(5):
        filename = osp.join(tmp_path, 'testfile_{}.tpf'.format(i + 1))
        with open(filename, 'w') as f:
            f.close()
        filenames.append(filename)
    return filenames


@pytest.fixture
def project_selector(qtbot, projectfiles):
    # We delete the second file from the list to test that the project
    # selector files that doesn't exists.
    os.remove(projectfiles[1])
    assert not osp.exists(projectfiles[1])

    project_selector = ProjectSelector(
        parent=None,
        recent_projects=projectfiles,
        max_recent_projects=3)

    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 2, 3]])
    assert len(project_selector.menu.actions()) == 6
    assert project_selector._current_project is None
    assert project_selector.text() == ''

    return project_selector


# ---- Tests
def test_set_current_project(project_selector, projectfiles):
    """
    Test that setting the current project is working as expected.
    """
    # Test setting None as current project.
    project_selector.set_current_project(None)
    assert project_selector._current_project is None
    assert project_selector.text() == ''

    # Test setting a project whose file is NOT accessible.
    assert not osp.exists(projectfiles[1])
    project_selector.set_current_project(projectfiles[1])
    assert project_selector._current_project is None
    assert project_selector.text() == ''

    # Test setting a project whose file is accessible.
    project_selector.set_current_project(projectfiles[3])
    assert project_selector._current_project == projectfiles[3]
    assert project_selector.text() == osp.basename(projectfiles[3])


def test_add_recent_project(project_selector, projectfiles):
    """
    Test that adding recent projects is working as expected.
    """
    # Test adding None.
    project_selector.add_recent_project(None)
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 2, 3]])
    assert len(project_selector.menu.actions()) == 6

    # Test adding a project whose file is NOT accessible.
    project_selector.add_recent_project(projectfiles[1])
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 2, 3]])
    assert len(project_selector.menu.actions()) == 6

    # Test adding a project that is already in the list of recent projects.
    project_selector.add_recent_project(projectfiles[2])
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [2, 0, 3]])
    assert len(project_selector.menu.actions()) == 6

    # Test adding a project that is not in the list of recent projects.
    project_selector.add_recent_project(projectfiles[4])
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [4, 2, 0]])
    assert len(project_selector.menu.actions()) == 6


def test_remove_recent_project(project_selector, projectfiles):
    """
    Test that removing recent projects is working as expected.
    """
    # Test removing None.
    project_selector.remove_recent_project(None)
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 2, 3]])
    assert len(project_selector.menu.actions()) == 6

    # Test removing a project whose file is NOT accessible.
    project_selector.remove_recent_project(projectfiles[1])
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 2, 3]])
    assert len(project_selector.menu.actions()) == 6

    # Test removing a project that is NOT in the list of recent projects.
    project_selector.remove_recent_project(projectfiles[4])
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 2, 3]])
    assert len(project_selector.menu.actions()) == 6

    # Test removing a project that is in the list of recent projects.
    project_selector.remove_recent_project(projectfiles[2])
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 3]])
    assert len(project_selector.menu.actions()) == 5


def test_delete_recent_project(project_selector, projectfiles, qtbot):
    """
    Test that removing recent projects by pressing the delete key when
    hovering the corresponding item in the menu is working as expected.
    """
    project_selector.menu.show()
    assert project_selector.menu.isVisible()
    assert len(project_selector.menu.actions()) == 3 + 3
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 2, 3]])
    assert len(project_selector.menu.actions()) == 6

    # Try to remove a protected action.
    pos = project_selector.menu.actionGeometry(
        project_selector._open_project_action).center()
    qtbot.mouseMove(project_selector.menu, pos)
    qtbot.keyPress(project_selector.menu, Qt.Key_Delete)
    assert len(project_selector.menu.actions()) == 3 + 3
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 2, 3]])
    assert len(project_selector.menu.actions()) == 6

    # Try to remove a recent project.
    pos = project_selector.menu.actionGeometry(
        project_selector._recent_project_actions[1]).center()
    qtbot.mouseMove(project_selector.menu, pos)
    qtbot.keyPress(project_selector.menu, Qt.Key_Delete)
    assert len(project_selector.menu.actions()) == 3 + 2
    assert project_selector.recent_projects() == (
        [projectfiles[i] for i in [0, 3]])
    assert len(project_selector.menu.actions()) == 5

    project_selector.menu.close()


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
