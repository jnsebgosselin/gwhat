# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Imports: Standard Libraries

import os
import os.path as osp
import requests
import zipfile
import io


# ---- Imports: Third Parties

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (QLabel, QDateTimeEdit, QCheckBox, QPushButton,
                             QApplication, QSpinBox, QAbstractSpinBox,
                             QGridLayout, QDoubleSpinBox, QFrame, QWidget,
                             QDesktopWidget, QMessageBox, QFileDialog,
                             QComboBox, QLayout)

from xlrd.xldate import xldate_from_date_tuple
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


# ---- Imports: Local

import gwhat.common.widgets as myqt
from gwhat.widgets.layout import VSep, HSep
from gwhat.widgets.buttons import LangToolButton, OnOffToolButton
from gwhat.common import StyleDB
from gwhat.utils import icons
from gwhat.utils.icons import QToolButtonNormal, QToolButtonSmall
from gwhat.utils.dates import qdate_from_xldate
from gwhat import brf_mod as bm
from gwhat.brf_mod import __install_dir__
from gwhat.brf_mod.kgs_plot import BRFFigure
from gwhat import __rootdir__

mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Arial']})


class KGSBRFInstaller(myqt.QFrameLayout):
    """
    A simple widget to download the kgs_brf program and install it in the
    proper directory.
    http://www.kgs.ku.edu/HighPlains/OHP/index_program/brf.html
    """

    sig_kgs_brf_installed = QSignal(str)

    def __init__(self, parent=None):
        super(KGSBRFInstaller, self).__init__(parent)

        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.install_btn = QPushButton("Install")
        self.install_btn.clicked.connect(self.install_kgsbrf)

        self.addWidget(self.install_btn, 1, 1)
        self.setRowStretch(0, 100)
        self.setRowStretch(self.rowCount(), 100)
        self.setColumnStretch(0, 100)
        self.setColumnStretch(self.columnCount(), 100)

    @property
    def install_dir(self):
        """Path to the installation folder."""
        return __install_dir__

    @property
    def kgs_brf_name(self):
        """Name of the kgs_brf binary executable."""
        return "kgs_brf.exe"

    @property
    def kgs_brf_path(self):
        """Path to the kgs_brf binary executable."""
        return os.path.join(self.install_dir, self.kgs_brf_name)

    def kgsbrf_is_installed(self):
        """Returns whether kgs_brf is installed or not."""
        return os.path.exists(self.kgs_brf_path)

    def install_kgsbrf(self):
        """Download and install the kgs_brf software."""
        if os.name != 'nt':
            url_t = "https://github.com/jnsebgosselin/gwhat/issues"
            msg = ("This feature is currently not supported for your"
                   " operating system. Please open a ticket in our"
                   " <a href=\"%s\">Issues Tracker</a>.") % url_t
            QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
            return

        print("Installing KGS_BRF software...", end=" ")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        url = "http://www.kgs.ku.edu/HighPlains/OHP/index_program/KGS_BRF.zip"
        request = requests.get(url)
        zfile = zipfile.ZipFile(io.BytesIO(request .content))

        if not os.path.exists(self.install_dir):
            os.makedirs(self.install_dir)

        with open(self.kgs_brf_path, 'wb') as f:
            f.write(zfile.read(self.kgs_brf_name))

        if self.kgsbrf_is_installed():
            self.sig_kgs_brf_installed.emit(self.install_dir)
            self.close()
            print("done")
        else:
            print("failed")
        QApplication.restoreOverrideCursor()


