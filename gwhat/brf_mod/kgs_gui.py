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
import requests
import zipfile
import io


# ---- Third party imports
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import (
    QLabel, QDateTimeEdit, QCheckBox, QPushButton, QApplication, QSpinBox,
    QAbstractSpinBox, QGridLayout, QDoubleSpinBox, QFrame, QWidget,
    QMessageBox, QFileDialog, QComboBox, QDialog, QGroupBox, QToolButton,
    QToolBar)

from xlrd.xldate import xldate_from_datetime_tuple, xldate_as_datetime
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


# ---- Local imports
from gwhat.hydrocalc.api import WLCalcTool, wlcalcmethod
from gwhat.hydrocalc.axeswidgets import WLCalcVSpanSelector
from gwhat.widgets.buttons import OnOffPushButton
from gwhat.widgets.layout import HSep
from gwhat.config.gui import FRAME_SYLE
from gwhat.utils import icons
from gwhat.utils.icons import QToolButtonNormal, get_icon
from gwhat.utils.dates import qdatetime_from_xldate
from gwhat.utils.qthelpers import create_toolbar_stretcher
from gwhat import brf_mod as bm
from gwhat.brf_mod import __install_dir__
from gwhat.brf_mod.kgs_plot import BRFFigure
from gwhat import __rootdir__

mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Arial']})


class KGSBRFInstaller(QFrame):
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

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.install_btn, 1, 1)
        layout.setRowStretch(0, 100)
        layout.setRowStretch(layout.rowCount(), 100)
        layout.setColumnStretch(0, 100)
        layout.setColumnStretch(layout.columnCount(), 100)

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
        url = "https://www.kgs.ku.edu/HighPlains/OHP/index_program/KGS_BRF.zip"
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


