# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

from __future__ import division, unicode_literals

# ---- Standard library imports
import os
import os.path as osp
from datetime import datetime
from shutil import copyfile

# ---- Third party imports
from appconfigs.base import get_home_dir
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (
    QWidget, QLabel, QDesktopWidget, QPushButton, QApplication, QGridLayout,
    QMessageBox, QDialog, QLineEdit, QToolButton, QFileDialog)

# ---- Local imports
from gwhat.config.ospath import (
    get_select_file_dialog_dir, set_select_file_dialog_dir)
from gwhat.config.main import CONF
from gwhat.projet.reader_projet import ProjetReader
from gwhat.utils import icons
from gwhat.projet.manager_data import DataManager
from gwhat.projet.project_selector import ProjectSelector
import gwhat.common.widgets as myqt
from gwhat.widgets.layout import VSep, HSep
from gwhat import __namever__


class ProjetManager(QWidget):

    currentProjetChanged = QSignal(ProjetReader)

    def __init__(self, parent=None, projet=None):
        super(ProjetManager, self).__init__(parent)
        self.new_projet_dialog = NewProject(parent)
        self.new_projet_dialog.sig_new_project.connect(self.load_project)

        self.projet = None
        self.__initGUI__()
        if projet:
            self.load_project(projet)

    def __initGUI__(self):
        self.project_selector = ProjectSelector(
            parent=self,
            recent_projects=CONF.get('project', 'recent_projects', None),
            recent_projects_icon=icons.get_icon('folder_open'))

        self.project_selector.sig_request_new_project.connect(
            self.show_newproject_dialog)
        self.project_selector.sig_request_open_project.connect(
            self.select_project)
        self.project_selector.sig_request_load_project.connect(
            self.load_project)

        # Setup the layout.
        layout = QGridLayout(self)

        layout.addWidget(QLabel('Project :'), 0, 1)
        layout.addWidget(self.project_selector, 0, 2)

        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setColumnStretch(0, 500)
        layout.setRowMinimumHeight(0, 28)

    def select_project(self):
        """
        Show a dialog that allows users to select an existing GWHAT
        project file.
        """
        filename, _ = QFileDialog.getOpenFileName(
            self.parent(), 'Open Project', get_select_file_dialog_dir(),
            'Gwhat Project (*.gwt ; *.what)')

        if filename:
            filename = osp.abspath(filename)
            set_select_file_dialog_dir(osp.dirname(filename))
            self.projectfile = filename
            self.load_project(filename)

    def load_project(self, filename):
        """
        Load the project from the specified filename.
        """
        self.close_projet()

        # If the project doesn't exist.
        if not osp.exists(filename):
            msg_box = QMessageBox(
                QMessageBox.Warning,
                "Open project warning",
                ("<b>Failed to open the project.</b><br><br>"
                 "The project file does not exist. Please open an existing "
                 "project or create a new one."
                 "<br><br><i>{}</i>").format(osp.abspath(filename)),
                buttons=QMessageBox.Ok,
                parent=self)
            msg_box.exec_()
            return False

        # If the project fails to load.
        try:
            projet = ProjetReader(filename)
        except Exception:
            if osp.exists(filename + '.bak'):
                msg_box = QMessageBox(
                    QMessageBox.Question,
                    "Open project warning",
                    ("<b>Failed to open the project.</b><br><br>"
                     "The project file may be corrupt. Do you want to "
                     "restore the project from the last project backup?"
                     "<br><br><i>{}</i>").format(osp.abspath(filename)),
                    buttons=QMessageBox.Yes | QMessageBox.Cancel,
                    parent=self)
                reply = msg_box.exec_()
                if reply == QMessageBox.Yes:
                    return self.restore_from_backup(filename)
                else:
                    return False
            else:
                msg_box = QMessageBox(
                    QMessageBox.Warning,
                    "Open project warning",
                    ("<b>Failed to open the project.</b><br><br>"
                     "The project file is not valid. Please open an existing "
                     "valid project or create a new one."
                     "<br><br><i>{}</i>").format(osp.abspath(filename)),
                    buttons=QMessageBox.Ok,
                    parent=self)
                msg_box.exec_()
                return False
        else:
            self.projet = projet

        # If the project is corrupted.
        if self.projet.check_project_file() is True:
            self.projet.backup_project_file()
        else:
            if osp.exists(filename + '.bak'):
                msg_box = QMessageBox(
                    QMessageBox.Question,
                    "Open project warning",
                    ("<b>The project file may be corrupt.</b><br><br>"
                     "Would you like to restore the project from the last "
                     "project backup?<br><br>"
                     "Click <i>Yes</i> to restore the project, click "
                     "<i>Ignore</i> to open the project anyway, "
                     "or click <i>Cancel</i> to not open any project."
                     "<br><br><i>{}</i>").format(osp.abspath(filename)),
                    buttons=(QMessageBox.Yes |
                             QMessageBox.Ignore |
                             QMessageBox.Cancel),
                    parent=self)
                reply = msg_box.exec_()
                if reply == QMessageBox.Yes:
                    return self.restore_from_backup(filename)
                if reply == QMessageBox.Ignore:
                    pass
                else:
                    self.close_projet()
                    return False
            else:
                msg_box = QMessageBox(
                    QMessageBox.Question,
                    "Open project warning",
                    ("<b>The project file appears to be corrupt.</b><br><br>"
                     "Do you want open the project anyway?"
                     "<br><br><i>{}</i>").format(osp.abspath(filename)),
                    buttons=QMessageBox.Yes | QMessageBox.Cancel,
                    parent=self)
                reply = msg_box.exec_()
                if reply == QMessageBox.Yes:
                    pass
                else:
                    self.close_projet()
                    return False

        self.project_selector.add_recent_project(self.projet.filename)
        self.project_selector.set_current_project(self.projet.filename)
        self.project_selector.adjustSize()
        self.currentProjetChanged.emit(self.projet)

        return True

    def restore_from_backup(self, filename):
        """
        Try to restore the project from its backup file.
        """
        self.close_projet()
        msg_box = QMessageBox(
            QMessageBox.Warning,
            "Restore project warning",
            ("<b>Failed to restore the project.</b><br><br>"
             "We are very sorry for the inconvenience. "
             "Please submit a bug report on our GitHub issue tracker."),
            buttons=QMessageBox.Ok,
            parent=self)

        # First we check that the backup is ok.
        try:
            backup = ProjetReader(filename + '.bak')
            assert backup.check_project_file() is True
            backup.close()
        except Exception:
            msg_box.exec_()
            return False

        # Then we try to restore the project from the backup.
        print("Restoring project from backup... ", end='')
        try:
            os.remove(filename)
            copyfile(filename + '.bak', filename)
        except (OSError, PermissionError):
            print('failed')
            msg_box.exec_()
            return False
        else:
            print('done')
            return self.load_project(filename)

    def close_projet(self):
        """Close the currently opened hdf5 project file."""
        if self.projet is not None:
            self.projet.close()
        self.projet = None
        self.project_selector.set_current_project(None)

    def show_newproject_dialog(self):
        """Show the dialog to create a new project."""
        self.new_projet_dialog.reset_UI()
        self.new_projet_dialog.set_directory(get_select_file_dialog_dir())
        self.new_projet_dialog.show()
        if self.new_projet_dialog.result():
            set_select_file_dialog_dir(self.new_projet_dialog.directory())

    def close(self):
        """Close this project manager."""
        self.close_projet()
        CONF.set('project', 'recent_projects',
                 self.project_selector.recent_projects())