class BRFManager(myqt.QFrameLayout):
    sig_brfperiod_changed = QSignal(list)

    def __init__(self, wldset=None, parent=None):
        super(BRFManager, self).__init__(parent)

        self.viewer = BRFViewer(wldset, parent)
        self.kgs_brf_installer = None
        self.__initGUI__()

    def __initGUI__(self):
        self.setContentsMargins(10, 10, 10, 10)

        # ---- Detrend and Correct Options
        self.baro_spinbox = myqt.QDoubleSpinBox(100, 0, show_buttons=True)
        self.baro_spinbox.setRange(0, 9999)
        self.baro_spinbox.setKeyboardTracking(True)

        self.earthtides_spinbox = myqt.QDoubleSpinBox(
            100, 0, show_buttons=True)
        self.earthtides_spinbox.setRange(0, 9999)
        self.earthtides_spinbox.setKeyboardTracking(True)

        self.earthtides_cbox = QCheckBox('Nbr of ET lags :')
        self.earthtides_cbox.setChecked(True)
        self.earthtides_cbox.stateChanged.connect(
            lambda: self.earthtides_spinbox.setEnabled(
                self.earthtides_cbox.isChecked()))

        self.detrend_waterlevels_cbox = QCheckBox('Detrend water levels')
        self.detrend_waterlevels_cbox.setChecked(True)

        # Setup options layout.
        options_layout = QGridLayout()
        options_layout.addWidget(QLabel('Nbr of BP lags :'), 0, 0)
        options_layout.addWidget(self.baro_spinbox, 0, 2)
        options_layout.addWidget(self.earthtides_cbox, 1, 0)
        options_layout.addWidget(self.earthtides_spinbox, 1, 2)
        options_layout.addWidget(self.detrend_waterlevels_cbox, 2, 0, 1, 3)
        options_layout.setColumnStretch(1, 100)
        options_layout.setContentsMargins(0, 0, 0, 0)

        # ---- BRF date range
        self.date_start_edit = QDateTimeEdit()
        self.date_start_edit.setCalendarPopup(True)
        self.date_start_edit.setDisplayFormat('dd/MM/yyyy hh:mm')
        self.date_start_edit.dateChanged.connect(
            lambda: self.sig_brfperiod_changed.emit(self.get_brfperiod()))
        self.date_start_edit.dateChanged.connect(
            lambda: self.wldset.save_brfperiod(self.get_brfperiod()))

        self.date_end_edit = QDateTimeEdit()
        self.date_end_edit.setCalendarPopup(True)
        self.date_end_edit.setDisplayFormat('dd/MM/yyyy hh:mm')
        self.date_end_edit.dateChanged.connect(
            lambda: self.sig_brfperiod_changed.emit(self.get_brfperiod()))
        self.date_end_edit.dateChanged.connect(
            lambda: self.wldset.save_brfperiod(self.get_brfperiod()))

        self.btn_seldata = OnOffToolButton('select_range', size='small')
        self.btn_seldata.setToolTip("Select a BRF calculation period with "
                                    "the mouse cursor on the graph.")

        # Setup BRF date range layout.
        daterange_layout = QGridLayout()
        daterange_layout.addWidget(QLabel('BRF Start :'), 0, 0)
        daterange_layout.addWidget(self.date_start_edit, 0, 2)
        daterange_layout.addWidget(QLabel('BRF End :'), 1, 0)
        daterange_layout.addWidget(self.date_end_edit, 1, 2)
        daterange_layout.setColumnStretch(1, 100)
        daterange_layout.setContentsMargins(0, 0, 0, 0)

        seldata_layout = QGridLayout()
        seldata_layout.addWidget(self.btn_seldata, 0, 0)
        seldata_layout.setRowStretch(1, 100)
        seldata_layout.setContentsMargins(0, 0, 0, 0)

        # ---- Toolbar
        btn_comp = QPushButton('Compute BRF')
        btn_comp.clicked.connect(self.calc_brf)
        btn_comp.setFocusPolicy(Qt.NoFocus)

        self.btn_show = QToolButtonSmall(icons.get_icon('search'))
        self.btn_show.clicked.connect(self.viewer.show)

        # ---- Main Layout
        self.addLayout(daterange_layout, 0, 0)
        self.addLayout(seldata_layout, 0, 1)
        self.setRowMinimumHeight(1, 15)
        self.addLayout(options_layout, 2, 0)
        self.setRowMinimumHeight(3, 15)
        self.setRowStretch(3, 100)
        self.addWidget(btn_comp, 4, 0)
        self.addWidget(self.btn_show, 4, 1)
        self.setColumnStretch(0, 100)

        # ---- Install Panel
        if not KGSBRFInstaller().kgsbrf_is_installed():
            self.__install_kgs_brf_installer()

    # ---- Properties

    @property
    def nlag_baro(self):
        """Return the number of lags to use for barometric correction."""
        return self.baro_spinbox.value()

    @property
    def nlag_earthtides(self):
        """Return the number of lags to use for Earth tides correction."""
        return (self.earthtides_spinbox.value() if
                self.earthtides_cbox.isChecked() else -1)

    @property
    def detrend_waterlevels(self):
        return self.detrend_waterlevels_cbox.isChecked()

    @property
    def correct_waterlevels(self):
        return True

    def get_brfperiod(self):
        """
        Get the period over which the BRF would be evaluated as a list of
        two numerical Excel date values.
        """
        y, m, d = self.date_start_edit.date().getDate()
        dstart = xldate_from_date_tuple((y, m, d), 0)

        y, m, d = self.date_end_edit.date().getDate()
        dend = xldate_from_date_tuple((y, m, d), 0)

        return [dstart, dend]

    def set_brfperiod(self, period):
        """
        Set the value of the date_start_edit and date_end_edit widgets used to
        define the period over which the BRF is evaluated. Also save the
        period to the waterlevel dataset.
        """
        period = np.sort(period).tolist()
        widgets = (self.date_start_edit, self.date_end_edit)
        for xldate, widget in zip(period, widgets):
            if xldate is not None:
                widget.blockSignals(True)
                widget.setDate(qdate_from_xldate(xldate))
                widget.blockSignals(False)
        self.wldset.save_brfperiod(period)

    # ---- KGS BRF installer
    def __install_kgs_brf_installer(self):
        """
        Installs a KGSBRFInstaller that overlays the whole brf tool
        layout until the KGS_BRF program is installed correctly.
        """
        self.kgs_brf_installer = KGSBRFInstaller()
        self.kgs_brf_installer.sig_kgs_brf_installed.connect(
                self.__uninstall_kgs_brf_installer)
        self.addWidget(self.kgs_brf_installer, 0, 0,
                       self.rowCount(), self.columnCount())

    def __uninstall_kgs_brf_installer(self):
        """
        Uninstall the KGSBRFInstaller after the KGS_BRF program has been
        installed properly.
        """
        self.kgs_brf_installer.sig_kgs_brf_installed.disconnect()
        self.kgs_brf_installer = None

    def set_wldset(self, wldset):
        """Set the namespace for the wldset in the widget."""
        self.wldset = wldset
        self.viewer.set_wldset(wldset)
        self.btn_seldata.setAutoRaise(True)
        self.setEnabled(wldset is not None)
        if wldset is not None:
            self.set_daterange((self.wldset['Time'][0],
                                self.wldset['Time'][-1]))

            # Set the period over which the BRF would be evaluated.
            saved_brfperiod = wldset.get_brfperiod()
            self.set_brfperiod(
                (saved_brfperiod[0] or np.floor(self.wldset['Time'][0]),
                 saved_brfperiod[1] or np.floor(self.wldset['Time'][-1])
                 ))

    def set_daterange(self, daterange):
        """
        Set the minimum and maximum value of date_start_edit and date_end_edit
        widgets from the specified list of Excel numeric dates.
        """
        for widget in (self.date_start_edit, self.date_end_edit):
            widget.blockSignals(True)
            widget.setMinimumDate(qdate_from_xldate(daterange[0]))
            widget.setMaximumDate(qdate_from_xldate(daterange[1]))
            widget.blockSignals(False)

    def calc_brf(self):
        """Prepare the data, calcul the brf, and save and plot the results."""

        # Prepare the datasets.
        well = self.wldset['Well']

        brfperiod = self.get_brfperiod()
        t1 = min(brfperiod)
        i1 = np.where(self.wldset['Time'] >= t1)[0][0]
        t2 = max(brfperiod)
        i2 = np.where(self.wldset['Time'] <= t2)[0][-1]

        time = np.copy(self.wldset['Time'][i1:i2+1])
        wl = np.copy(self.wldset['WL'][i1:i2+1])
        bp = np.copy(self.wldset['BP'][i1:i2+1])
        if len(bp) == 0:
            msg = ("The barometric response function cannot be computed"
                   " because the currently selected water level dataset does"
                   " not contain any barometric data for the selected period.")
            QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
            return
        et = np.copy(self.wldset['ET'][i1:i2+1])
        if len(et) == 0:
            et = np.zeros(len(wl))

        # Fill the gaps in the dataset.
        dt = np.min(np.diff(time))
        tc = np.arange(t1, t2+dt/2, dt)
        if len(tc) != len(time):
            print('Filling gaps in data with linear interpolation.')
            indx = np.where(~np.isnan(wl))[0]
            wl = np.interp(tc, time[indx], wl[indx])

            indx = np.where(~np.isnan(bp))[0]
            bp = np.interp(tc, time[indx], bp[indx])

            indx = np.where(~np.isnan(et))[0]
            et = np.interp(tc, time[indx], et[indx])

            time = tc

        QApplication.setOverrideCursor(Qt.WaitCursor)
        print('calculating the BRF')

        bm.produce_BRFInputtxt(well, time, wl, bp, et)
        msg = ("Not enough data. Try enlarging the selected period "
               "or reduce the number of BP lags.")
        if self.nlag_baro >= len(time) or self.nlag_earthtides >= len(time):
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
            return

        bm.produce_par_file(
            self.nlag_baro, self.nlag_earthtides, self.detrend_waterlevels,
            self.correct_waterlevels)
        bm.run_kgsbrf()

        try:
            lag, A, err = bm.read_brf_output()
            date_start = self.date_start_edit.date().getDate()
            date_end = self.date_end_edit.date().getDate()
            self.wldset.save_brf(lag, A, err, date_start, date_end)
            self.viewer.new_brf_added()
            self.viewer.show()
            QApplication.restoreOverrideCursor()
        except Exception:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
            return