class BRFManager(WLCalcTool):
    __toolname__ = 'brf'
    __tooltitle__ = 'BRF'
    __tooltip__ = ("A tool to evaluate the barometric "
                   "response function of wells.")

    def __init__(self, wldset=None, parent=None):
        super().__init__(parent)
        # Whether it is the first time showEvent is called.
        self._first_show_event = True

        # The WLCalc instance to which this tool is registered.
        self.wlcalc = None

        # The water level dataset currently registered to this tool.
        self.wldset = None

        self._bp_and_et_lags_are_linked = False
        self._previous_toggled_navig_and_select_tool = None
        self.kgs_brf_installer = None

        self.viewer = BRFViewer(wldset, parent)
        self.viewer.set_language(self.get_option('graphs_labels_language'))
        if self.get_option('graph_opt_panel_is_visible', False):
            self.viewer.toggle_graphpannel()
        self.viewer.sig_import_params_in_manager_request.connect(
            self.import_current_viewer_brf_parameters)

        self.setup()

    def setup(self):
        self.setContentsMargins(10, 10, 10, 10)

        # Detrend and Correct Options
        self.baro_spinbox = QSpinBox()
        self.baro_spinbox.setRange(0, 9999)
        self.baro_spinbox.setValue(self.get_option('nbr_of_baro_lags'))
        self.baro_spinbox.setKeyboardTracking(True)
        self.baro_spinbox.valueChanged.connect(
            lambda value: self._handle_lag_value_changed(self.baro_spinbox))

        self.earthtides_spinbox = QSpinBox()
        self.earthtides_spinbox.setRange(0, 9999)
        self.earthtides_spinbox.setValue(
            self.get_option('nbr_of_earthtides_lags'))
        self.earthtides_spinbox.setKeyboardTracking(True)
        self.earthtides_spinbox.setEnabled(
            self.get_option('compute_with_earthtides'))
        self.earthtides_spinbox.valueChanged.connect(
            lambda value: self._handle_lag_value_changed(
                self.earthtides_spinbox))

        self.earthtides_cbox = QCheckBox('No. of ET lags :')
        self.earthtides_cbox.setChecked(
            self.get_option('compute_with_earthtides'))
        self.earthtides_cbox.toggled.connect(
            lambda: self.earthtides_spinbox.setEnabled(
                self.earthtides_cbox.isChecked()))

        self._link_lags_button = QToolButton()
        self._link_lags_button.setAutoRaise(True)
        self._link_lags_button.setFixedWidth(24)
        self._link_lags_button.setIconSize(icons.get_iconsize('normal'))
        self._link_lags_button.clicked.connect(
            lambda checked: self.toggle_link_bp_and_et_lags(
                not self._bp_and_et_lags_are_linked))
        self.toggle_link_bp_and_et_lags(
            self.get_option('bp_and_et_lags_are_linked', False))

        self.detrend_waterlevels_cbox = QCheckBox('Detrend water levels')
        self.detrend_waterlevels_cbox.setChecked(
            self.get_option('detrend_waterlevels'))

        # Lags spinboxes layout.
        lags_layout = QGridLayout()
        lags_layout.setContentsMargins(0, 0, 0, 0)
        lags_layout.setHorizontalSpacing(2)
        lags_layout.addWidget(self.baro_spinbox, 0, 0)
        lags_layout.addWidget(self.earthtides_spinbox, 1, 0)
        lags_layout.addWidget(self._link_lags_button, 0, 1, 2, 1)

        # Setup options layout.
        options_grpbox = QGroupBox()
        options_layout = QGridLayout(options_grpbox)
        options_layout.addWidget(QLabel('No. of BP lags :'), 0, 0)
        options_layout.addWidget(self.earthtides_cbox, 1, 0)
        options_layout.addLayout(lags_layout, 0, 1, 2, 1)
        options_layout.addWidget(self.detrend_waterlevels_cbox, 2, 0, 1, 2)
        options_layout.setColumnStretch(0, 100)
        margins = options_layout.contentsMargins()
        margins.setRight(2)
        options_layout.setContentsMargins(margins)

        # Setup BRF date range widgets.
        self.date_start_edit = QDateTimeEdit()
        self.date_start_edit.setCalendarPopup(True)
        self.date_start_edit.setDisplayFormat('dd/MM/yyyy hh:mm')
        self.date_start_edit.dateChanged.connect(self._plot_brfperiod)
        self.date_start_edit.dateChanged.connect(self._plot_brfperiod)

        self.date_end_edit = QDateTimeEdit()
        self.date_end_edit.setCalendarPopup(True)
        self.date_end_edit.setDisplayFormat('dd/MM/yyyy hh:mm')
        self.date_end_edit.dateChanged.connect(self._plot_brfperiod)
        self.date_end_edit.dateChanged.connect(self._plot_brfperiod)

        self._select_brfperiod_btn = OnOffPushButton('Select')
        self._select_brfperiod_btn.setIcon(get_icon('select_range'))
        self._select_brfperiod_btn.setToolTip(
            "Select a BRF calculation period.")
        self._select_brfperiod_btn.setCheckable(True)
        self._select_brfperiod_btn.setFocusPolicy(Qt.NoFocus)
        self._select_brfperiod_btn.sig_value_changed.connect(
            self.toggle_brfperiod_selection)

        # Setup BRF date range layout.
        daterange_grpbox = QGroupBox()
        daterange_layout = QGridLayout(daterange_grpbox)
        daterange_layout.addWidget(QLabel('BRF Start :'), 0, 0)
        daterange_layout.addWidget(self.date_start_edit, 0, 2)
        daterange_layout.addWidget(QLabel('BRF End :'), 1, 0)
        daterange_layout.addWidget(self.date_end_edit, 1, 2)
        daterange_layout.addWidget(self._select_brfperiod_btn, 2, 0, 1, 3)
        daterange_layout.setColumnStretch(1, 100)

        # Setup the toolbar.
        btn_comp = QPushButton('Compute BRF')
        btn_comp.setToolTip(
            "Compute the barometric response function (BRF) of the well.")
        btn_comp.setIcon(get_icon('play_start'))
        btn_comp.setFocusPolicy(Qt.NoFocus)
        btn_comp.clicked.connect(self.calc_brf)

        self._show_brf_results_btn = QPushButton('Show BRF')
        self._show_brf_results_btn.setIcon(get_icon('search'))
        self._show_brf_results_btn.setToolTip(
            "Show the BRF previously calculated for the well.")
        self._show_brf_results_btn.setFocusPolicy(Qt.NoFocus)
        self._show_brf_results_btn.clicked.connect(self.viewer.show)

        # Setup the main Layout.
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(daterange_grpbox, 0, 0)
        main_layout.addWidget(options_grpbox, 1, 0)
        main_layout.setRowStretch(2, 100)
        main_layout.addWidget(self._show_brf_results_btn, 3, 0)
        main_layout.addWidget(btn_comp, 4, 0)

        # Setup the install KGS_BRF panel
        if not KGSBRFInstaller().kgsbrf_is_installed():
            self.__install_kgs_brf_installer()

    def showEvent(self, event):
        if self._first_show_event:
            self._first_show_event = False
            self._plot_brfperiod()
        super().showEvent(event)

    # ---- WLCalc integration
    @wlcalcmethod
    def _on_period_selected(self, xdata, button, modifiers):
        """
        Handle when a period is selected for the BRF calculations.

        Parameters
        ----------
        xdata : 2-tuple
            A 2-tuple of floats containing the time, in numerical Excel format,
            of the period over which the BRF is to be calculated.
        """
        brfperiod = []
        for x in xdata:
            brfperiod.append(self.wlcalc.time[
                np.argmin(np.abs(x - self.wlcalc.time))])
        self.set_brfperiod(brfperiod)
        self.toggle_brfperiod_selection(False)

    @wlcalcmethod
    def _plot_brfperiod(self):
        """
        Plot on the graph the vertical lines that are used to define the period
        over which the BRF is evaluated.
        """
        if not self.is_brfperiod_selection_toggled() and self.isVisible():
            brfperiod = self.get_brfperiod()
        else:
            brfperiod = [None, None]

        for x, vline in zip(brfperiod, [self._axvline1, self._axvline2]):
            if x is None:
                vline.set_visible(False)
            else:
                vline.set_visible(True)
                vline.set_xdata(
                    x + self.wlcalc.dt4xls2mpl * self.wlcalc.dformat)
        self.wlcalc.draw()

    @wlcalcmethod
    def toggle_brfperiod_selection(self, value):
        """
        Toggle on or off the option to select the BRF calculation period on
        the graph.
        """
        if self.wlcalc.wldset is None:
            self._period_selector.set_active(False)
            self._select_brfperiod_btn.setValue(False, silent=True)
            if value is True:
                self.wlcalc.emit_warning(
                    "Please import a valid water level dataset first.")
            return

        self._period_selector.set_active(value)
        self._select_brfperiod_btn.setValue(value, silent=True)
        if value is True:
            self.wlcalc.toggle_navig_and_select_tools(
                self._select_brfperiod_btn)
        self._plot_brfperiod()

    # ---- WLCalcTool API
    def is_registered(self):
        return self.wlcalc is not None

    def register_tool(self, wlcalc: QWidget):
        self.wlcalc = wlcalc
        index = wlcalc.tools_tabwidget.addTab(self, self.title())
        wlcalc.tools_tabwidget.setTabToolTip(index, self.tooltip())
        wlcalc.tools_tabwidget.currentChanged.connect(
            lambda: self.toggle_brfperiod_selection(False))

        wlcalc.register_navig_and_select_tool(
            self._select_brfperiod_btn)

        self._period_selector = WLCalcVSpanSelector(
            wlcalc.fig.axes[0], wlcalc, onselected=self._on_period_selected,
            axvspan_color='#009900')
        wlcalc.install_axeswidget(self._period_selector)

        # Init axvline artists to plot the BRF period.
        ax = wlcalc.fig.axes[0]
        self._axvline1 = ax.axvline(0, color='#009900', lw=1)
        self._axvline2 = ax.axvline(0, color='#009900', lw=1)

        self._plot_brfperiod()

    def close_tool(self):
        self.set_option('graphs_labels_language', self.viewer.get_language())
        self.set_option('graph_opt_panel_is_visible',
                        self.viewer._graph_opt_panel_is_visible)
        self.viewer.close()

        self.set_option('bp_and_et_lags_are_linked',
                        self._bp_and_et_lags_are_linked)
        self.set_option('compute_with_earthtides',
                        self.earthtides_cbox.isChecked())
        self.set_option('nbr_of_earthtides_lags',
                        self.earthtides_spinbox.value())
        self.set_option('nbr_of_baro_lags',
                        self.baro_spinbox.value())
        self.set_option('detrend_waterlevels',
                        self.detrend_waterlevels_cbox.isChecked())
        super().close()

    def set_wldset(self, wldset):
        self.wldset = wldset
        self.viewer.set_wldset(wldset)
        self.toggle_brfperiod_selection(False)
        self.setEnabled(wldset is not None)
        if wldset is not None:
            xldates = self.wldset.xldates
            self.set_daterange((xldates[0], xldates[-1]))

            # Set the period over which the BRF would be evaluated.
            saved_brfperiod = wldset.get_brfperiod()
            self.set_brfperiod((saved_brfperiod[0] or np.floor(xldates[0]),
                                saved_brfperiod[1] or np.floor(xldates[-1])))
        self._plot_brfperiod()

    def set_wxdset(self, wxdset):
        pass

    # ---- BRF Tool Interface
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
        Get the period over which the BRF would be evaluated.

        Returns
        -------
        brfperiod
            A list of two numerical Excel date values.
        """
        year, month, day = self.date_start_edit.date().getDate()
        hour = self.date_start_edit.time().hour()
        minute = self.date_start_edit.time().minute()
        dstart = xldate_from_datetime_tuple(
            (year, month, day, hour, minute, 0), 0)

        year, month, day = self.date_end_edit.date().getDate()
        hour = self.date_end_edit.time().hour()
        minute = self.date_end_edit.time().minute()
        dend = xldate_from_datetime_tuple(
            (year, month, day, hour, minute, 0), 0)

        return [dstart, dend]

    def set_brfperiod(self, period):
        """
        Set the value of the date_start_edit and date_end_edit widgets used to
        define the period over which the BRF is evaluated. Also save the
        period to the waterlevel dataset.

        Parameters
        ----------
        daterange : 2-length tuple of int
            A list of two numerical Excel date values.
        """
        period = np.sort(period).tolist()
        widgets = (self.date_start_edit, self.date_end_edit)
        for xldate, widget in zip(period, widgets):
            if xldate is not None:
                widget.blockSignals(True)
                widget.setDateTime(qdatetime_from_xldate(xldate))
                widget.blockSignals(False)
        self.wldset.save_brfperiod(period)

    def set_daterange(self, daterange):
        """
        Set the minimum and maximum value of the date_start_edit and
        date_end_edit widgets from the specified Excel numeric dates.

        Parameters
        ----------
        daterange : 2-length tuple of int
            A list of two numerical Excel date values.
        """
        for widget in (self.date_start_edit, self.date_end_edit):
            widget.blockSignals(True)
            widget.setMinimumDateTime(qdatetime_from_xldate(daterange[0]))
            widget.setMaximumDateTime(qdatetime_from_xldate(daterange[1]))
            widget.blockSignals(False)

    def is_brfperiod_selection_toggled(self):
        """Return whether the BRF period selection is toggled."""
        return self._select_brfperiod_btn.value()

    def toggle_link_bp_and_et_lags(self, toggle):
        """
        Toggle on or off the linking of the BP and ET lags values.
        """
        self._bp_and_et_lags_are_linked = toggle
        self._link_lags_button.setIcon(icons.get_icon(
            'link' if toggle else 'link_off'))
        if toggle is True:
            self._handle_lag_value_changed(self.baro_spinbox)

    def import_current_viewer_brf_parameters(self):
        """
        Setup the BRF parameters to reflect those saved in the provided
        BRF results dataset.
        """
        if self.wldset is None or self.wldset.brf_count() == 0:
            return
        brfdata = self.wldset.get_brf(
            self.wldset.get_brfname_at(self.viewer.current_brf.value() - 1))

        # Setup the lags.
        nlag_bp = len(brfdata.loc[:, 'A'].dropna()) - 1
        nlag_et = len(brfdata.loc[:, 'B'].dropna()) - 1

        self.earthtides_cbox.setChecked(nlag_et != -1)
        if nlag_bp != nlag_et and nlag_et != -1:
            self.toggle_link_bp_and_et_lags(False)
        self.baro_spinbox.setValue(nlag_bp)
        if nlag_et != -1:
            self.earthtides_spinbox.setValue(nlag_et)

        # Setup the detrending paramenter.
        self.detrend_waterlevels_cbox.setChecked(brfdata.detrending == 'Yes')

        # Setup the BRF period.
        xls_date_start = xldate_from_datetime_tuple(
            brfdata.date_start.timetuple()[:6], 0)
        xls_date_end = xldate_from_datetime_tuple(
            brfdata.date_end.timetuple()[:6], 0)
        self.set_brfperiod((xls_date_start, xls_date_end))
        self._plot_brfperiod()

    def _handle_lag_value_changed(self, sender):
        """
        Handle when the value of either the barometric pressure
        or earth tide lags change.
        """
        if self._bp_and_et_lags_are_linked:
            if sender == self.baro_spinbox:
                self.earthtides_spinbox.blockSignals(True)
                self.earthtides_spinbox.setValue(self.baro_spinbox.value())
                self.earthtides_spinbox.blockSignals(False)
            else:
                self.baro_spinbox.blockSignals(True)
                self.baro_spinbox.setValue(self.earthtides_spinbox.value())
                self.baro_spinbox.blockSignals(False)

    # ---- KGS BRF installer
    def __install_kgs_brf_installer(self):
        """
        Installs a KGSBRFInstaller that overlays the whole brf tool
        layout until the KGS_BRF program is installed correctly.
        """
        self.kgs_brf_installer = KGSBRFInstaller()
        self.kgs_brf_installer.sig_kgs_brf_installed.connect(
            self.__uninstall_kgs_brf_installer)
        self.layout().addWidget(
            self.kgs_brf_installer,
            0, 0, self.layout().rowCount(), self.layout().columnCount())

    def __uninstall_kgs_brf_installer(self):
        """
        Uninstall the KGSBRFInstaller after the KGS_BRF program has been
        installed properly.
        """
        self.kgs_brf_installer.sig_kgs_brf_installed.disconnect()
        self.kgs_brf_installer = None

    # ---- Calculations
    def calc_brf(self):
        """Prepare the data, calcul the brf, and save and plot the results."""

        # Prepare the datasets.
        well = self.wldset['Well']

        brfperiod = self.get_brfperiod()
        t1 = min(brfperiod)
        i1 = np.where(self.wldset.xldates >= t1)[0][0]
        t2 = max(brfperiod)
        i2 = np.where(self.wldset.xldates <= t2)[0][-1]

        time = np.copy(self.wldset.xldates[i1:i2+1])
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

        # Fill the gaps in the waterlevel data.
        dt = np.min(np.diff(time))
        tc = np.arange(t1, t2+dt/2, dt)
        if len(tc) != len(time) or np.any(np.isnan(wl)):
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
            dataf = bm.read_brf_output()
            date_start, date_end = (xldate_as_datetime(xldate, 0) for
                                    xldate in self.get_brfperiod())
            self.wldset.save_brf(dataf, date_start, date_end,
                                 self.detrend_waterlevels)
            self.viewer.new_brf_added()
            self.viewer.show()
            QApplication.restoreOverrideCursor()
        except Exception:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
            return


class BRFViewer(QDialog):
    """
    Window that is used to show all the results produced with for the
    currently selected water level dataset.
    """
    sig_import_params_in_manager_request = QSignal()

    def __init__(self, wldset=None, parent=None):
        super(BRFViewer, self).__init__(parent)
        self.__save_ddir = None

        self.setWindowTitle('BRF Results Viewer')
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowFlags(
            Qt.Window | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        self.__initGUI__()
        self.set_wldset(wldset)

    def __initGUI__(self):
        # Setup the navigation buttons and widgets.
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

        self.total_brf = QLabel(' / 0')

        # Generate the toolbar buttons.
        self.btn_del = QToolButtonNormal(icons.get_icon('delete_data'))
        self.btn_del.setToolTip('Delete current BRF results')
        self.btn_del.clicked.connect(self.del_brf)

        self.btn_del_all = QToolButtonNormal(icons.get_icon('close_all'))
        self.btn_del_all.setToolTip(
            'Delete all BRF results for the current water level dataset.')
        self.btn_del_all.clicked.connect(self.del_all_brf)

        self.btn_save = btn_save = QToolButtonNormal(icons.get_icon('save'))
        btn_save.setToolTip('Save current BRF graph as...')
        btn_save.clicked.connect(self.select_savefig_path)

        self.btn_export = QToolButtonNormal(icons.get_icon('export_data'))
        self.btn_export.setToolTip('Export data to file.')
        self.btn_export.clicked.connect(self.select_export_brfdata_filepath)

        self.btn_copy = QToolButtonNormal('copy_clipboard')
        self.btn_copy.setToolTip('Copy figure to clipboard as image.')
        self.btn_copy.clicked.connect(self.copyfig_to_clipboard)

        self.btn_setp = QToolButtonNormal(icons.get_icon('page_setup'))
        self.btn_setp.setToolTip('Show graph layout parameters...')
        self.btn_setp.clicked.connect(self.toggle_graphpannel)

        self.import_params_in_manager_btn = QToolButtonNormal(
            icons.get_icon('content_duplicate'))
        self.import_params_in_manager_btn.setToolTip(
            'Set the parameters of the BRF tool to the values that were '
            'used to calculate the BRF currently displayed in this viewer.')
        self.import_params_in_manager_btn.clicked.connect(
            lambda _: self.sig_import_params_in_manager_request.emit())

        # Setup the toolbar.
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("QToolBar {border: 0px; spacing:1px;}")
        buttons = [btn_save, self.btn_copy, self.btn_export, self.btn_del,
                   self.btn_del_all, None, self.btn_prev, self.current_brf,
                   self.total_brf, self.btn_next, None,
                   self.import_params_in_manager_btn]
        for button in buttons:
            if button is None:
                self.toolbar.addSeparator()
            else:
                self.toolbar.addWidget(button)
        self.toolbar.addWidget(create_toolbar_stretcher())
        self.toolbar.addWidget(self.btn_setp)

        # Setup the graph canvas.
        self.brf_canvas = FigureCanvasQTAgg(BRFFigure())

        self.fig_frame = QFrame()
        self.fig_frame.setFrameStyle(FRAME_SYLE)
        self.fig_frame.setObjectName("figframe")
        self.fig_frame.setStyleSheet("#figframe {background-color:white;}")

        fig_frame_layout = QGridLayout(self.fig_frame)
        fig_frame_layout.addWidget(self.brf_canvas, 0, 0)
        fig_frame_layout.addWidget(HSep(), 1, 0)
        fig_frame_layout.addWidget(self.toolbar, 2, 0)

        # Setup the graph options panel.
        self.graph_opt_panel = BRFOptionsPanel()
        self.graph_opt_panel.sig_graphconf_changed.connect(self.plot_brf)
        self._graph_opt_panel_is_visible = False

        # Setup the main layout.
        main_layout = QGridLayout(self)
        main_layout.addWidget(self.fig_frame, 0, 2)
        main_layout.addWidget(self.graph_opt_panel, 0, 3)
        main_layout.setColumnStretch(1, 100)
        main_layout.setSizeConstraint(main_layout.SetFixedSize)

    @property
    def savedir(self):
        """Return a path where figures and files are saved by default."""
        if self.__save_ddir is None or not osp.exists(self.__save_ddir):
            try:
                savedir = self.wldset.dirname
            except AttributeError:
                savedir = osp.dirname(__rootdir__)
            finally:
                return savedir
        else:
            return self.__save_ddir

    # ---- Toolbar Handlers
    def toggle_graphpannel(self):
        """
        Hide or show the BRF graph option panel.
        """
        self._graph_opt_panel_is_visible = not self._graph_opt_panel_is_visible
        self.graph_opt_panel.setVisible(self._graph_opt_panel_is_visible)
        self.btn_setp.setAutoRaise(not self._graph_opt_panel_is_visible)
        self.btn_setp.setToolTip(
            'Show graph layout parameters...' if
            self._graph_opt_panel_is_visible is False else
            'Hide graph layout parameters...')

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
        self.total_brf.setText(' / %d' % count)

        self.current_brf.setMinimum(min(count, 1))
        self.current_brf.setMaximum(count)
        curnt = self.current_brf.value()

        self.toolbar.setEnabled(count > 0)
        self.btn_prev.setEnabled(curnt > 1)
        self.btn_next.setEnabled(curnt < count)
        self.btn_del.setEnabled(count > 0)

        self.plot_brf()

    def select_savefig_path(self):
        """
        Opens a dialog to select a file path where to save the brf figure.
        """
        ddir = osp.join(self.savedir, 'brf_%s' % self.wldset['Well'])

        dialog = QFileDialog()
        fname, ftype = dialog.getSaveFileName(
            self, "Save Figure", ddir, '*.pdf;;*.svg')
        ftype = ftype.replace('*', '')
        if fname:
            if not osp.samefile(osp.dirname(ddir), osp.dirname(fname)):
                self.__save_ddir = osp.dirname(fname)
            if not fname.endswith(ftype):
                fname = fname + ftype
            self.save_brf_fig(fname)

    def save_brf_fig(self, fname):
        """Saves the current BRF figure to fname."""
        self.brf_canvas.figure.savefig(fname)

    def copyfig_to_clipboard(self):
        """Saves the current BRF figure to the clipboard."""
        buf = io.BytesIO()
        self.save_brf_fig(buf)
        QApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
        buf.close()

    def select_export_brfdata_filepath(self):
        """
        Open a dialog to select a file path where to save the brf data.
        """
        fname = 'brf_' + self.wldset['Well']
        if self.wldset['Well ID']:
            fname += '_%s' % self.wldset['Well ID']
        ddir = osp.join(self.savedir, fname)

        dialog = QFileDialog()
        fname, ftype = dialog.getSaveFileName(
            self, "Export Data", ddir, "*.xlsx;;*.xls;;*.csv")
        ftype = ftype.replace('*', '')
        if fname:
            if not osp.samefile(osp.dirname(ddir), osp.dirname(fname)):
                self.__save_ddir = osp.dirname(fname)
            if not fname.endswith(ftype):
                fname = fname + ftype
            self.export_brf_data(fname)

    def export_brf_data(self, fname):
        """Export the current BRF data to to file."""
        self.wldset.export_brf_to_csv(fname, self.current_brf.value()-1)

    # ---- Others
    def set_wldset(self, wldset):
        self.wldset = wldset
        self.setEnabled(wldset is not None)
        if wldset is not None:
            self.update_brfnavigate_state()

    def get_language(self):
        return self.graph_opt_panel.get_language()

    def set_language(self, language):
        return self.graph_opt_panel.set_language(language)

    def plot_brf(self):
        self.brf_canvas.figure.set_language(self.get_language())
        if self.wldset is None or self.wldset.brf_count() == 0:
            self.brf_canvas.figure.empty_BRF()
        else:
            brfdata = self.wldset.get_brf(
                self.wldset.get_brfname_at(self.current_brf.value() - 1))

            well_name = self.wldset['Well']
            if self.wldset['Well ID']:
                well_name += ' ({})'.format(self.wldset['Well ID'])

            self.brf_canvas.figure.plot(
                brfdata,
                well_name,
                show_ebar=self.graph_opt_panel.show_ebar,
                msize=self.graph_opt_panel.markersize,
                draw_line=self.graph_opt_panel.draw_line,
                ylim=[self.graph_opt_panel.ymin, self.graph_opt_panel.ymax],
                xlim=[self.graph_opt_panel.xmin, self.graph_opt_panel.xmax],
                time_units=self.graph_opt_panel.time_units,
                xscl=self.graph_opt_panel.xscale,
                yscl=self.graph_opt_panel.yscale)
        self.brf_canvas.draw()

    def show(self):
        super(BRFViewer, self).show()
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
        # Setup the line and marker options.
        self._errorbar = QCheckBox('Show error bars')
        self._errorbar.setChecked(True)
        self._errorbar.stateChanged.connect(self._graphconf_changed)

        self._drawline = QCheckBox('Draw line')
        self._drawline.setChecked(False)
        self._drawline.stateChanged.connect(self._graphconf_changed)

        self._markersize = {}
        self._markersize['label'] = QLabel('Marker size :')
        self._markersize['widget'] = QSpinBox()
        self._markersize['widget'].setValue(5)
        self._markersize['widget'].setRange(0, 25)
        self._markersize['widget'].valueChanged.connect(
            self._graphconf_changed)

        line_and_marker_groupbox = QGroupBox()
        line_and_marker_layout = QGridLayout(line_and_marker_groupbox)
        line_and_marker_layout.addWidget(self._errorbar, 0, 0, 1, 2)
        line_and_marker_layout.addWidget(self._drawline, 1, 0, 1, 2)
        line_and_marker_layout.addWidget(self._markersize['label'], 2, 0)
        line_and_marker_layout.addWidget(self._markersize['widget'], 2, 1)
        line_and_marker_layout.setColumnStretch(0, 1)

        # Setup yaxis options.
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

        self.ylim_groupbox = QGroupBox('Vertical Axis Options')
        self.ylim_groupbox.setCheckable(True)
        self.ylim_groupbox.setChecked(False)
        self.ylim_groupbox.toggled.connect(lambda _: self._graphconf_changed())

        ylim_grouplayout = QGridLayout(self.ylim_groupbox)
        ylim_grouplayout.addWidget(QLabel('Minimum :'), 0, 0)
        ylim_grouplayout.addWidget(self._ylim['min'], 0, 1)
        ylim_grouplayout.addWidget(QLabel('Maximum :'), 1, 0)
        ylim_grouplayout.addWidget(self._ylim['max'], 1, 1)
        ylim_grouplayout.addWidget(QLabel('Scale :'), 2, 0)
        ylim_grouplayout.addWidget(self._ylim['scale'], 2, 1)
        ylim_grouplayout.setColumnStretch(0, 1)

        # Setup xaxis options.
        self._xlim = {}
        self._xlim['units'] = QComboBox()
        self._xlim['units'].addItems(['Hours', 'Days'])
        self._xlim['units'].setCurrentIndex(1)
        self._xlim['units'].currentIndexChanged.connect(
            self._time_units_changed)
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

        self.xlim_groupbox = QGroupBox('Horizontal Axis Options')
        self.xlim_groupbox.setCheckable(True)
        self.xlim_groupbox.setChecked(False)
        self.xlim_groupbox.toggled.connect(lambda _: self._graphconf_changed())

        xlim_grouplayout = QGridLayout(self.xlim_groupbox)
        xlim_grouplayout.addWidget(QLabel('Time units :'), 0, 0)
        xlim_grouplayout.addWidget(self._xlim['units'], 0, 1)
        xlim_grouplayout.addWidget(QLabel('Minimum :'), 1, 0)
        xlim_grouplayout.addWidget(self._xlim['min'], 1, 1)
        xlim_grouplayout.addWidget(QLabel('Maximum :'), 2, 0)
        xlim_grouplayout.addWidget(self._xlim['max'], 2, 1)
        xlim_grouplayout.addWidget(QLabel('Scale :'), 3, 0)
        xlim_grouplayout.addWidget(self._xlim['scale'], 3, 1)
        xlim_grouplayout.setColumnStretch(0, 1)

        # Setup the language widget.
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(['English', 'French'])
        self.language_combobox.setCurrentIndex(0)
        self.language_combobox.setToolTip(
            "Set the language of the text shown in the graph.")
        self.language_combobox.currentIndexChanged.connect(
            self._graphconf_changed)

        language_layout = QGridLayout()
        language_layout.setContentsMargins(0, 0, 0, 0)
        language_layout.addWidget(QLabel('Language :'), 0, 0)
        language_layout.addWidget(self.language_combobox, 0, 1)
        language_layout.setColumnStretch(1, 1)

        # Setup the main layout.
        layout = QGridLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.addWidget(line_and_marker_groupbox, 0, 0)
        layout.addWidget(self.ylim_groupbox, 1, 0)
        layout.addWidget(self.xlim_groupbox, 2, 0)
        layout.addLayout(language_layout, 3, 0)
        layout.setRowStretch(4, 1)

    def _graphconf_changed(self):
        """
        Emits a signal to indicate that the graph configuration has changed.
        """
        self.sig_graphconf_changed.emit()

    # ---- Graph Panel Properties
    @property
    def time_units(self):
        if not self.xlim_groupbox.isChecked():
            return 'auto'
        else:
            return self._xlim['units'].currentText().lower()

    @property
    def xmin(self):
        if not self.xlim_groupbox.isChecked():
            return None
        else:
            if self.time_units == 'hours':
                return self._xlim['min'].value() / 24
            else:
                return self._xlim['min'].value()

    @property
    def xmax(self):
        if not self.xlim_groupbox.isChecked():
            return None
        else:
            if self.time_units == 'hours':
                return self._xlim['max'].value() / 24
            else:
                return self._xlim['max'].value()

    @property
    def xscale(self):
        if not self.xlim_groupbox.isChecked():
            return None
        else:
            if self.time_units == 'hours':
                return self._xlim['scale'].value() / 24
            else:
                return self._xlim['scale'].value()

    @property
    def ymin(self):
        return (self._ylim['min'].value() if self.ylim_groupbox.isChecked()
                else None)

    @property
    def ymax(self):
        return (self._ylim['max'].value() if self.ylim_groupbox.isChecked()
                else None)

    @property
    def yscale(self):
        return (self._ylim['scale'].value() if self.ylim_groupbox.isChecked()
                else None)

    @property
    def show_ebar(self):
        return self._errorbar.isChecked()

    @property
    def draw_line(self):
        return self._drawline.isChecked()

    @property
    def markersize(self):
        return self._markersize['widget'].value()

    def get_language(self):
        return self.language_combobox.currentText().lower()

    def set_language(self, language):
        for i in range(self.language_combobox.count()):
            if self.language_combobox.itemText(i).lower() == language.lower():
                self.language_combobox.setCurrentIndex(i)
                self._graphconf_changed()
                break

    # ---- Handlers
    def _time_units_changed(self):
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