class NewProject(QDialog):
    # Dialog window to create a new WHAT project.

    sig_new_project = QSignal(str)

    def __init__(self, parent=None, directory=None):
        super(NewProject, self).__init__(parent)
        self.setModal(True)
        self.setResult(False)

        self.setWindowTitle('New Project')
        self.setWindowIcon(icons.get_icon('master'))

        self.__initUI__()
        self.set_directory(directory)

    def directory(self):
        """Return the directory currently being displayed in the dialog."""
        return self._directory

    def set_directory(self, directory):
        """Set the directory to display in the dialog."""
        if directory is None or not osp.exists(directory):
            self._directory = get_home_dir()
        else:
            self._directory = directory
        self.directory_lineedit.setText(self._directory)

    def __initUI__(self):

        # Setup current date
        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)

        # ----------------------------------------------------- PROJECT INFO --

        # ---- Widgets ----

        self.name = QLineEdit()
        self.author = QLineEdit()
        self.date = QLabel('%02d/%02d/%d %02d:%02d' % now)
        self.createdby = QLabel(__namever__)

        # ---- Layout ----

        projet_info = QGridLayout()

        row = 0
        projet_info.addWidget(QLabel('Project Title :'), row, 0)
        projet_info.addWidget(self.name, row, 1)
        row += 1
        projet_info.addWidget(QLabel('Author :'), row, 0)
        projet_info.addWidget(self.author, row, 1)
        row += 1
        projet_info.addWidget(QLabel('Created :'), row, 0)
        projet_info.addWidget(self.date, row, 1)
        row += 1
        projet_info.addWidget(QLabel('Software :'), row, 0)
        projet_info.addWidget(self.createdby, row, 1)

        projet_info.setSpacing(10)
        projet_info.setColumnStretch(1, 100)
        projet_info.setColumnMinimumWidth(1, 250)
        projet_info.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # --------------------------------------------- LOCATION COORDINATES --

        locaCoord_title = QLabel('<b>Project Location Coordinates:</b>')
        locaCoord_title.setAlignment(Qt.AlignLeft)

        self.lat_spinbox = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self.lat_spinbox.setRange(0, 180)

        self.lon_spinbox = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self.lon_spinbox.setRange(0, 180)

        # ----- layout ----

        loc_coord = QGridLayout()

        row = 0
        loc_coord.addWidget(locaCoord_title, row, 0, 1, 11)
        row += 1
        loc_coord.setColumnStretch(0, 100)
        loc_coord.addWidget(QLabel('Latitude :'), row, 1)
        loc_coord.addWidget(self.lat_spinbox, row, 2)
        loc_coord.addWidget(QLabel('North'), row, 3)
        loc_coord.setColumnStretch(4, 100)

        loc_coord.addWidget(VSep(), row, 5)
        loc_coord.setColumnStretch(6, 100)

        loc_coord.addWidget(QLabel('Longitude :'), row, 7)
        loc_coord.addWidget(self.lon_spinbox, row, 8)
        loc_coord.addWidget(QLabel('West'), row, 9)
        loc_coord.setColumnStretch(10, 100)

        loc_coord.setSpacing(10)
        loc_coord.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # Setup browse widgets.
        save_in_folder = os.path.abspath(os.path.join('..', 'Projects'))

        directory_label = QLabel('Save in Folder:')
        self.directory_lineedit = QLineEdit()
        self.directory_lineedit.setReadOnly(True)
        self.directory_lineedit.setText(save_in_folder)
        self.directory_lineedit.setMinimumWidth(350)

        btn_browse = QToolButton()
        btn_browse.setAutoRaise(True)
        btn_browse.setIcon(icons.get_icon('openFolder'))
        btn_browse.setIconSize(icons.get_iconsize('small'))
        btn_browse.setToolTip('Browse...')
        btn_browse.setFocusPolicy(Qt.NoFocus)
        btn_browse.clicked.connect(self.browse_saveIn_folder)

        browse = QGridLayout()

        browse.addWidget(directory_label, 0, 0)
        browse.addWidget(self.directory_lineedit, 0, 1)
        browse.addWidget(btn_browse, 0, 2)

        browse.setContentsMargins(0, 0, 0, 0)
        browse.setColumnStretch(1, 100)
        browse.setSpacing(10)

        # ---------------------------------------------------------- Toolbar --

        # ---- widgets ----

        btn_save = QPushButton(' Save')
        btn_save.setMinimumWidth(100)
        btn_save.clicked.connect(self.save_project)

        btn_cancel = QPushButton(' Cancel')
        btn_cancel.setMinimumWidth(100)
        btn_cancel.clicked.connect(self.close)

        # ---- layout ----

        toolbar = QGridLayout()

        toolbar.addWidget(btn_save, 0, 1)
        toolbar.addWidget(btn_cancel, 0, 2)

        toolbar.setSpacing(10)
        toolbar.setColumnStretch(0, 100)
        toolbar.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # Setup the main layout.
        main_layout = QGridLayout(self)

        main_layout.addLayout(projet_info, 0, 0)
        main_layout.addWidget(HSep(), 1, 0)
        main_layout.addLayout(loc_coord, 2, 0)
        main_layout.addWidget(HSep(), 3, 0)
        main_layout.addLayout(browse, 4, 0)
        main_layout.addLayout(toolbar, 5, 0)

        main_layout.setVerticalSpacing(25)
        main_layout.setContentsMargins(15, 15, 15, 15)  # (L, T, R, B)

    def browse_saveIn_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, 'Save in Folder', self.directory())
        if folder:
            folder = osp.abspath(folder)
            self.directory_lineedit.setText(folder)

    def save_project(self):
        name = self.name.text()
        if name == '':
            print('Please enter a valid Project name')
            return

        rootname = self.directory_lineedit.text()
        dirname = os.path.join(rootname, name)

        # If directory already exist, a number is added at the end.
        count = 1
        while osp.exists(dirname):
            dirname = os.path.join(rootname, '%s (%d)' % (name, count))
            count += 1
        os.makedirs(dirname)

        # ---- project.what ----

        fname = osp.join(dirname, '%s.gwt' % name)

        projet = ProjetReader(fname)
        projet.name = self.name.text()
        projet.author = self.author.text()
        projet.created = self.date.text()
        projet.modified = self.date.text()
        projet.version = self.createdby.text()
        projet.lat = self.lat_spinbox.value()
        projet.lon = self.lon_spinbox.value()

        del projet

        print('Creating file %s.gwt' % name)
        print('---------------')

        self.setResult(True)
        self.close()
        self.sig_new_project.emit(fname)

    def reset_UI(self):
        self.setResult(False)

        self.name.clear()
        self.author.clear()

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)
        self.date = QLabel('%02d/%02d/%d %02d:%02d' % now)

        self.lat_spinbox.setValue(0)
        self.lon_spinbox.setValue(0)

    def show(self):
        super(NewProject, self).show()
        self.raise_()

        qr = self.frameGeometry()
        if self.parentWidget():
            wp = self.parentWidget().frameGeometry().width()
            hp = self.parentWidget().frameGeometry().height()
            cp = self.parentWidget().mapToGlobal(QPoint(wp/2., hp/2.))
        else:
            cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setFixedSize(self.size())


if __name__ == '__main__':
    import sys
    from gwhat.utils.qthelpers import create_qapplication

    f = 'C:/Users/jnsebgosselin/Desktop/Project4Testing/Project4Testing.what'

    app = create_qapplication()

    pm = ProjetManager(projet=None)
    pm.show()

    dm = DataManager(pm=pm)
    dm.show()

    sys.exit(app.exec_())