class BRFViewer(QWidget):
    """
    Window that is used to show all the results produced with for the
    currently selected water level dataset.
    """

    def __init__(self, wldset=None, parent=None):
        super(BRFViewer, self).__init__(parent)
        self.__save_ddir = osp.dirname(__rootdir__)

        self.setWindowTitle('BRF Results Viewer')
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowFlags(Qt.Window |
                            Qt.CustomizeWindowHint |
                            Qt.WindowMinimizeButtonHint |
                            Qt.WindowCloseButtonHint)

        self.__initGUI__()
        self.set_wldset(wldset)

    def __initGUI__(self):

        # ---- Navigator

        self.btn_prev = QToolButtonNormal(icons.get_icon('go_previous'))
        self.btn_prev.clicked.connect(self.navigate_brf)

        self.btn_next = QToolButtonNormal(icons.get_icon('go_next'))
        self.btn_next.clicked.connect(self.navigate_brf)

        self.current_brf = QSpinBox()
        self.current_brf.setRange(0, 99)
        self.current_brf.setAlignment(Qt.AlignCenter)
        self.current_brf.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.current_brf.setCorrectionMode(
                QAbstractSpinBox.CorrectToNearestValue)
        self.current_brf.valueChanged.connect(self.navigate_brf)
        self.current_brf.setValue(0)

        self.total_brf = QLabel('/ 0')

        # ---- Language button

        self.btn_language = LangToolButton()
        self.btn_language.setToolTip(
            "Set the language of the text shown in the graph.")
        self.btn_language.sig_lang_changed.connect(self.plot_brf)
        self.btn_language.setIconSize(icons.get_iconsize('normal'))

        # ---- Toolbar

        # Generate the buttons :

        self.btn_del = QToolButtonNormal(icons.get_icon('clear_search'))
        self.btn_del.setToolTip('Delete current BRF results')
        self.btn_del.clicked.connect(self.del_brf)

        self.btn_del_all = QToolButtonNormal(icons.get_icon('close_all'))
        self.btn_del_all.setToolTip(
            'Delete all BRF results for the current water level dataset.')
        self.btn_del_all.clicked.connect(self.del_all_brf)

        self.btn_save = btn_save = QToolButtonNormal(icons.get_icon('save'))
        btn_save.setToolTip('Save current BRF graph...')
        btn_save.clicked.connect(self.select_savefig_path)

        self.btn_setp = QToolButtonNormal(icons.get_icon('page_setup'))
        self.btn_setp.setToolTip('Show graph layout parameters...')
        self.btn_setp.clicked.connect(self.toggle_graphpannel)

        # Generate the layout :

        self.tbar = myqt.QFrameLayout()

        buttons = [btn_save, self.btn_del,  self.btn_del_all, VSep(),
                   self.btn_prev, self.current_brf, self.total_brf,
                   self.btn_next, VSep(), self.btn_setp, self.btn_language]

        for btn in buttons:
            if isinstance(btn, QLayout):
                self.tbar.addLayout(btn, 1, self.tbar.columnCount())
            else:
                self.tbar.addWidget(btn, 1, self.tbar.columnCount())

        row = self.tbar.columnCount()
        self.tbar.addWidget(HSep(), 0, 0, 1, row+1)
        self.tbar.setColumnStretch(row, 100)
        self.tbar.setContentsMargins(10, 0, 10, 10)  # (l, t, r, b)

        # ---- Graph Canvas

        self.fig_frame = QFrame()
        self.fig_frame.setFrameStyle(StyleDB().frame)
        self.fig_frame.setObjectName("figframe")
        self.fig_frame.setStyleSheet("#figframe {background-color:white;}")

        self.brf_canvas = FigureCanvasQTAgg(BRFFigure())

        fflay = QGridLayout(self.fig_frame)
        fflay.setContentsMargins(0, 0, 0, 0)   # (left, top, right, bottom)
        fflay.addWidget(self.tbar, 1, 0)
        fflay.addWidget(self.brf_canvas, 0, 0)

        # ---- Graph Options Panel

        self.graph_opt_panel = BRFOptionsPanel()
        self.graph_opt_panel.sig_graphconf_changed.connect(self.plot_brf)

        # ---- Main Layout

        ml = QGridLayout(self)

        ml.addWidget(self.fig_frame, 0, 2)
        ml.addWidget(self.graph_opt_panel, 0, 3)

        ml.setColumnStretch(1, 100)

    # ---- Toolbar Handlers

    def toggle_graphpannel(self):
        if self.graph_opt_panel.isVisible() is True:
            # Hide the panel.
            self.graph_opt_panel.setVisible(False)
            self.btn_setp.setAutoRaise(True)
            self.btn_setp.setToolTip('Show graph layout parameters...')

            w = self.size().width() - self.graph_opt_panel.size().width()
            self.setFixedWidth(w)
        else:
            # Show the panel.
            self.graph_opt_panel.setVisible(True)
            self.btn_setp.setAutoRaise(False)
            self.btn_setp.setToolTip('Hide graph layout parameters...')

            w = self.size().width() + self.graph_opt_panel.size().width()
            self.setFixedWidth(w)

    def navigate_brf(self):
        if self.sender() == self.btn_prev:
            cur_num = self.current_brf.value() - 1
        elif self.sender() == self.btn_next:
            cur_num = self.current_brf.value() + 1
        elif self.sender() == self.current_brf:
            cur_num = self.current_brf.value()
        self.current_brf.setValue(cur_num)

        self.update_brfnavigate_state()

    def del_brf(self):
        """Delete the graph and data of the currently selected result."""
        index = self.current_brf.value()-1
        name = self.wldset.get_brfname_at(index)
        self.wldset.del_brf(name)
        self.update_brfnavigate_state()

    def del_all_brf(self):
        """Delete all the graphs and BRF results for the current dataset."""
        msg = ("Do you want to delete all BRF results that were evaluated "
               "for dataset <i>{}</i>?"
               "<br><br>"
               "All data will be lost permanently."
               ).format(self.wldset.name)
        btn = QMessageBox.Yes | QMessageBox.No
        reply = QMessageBox.question(self, 'Delete all BRF results', msg, btn)

        if reply == QMessageBox.Yes:
            for name in self.wldset.saved_brf():
                self.wldset.del_brf(name)
            self.update_brfnavigate_state()

    def new_brf_added(self):
        self.current_brf.setMaximum(self.wldset.brf_count())
        self.current_brf.setValue(self.wldset.brf_count())
        self.update_brfnavigate_state()

    def update_brfnavigate_state(self):
        count = self.wldset.brf_count()
        self.total_brf.setText('/ %d' % count)

        self.current_brf.setMinimum(min(count, 1))
        self.current_brf.setMaximum(count)
        curnt = self.current_brf.value()

        self.tbar.setEnabled(count > 0)
        self.btn_prev.setEnabled(curnt > 1)
        self.btn_next.setEnabled(curnt < count)
        self.btn_del.setEnabled(count > 0)

        self.plot_brf()

    def select_savefig_path(self):
        """
        Opens a dialog to select a file path where to save the brf figure.
        """
        ddir = osp.join(self.__save_ddir,
                        'brf_%s' % self.wldset['Well'])

        dialog = QFileDialog()
        fname, ftype = dialog.getSaveFileName(
                self, "Save Figure", ddir, '*.pdf;;*.svg')
        ftype = ftype.replace('*', '')
        if fname:
            self.__save_ddir = osp.dirname(fname)
            if not fname.endswith(ftype):
                fname = fname + ftype
            self.save_brf_fig(fname)

    def save_brf_fig(self, fname):
        """Saves the current BRF figure to fname."""
        self.brf_canvas.figure.savefig(fname)

    # ---- Others

    def set_wldset(self, wldset):
        self.wldset = wldset
        if wldset is None:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            self.update_brfnavigate_state()

    def plot_brf(self):
        self.brf_canvas.figure.set_language(self.btn_language.language)
        if self.wldset.brf_count() == 0:
            self.brf_canvas.figure.empty_BRF()
        else:
            name = self.wldset.get_brfname_at(self.current_brf.value()-1)
            lag, A, err, date_start, date_end = self.wldset.get_brf(name)
            well = self.wldset['Well']

            if self.graph_opt_panel.show_ebar is False:
                err = []
            msize = self.graph_opt_panel.markersize
            draw_line = self.graph_opt_panel.draw_line

            ymin = self.graph_opt_panel.ymin
            ymax = self.graph_opt_panel.ymax
            yscale = self.graph_opt_panel.yscale

            xmin = self.graph_opt_panel.xmin
            xmax = self.graph_opt_panel.xmax
            xscale = self.graph_opt_panel.xscale

            time_units = self.graph_opt_panel.time_units

            date0 = '%02d/%02d/%04d' % (date_start[2],
                                        date_start[1],
                                        date_start[0])

            date1 = '%02d/%02d/%04d' % (date_end[2],
                                        date_end[1],
                                        date_end[0])

            self.brf_canvas.figure.plot_BRF(
                    lag, A, err, date0, date1, well, msize, draw_line,
                    [ymin, ymax], [xmin, xmax], time_units, xscale, yscale)
        self.brf_canvas.draw()

    def show(self):
        super(BRFViewer, self).show()
        qr = self.frameGeometry()
        if self.parentWidget():
            parent = self.parentWidget()

            wp = parent.frameGeometry().width()
            hp = parent.frameGeometry().height()
            cp = parent.mapToGlobal(QPoint(wp/2, hp/2))
        else:
            cp = QDesktopWidget().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.fig_frame.setFixedSize(self.fig_frame.size())
        self.setFixedSize(self.size())

        self.raise_()
        if self.windowState() == Qt.WindowMinimized:
            # Window is minimised. Restore it.
            self.setWindowState(Qt.WindowNoState)


