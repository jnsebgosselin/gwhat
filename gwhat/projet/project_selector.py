# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the MIT License.
# -----------------------------------------------------------------------------

from __future__ import division, unicode_literals

# ---- Standard library imports
import os.path as osp

# ---- Third party imports
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QPushButton, QMenu, QAction


class ProjectSelector(QPushButton):
    """
    A pushbutton that provides a graphical interface for the user to
    create and open projects.
    """
    sig_current_project_changed = QSignal(str)
    sig_request_open_project = QSignal()
    sig_request_new_project = QSignal()
    sig_request_load_project = QSignal(str)

    def __init__(self, parent=None, recent_projects=None,
                 recent_projects_icon=None, max_recent_projects=15):
        super().__init__(parent)
        self.setMinimumWidth(125)

        self._recent_project_actions = []
        self._protected_actions = []
        self._current_project = None
        self._recent_project_icon = recent_projects_icon or QIcon()
        self._max_recent_projects = max_recent_projects

        self.menu = QMenu()
        self.setMenu(self.menu)
        self.menu.aboutToShow.connect(self._validate)
        self.menu.setToolTipsVisible(True)
        self.menu.installEventFilter(self)

        self._new_project_action = QAction(
            text='New Project...', parent=self.parent())
        self._new_project_action.triggered.connect(
            lambda: self.sig_request_new_project.emit())
        self.menu.addAction(self._new_project_action)
        self._new_project_action.setToolTip("Create a new project.")
        self._protected_actions.append(self._new_project_action)

        self._open_project_action = QAction(
            text='Open Project...', parent=self.parent())
        self._open_project_action.triggered.connect(
            lambda: self.sig_request_open_project.emit())
        self.menu.addAction(self._open_project_action)
        self._open_project_action.setToolTip("Open an existing project.")
        self._protected_actions.append(self._open_project_action)

        self._protected_actions.append(self.menu.addSeparator())

        # Setup recent projects.
        for project in reversed(recent_projects or []):
            self.add_recent_project(project)

    def eventFilter(self, widget, event):
        """Handle key events on the QMenu of this ProjectSelector."""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Delete:
            # Remove hovered item from the list of recent projects.
            action = self.menu.actionAt(
                self.menu.mapFromGlobal(QCursor.pos()))
            if action not in self._protected_actions:
                self.remove_recent_project(action.data())
        return super().eventFilter(widget, event)

    def _validate(self):
        """
        Validate that each project currently added to the list of recent
        projects is available and remove it if it is not.
        """
        for action in self._recent_project_actions:
            if not osp.exists(action.data()):
                self._recent_project_actions.remove(action)
                self.menu.removeAction(action)

    # ---- Public API
    def recent_projects(self):
        """
        Return the list of recent projects.

        Returns
        -------
        list of str
            The list of recent projects absolute paths.
        """
        self._validate()
        return [action.data() for action in self._recent_project_actions]

    def remove_recent_project(self, filename):
        """
        Remove the project corresponding to filename from the list
        of recent projects.

        Parameters
        ----------
        filename : str
            The absolute path of the project that needs to be removed from
            the list of recent projects.

        Returns
        -------
        removed_action : QAction
            The QAction corresponding to the project that was removed from
            the list of recent projects.
        """
        self._validate()
        if filename is None or not osp.exists(filename):
            return

        for action in self._recent_project_actions:
            if osp.samefile(filename, action.data()):
                self._recent_project_actions.remove(action)
                self.menu.removeAction(action)
                return action

    def add_recent_project(self, filename):
        """
        Add the project corresponding to filename to the list
        of recent projects.

        The project is always added at the top of the recent projects list.

        Parameters
        ----------
        filename : str
            The absolute path of the project that needs to be added to
            the list of recent projects.
        """
        self._validate()
        if filename is None or not osp.exists(filename):
            return

        for action in self._recent_project_actions:
            if osp.samefile(filename, action.data()):
                action = self.remove_recent_project(action.data())
                break
        else:
            action = QAction(
                text=osp.basename(filename),
                icon=self._recent_project_icon,
                parent=self.parent())
            action.triggered.connect(
                lambda: self.sig_request_load_project.emit(filename))
            action.setToolTip(filename)
            action.setData(filename)

        # Make sure the number of recent projet does not exceed the
        # maximum value.
        while len(self._recent_project_actions) >= self._max_recent_projects:
            self.menu.removeAction(self._recent_project_actions.pop(-1))

        if len(self._recent_project_actions):
            self.menu.insertAction(self._recent_project_actions[0], action)
        else:
            self.menu.addAction(action)
        self._recent_project_actions.insert(0, action)

    def set_current_project(self, filename):
        """
        Set the current project to filename.

        name
        ----------
        filename : str, optional
            The absolute path of the filename of the current project.
        """
        if filename is None or not osp.exists(filename):
            self.setText('')
            self.setToolTip(None)
            self._current_project = None
        else:
            self.setText(osp.basename(filename))
            self.setToolTip(filename)
            self._current_project = filename
        self.sig_current_project_changed.emit(self._current_project)
