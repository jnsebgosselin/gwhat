# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports
import os.path as osp

# ---- Third party imports
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

# ---- Local imports
from gwhat.config.ospath import (
    get_select_file_dialog_dir, set_select_file_dialog_dir)


class SaveFileMixin(object):

    @property
    def dialog_dir(self):
        return get_select_file_dialog_dir()

    def set_dialog_dir(self, dirname):
        """Set the default dialog directory to dirname."""
        set_select_file_dialog_dir(dirname)

    def select_savefilename(self, title, fname, ffmat):
        """Open a dialog where the user can select a file name."""
        fname, ftype = QFileDialog.getSaveFileName(self, title, fname, ffmat)
        if fname:
            ftype = ftype.replace('*', '')
            fname = fname if fname.endswith(ftype) else fname + ftype
            self.set_dialog_dir(osp.dirname(fname))
            return fname
        else:
            return None

    def show_permission_error(self):
        """
        Show a warning message telling the user that the saving operation
        has failed.
        """
        QApplication.restoreOverrideCursor()
        msg = "The file is in use by another application or user."
        QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