class BRFOptionsPanel(QWidget):
    """A Panel where the options to plot the graph are displayed."""

    sig_graphconf_changed = QSignal()

    def __init__(self, parent=None):
        super(BRFOptionsPanel, self).__init__(parent)
        self.__initGUI__()
        self.setVisible(False)

    def __initGUI__(self):
        # ---- Line and Markers Style Widgets

        self._errorbar = QCheckBox('Show error bars')
        self._errorbar.setCheckState(Qt.Checked)
        self._errorbar.stateChanged.connect(self._graphconf_changed)

        self._drawline = QCheckBox('Draw line')
        self._drawline.setCheckState(Qt.Unchecked)
        self._drawline.stateChanged.connect(self._graphconf_changed)

        self._markersize = {}
        self._markersize['label'] = QLabel('Marker size :')
        self._markersize['widget'] = QSpinBox()
        self._markersize['widget'].setValue(5)
        self._markersize['widget'].setRange(0, 25)
        self._markersize['widget'].valueChanged.connect(
                self._graphconf_changed)

        # ---- Y-Axis Options Widgets

        self._ylim = {}
        self._ylim['min'] = QDoubleSpinBox()
        self._ylim['min'].setValue(0)
        self._ylim['min'].setDecimals(1)
        self._ylim['min'].setSingleStep(0.1)
        self._ylim['min'].setRange(-10, 10)
        self._ylim['min'].setEnabled(True)
        self._ylim['min'].valueChanged.connect(self._graphconf_changed)
        self._ylim['max'] = QDoubleSpinBox()
        self._ylim['max'].setValue(1)
        self._ylim['max'].setDecimals(1)
        self._ylim['max'].setSingleStep(0.1)
        self._ylim['max'].setRange(-10, 10)
        self._ylim['max'].setEnabled(True)
        self._ylim['max'].valueChanged.connect(self._graphconf_changed)
        self._ylim['scale'] = QDoubleSpinBox()
        self._ylim['scale'].setValue(0.2)
        self._ylim['scale'].setDecimals(2)
        self._ylim['scale'].setSingleStep(0.05)
        self._ylim['scale'].setRange(0.01, 1)
        self._ylim['scale'].setEnabled(True)
        self._ylim['scale'].valueChanged.connect(self._graphconf_changed)
        self._ylim['auto'] = QCheckBox('')
        self._ylim['auto'].setCheckState(Qt.Checked)
        self._ylim['auto'].stateChanged.connect(self.axis_autocheck_changed)

        # ---- X-Axis Options Widgets

        self._xlim = {}
        self._xlim['units'] = QComboBox()
        self._xlim['units'].addItems(['Hours', 'Days'])
        self._xlim['units'].setCurrentIndex(1)
        self._xlim['units'].currentIndexChanged.connect(
                self.time_units_changed)
        self._xlim['min'] = QSpinBox()
        self._xlim['min'].setValue(0)
        self._xlim['min'].setSingleStep(1)
        self._xlim['min'].setRange(0, 9999)
        self._xlim['min'].setEnabled(True)
        self._xlim['min'].valueChanged.connect(self._graphconf_changed)
        self._xlim['max'] = QSpinBox()
        self._xlim['max'].setValue(1)
        self._xlim['max'].setSingleStep(1)
        self._xlim['max'].setRange(1, 9999)
        self._xlim['max'].setEnabled(True)
        self._xlim['max'].valueChanged.connect(self._graphconf_changed)
        self._xlim['scale'] = QDoubleSpinBox()
        self._xlim['scale'].setValue(1)
        self._xlim['scale'].setDecimals(1)
        self._xlim['scale'].setSingleStep(0.1)
        self._xlim['scale'].setRange(0.1, 99)
        self._xlim['scale'].setEnabled(True)
        self._xlim['scale'].valueChanged.connect(self._graphconf_changed)
        self._xlim['auto'] = QCheckBox('')
        self._xlim['auto'].setCheckState(Qt.Checked)
        self._xlim['auto'].stateChanged.connect(self.axis_autocheck_changed)

        self.axis_autocheck_changed()

        # ---- Axis Options Layout

        axlayout = QGridLayout()

        row = 0
        axlayout.addWidget(QLabel('y-axis limits:'), 0, 0, 1, 2)
        row += 1
        axlayout.addWidget(QLabel('   Minimum :'), row, 0)
        axlayout.addWidget(self._ylim['min'], row, 1)
        row += 1
        axlayout.addWidget(QLabel('   Maximum :'), row, 0)
        axlayout.addWidget(self._ylim['max'], row, 1)
        row += 1
        axlayout.addWidget(QLabel('   Scale :'), row, 0)
        axlayout.addWidget(self._ylim['scale'], row, 1)
        row += 1
        axlayout.addWidget(QLabel('   Auto :'), row, 0)
        axlayout.addWidget(self._ylim['auto'], row, 1)
        row += 1
        axlayout.setRowMinimumHeight(row, 15)
        row += 1
        axlayout.addWidget(QLabel('x-axis limits:'), row, 0, 1, 2)
        row += 1
        axlayout.addWidget(QLabel('   Time units :'), row, 0)
        axlayout.addWidget(self._xlim['units'], row, 1)
        row += 1
        axlayout.addWidget(QLabel('   Minimum :'), row, 0)
        axlayout.addWidget(self._xlim['min'], row, 1)
        row += 1
        axlayout.addWidget(QLabel('   Maximum :'), row, 0)
        axlayout.addWidget(self._xlim['max'], row, 1)
        row += 1
        axlayout.addWidget(QLabel('   Scale :'), row, 0)
        axlayout.addWidget(self._xlim['scale'], row, 1)
        row += 1
        axlayout.addWidget(QLabel('   Auto :'), row, 0)
        axlayout.addWidget(self._xlim['auto'], row, 1)

        axlayout.setColumnStretch(3, 100)
        axlayout.setContentsMargins(0, 0, 0, 0)  # (left, top, right, bottom)

        # ---- Graph Panel Layout

        layout = QGridLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)  # (l, t, r, b)

        row = 0
        layout.addWidget(self._errorbar, row, 1, 1, 2)
        row += 1
        layout.addWidget(self._drawline, row, 1, 1, 2)
        row += 1
        layout.addWidget(self._markersize['label'], row, 1)
        layout.addWidget(self._markersize['widget'], row, 2)
        row += 1
        layout.addWidget(HSep(), row, 1, 1, 2)
        row += 1
        layout.addLayout(axlayout, row, 1, 1, 2)
        row += 1
        layout.setRowMinimumHeight(row, 15)
        layout.setRowStretch(row, 100)

    def _graphconf_changed(self):
        """
        Emits a signal to indicate that the graph configuration has changed.
        """
        self.sig_graphconf_changed.emit()

    # ---- Graph Panel Properties

    @property
    def time_units(self):
        if self._xlim['auto'].checkState() == Qt.Checked:
            return 'auto'
        else:
            return self._xlim['units'].currentText().lower()

    @property
    def xmin(self):
        if self._xlim['auto'].checkState() == Qt.Checked:
            return None
        else:
            if self.time_units == 'hours':
                return self._xlim['min'].value()/24
            else:
                return self._xlim['min'].value()

    @property
    def xmax(self):
        if self._xlim['auto'].checkState() == Qt.Checked:
            return None
        else:
            if self.time_units == 'hours':
                return self._xlim['max'].value()/24
            else:
                return self._xlim['max'].value()

    @property
    def xscale(self):
        if self._xlim['auto'].checkState() == Qt.Checked:
            return None
        else:
            if self.time_units == 'hours':
                return self._xlim['scale'].value()/24
            else:
                return self._xlim['scale'].value()

    @property
    def ymin(self):
        if self._ylim['auto'].checkState() == Qt.Checked:
            return None
        else:
            return self._ylim['min'].value()

    @property
    def ymax(self):
        if self._ylim['auto'].checkState() == Qt.Checked:
            return None
        else:
            return self._ylim['max'].value()

    @property
    def yscale(self):
        if self._ylim['auto'].checkState() == Qt.Checked:
            return None
        else:
            return self._ylim['scale'].value()

    @property
    def show_ebar(self):
        return self._errorbar.checkState() == Qt.Checked

    @property
    def draw_line(self):
        return self._drawline.checkState() == Qt.Checked

    @property
    def markersize(self):
        return self._markersize['widget'].value()

    # ---- Handlers

    def time_units_changed(self):
        """ Handles when the time_units combobox selection changes."""
        for xlim in [self._xlim['min'], self._xlim['max'],
                     self._xlim['scale']]:
            xlim.blockSignals(True)
            if self._xlim['units'].currentText() == 'Hours':
                xlim.setValue(xlim.value()*24)
            elif self._xlim['units'].currentText() == 'Days':
                xlim.setValue(xlim.value()/24)
            xlim.blockSignals(False)

        self._graphconf_changed()

    def axis_autocheck_changed(self):
        """
        Handles when the Auto checkbox state change for the
        limits of the y-axis or the x-axis.
        """
        self._ylim['min'].setEnabled(not self._ylim['auto'].isChecked())
        self._ylim['max'].setEnabled(not self._ylim['auto'].isChecked())
        self._ylim['scale'].setEnabled(not self._ylim['auto'].isChecked())

        self._xlim['units'].setEnabled(not self._xlim['auto'].isChecked())
        self._xlim['min'].setEnabled(not self._xlim['auto'].isChecked())
        self._xlim['max'].setEnabled(not self._xlim['auto'].isChecked())
        self._xlim['scale'].setEnabled(not self._xlim['auto'].isChecked())

        self._graphconf_changed()


# %% if __name__ == "__main__"

if __name__ == "__main__":
    import gwhat.projet.reader_projet as prd
    import sys
    # projet = prd.ProjetReader("C:/Users/jsgosselin/GWHAT/Projects/Example/"
                                # "Example.gwt")
    projet = prd.ProjetReader("C:/Users/User/gwhat/gwhat/"
                              "tests/@ new-prô'jèt!/@ new-prô'jèt!.gwt")
    wldset = projet.get_wldset(projet.wldsets[0])

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setPointSize(11)
    ft.setFamily('Segoe UI')
    app.setFont(ft)

    brfwin = BRFManager(None)
    brfwin.show()
    brfwin.set_wldset(wldset)
    brfwin.viewer.show()
    brfwin.viewer.toggle_graphpannel()

    sys.exit(app.exec_())

#    plt.close('all')
    # produce_par_file()
    # run_kgsbrf()
    # load_BRFOutput(show_ebar=True, msize=5, draw_line=False)
#    plt.show()
