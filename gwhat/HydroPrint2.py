# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports
import io
import sys
import os
import os.path as osp

# ---- Third party imports
from PyQt5.QtGui import QImage
from PyQt5.QtCore import Qt, QDate, QCoreApplication, QPoint
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtWidgets import (
    QSpinBox, QDoubleSpinBox, QWidget, QDateEdit, QAbstractSpinBox,
    QGridLayout, QFrame, QMessageBox, QComboBox, QLabel, QTabWidget,
    QFileDialog, QApplication, QPushButton, QDesktopWidget, QGroupBox,
    QMainWindow, QToolBar)

from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

# ---- Local imports
from gwhat.config.ospath import (
    get_select_file_dialog_dir, set_select_file_dialog_dir)
from gwhat.gwrecharge.glue import GLUEDataFrameBase
from gwhat.hydrograph4 import Hydrograph
from gwhat.utils.icons import get_iconsize, get_icon
from gwhat.utils.qthelpers import create_toolbutton
from gwhat.common.utils import find_unique_filename
from gwhat.projet.reader_waterlvl import load_waterlvl_measures
from gwhat.widgets.buttons import LangToolButton
from gwhat.widgets.colorpreferences import (
    ColorsManager, ColorPreferencesDialog)
from gwhat.widgets.layout import OnOffToggleWidget, VSep
import gwhat.widgets.mplfigureviewer as mplFigViewer


class HydroprintGUI(QWidget):

    ConsoleSignal = QSignal(str)

    def __init__(self, datamanager, parent=None):
        super().__init__(parent)

        self.__updateUI = True

        # Child widgets:
        self.dmngr = datamanager
        self.dmngr.wldsetChanged.connect(self.wldset_changed)
        self.dmngr.wxdsetChanged.connect(self.wxdset_changed)

        self.page_setup_win = PageSetupWin(self)
        self.page_setup_win.newPageSetupSent.connect(self.layout_changed)

        self.color_palette_win = ColorPreferencesDialog(parent)
        self.color_palette_win.sig_color_preferences_changed.connect(
            self.update_colors)

        self.__initUI__()

    def __initUI__(self):
        # =====================================================================
        # Setup the left side layout.
        # =====================================================================
        left_widget = QMainWindow()

        # Setup the hydrograph frame.
        self.hydrograph = Hydrograph()
        self.hydrograph_scrollarea = mplFigViewer.ImageViewer()
        left_widget.setCentralWidget(self.hydrograph_scrollarea)

        # Setup the toolbar buttons.
        self.btn_save = btn_save = create_toolbutton(
            parent=self,
            icon='save',
            tip='Save the well hydrograph',
            triggered=self.select_save_path
            )
        self.btn_copy_to_clipboard = create_toolbutton(
            self, icon='copy_clipboard',
            text="Copy",
            tip="Put a copy of the figure on the Clipboard.",
            triggered=self.copyfig_to_clipboard,
            shortcut='Ctrl+C')
        # The button draw is usefull for debugging purposes
        btn_draw = create_toolbutton(
            parent=self,
            icon='refresh',
            tip='Force a refresh of the well hydrograph',
            triggered=self.draw_hydrograph
            )
        self.btn_load_layout = create_toolbutton(
            parent=self,
            icon='load_graph_config',
            tip=("Load graph layout for the current water level "
                 "datafile if it exists."),
            triggered=self.load_layout_isClicked
            )
        self.btn_save_layout = create_toolbutton(
            parent=self,
            icon='save_graph_config',
            tip='Save current graph layout',
            triggered=self.save_layout_isClicked
            )

        btn_bestfit_waterlvl = create_toolbutton(
            parent=self,
            icon='fit_y',
            tip='Best fit the water level scale',
            triggered=self.best_fit_waterlvl
            )
        btn_bestfit_time = create_toolbutton(
            parent=self,
            icon='fit_x',
            tip='Best fit the time scale',
            triggered=self.best_fit_time
            )
        self.btn_page_setup = create_toolbutton(
            parent=self,
            icon='page_setup',
            tip='Show the page setup window',
            triggered=self.page_setup_win.show
            )
        btn_color_pick = create_toolbutton(
            parent=self,
            icon='color_picker',
            tip=("Show a window to setup the color palette "
                 "used to draw the hydrograph."),
            triggered=self.color_palette_win.show
            )
        self.btn_language = LangToolButton()
        self.btn_language.setToolTip(
            "Set the language of the text shown in the graph.")
        self.btn_language.sig_lang_changed.connect(self.layout_changed)

        # Setup the zoom panel.
        btn_zoom_out = create_toolbutton(
            parent=self,
            icon='zoom_out',
            tip='Zoom out (ctrl + mouse-wheel-down)',
            triggered=self.zoom_out,
            iconsize=get_iconsize('normal')
            )
        btn_zoom_in = create_toolbutton(
            parent=self,
            icon='zoom_in',
            tip='Zoom in (ctrl + mouse-wheel-up)',
            triggered=self.zoom_in,
            iconsize=get_iconsize('normal')
            )
        self.zoom_disp = QDoubleSpinBox()
        self.zoom_disp.setAlignment(Qt.AlignCenter)
        self.zoom_disp.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.zoom_disp.setReadOnly(True)
        self.zoom_disp.setSuffix(' %')
        self.zoom_disp.setRange(0, 9999)
        self.zoom_disp.setValue(100)
        self.zoom_disp.setDecimals(0)
        self.hydrograph_scrollarea.zoomChanged.connect(self.zoom_disp.setValue)

        zoom_pan = QFrame()
        zoom_pan_layout = QGridLayout(zoom_pan)
        zoom_pan_layout.setContentsMargins(0, 0, 0, 0)
        zoom_pan_layout.setSpacing(3)
        zoom_pan_layout.addWidget(btn_zoom_out, 0, 0)
        zoom_pan_layout.addWidget(btn_zoom_in, 0, 1)
        zoom_pan_layout.addWidget(self.zoom_disp, 0, 2)

        # Setup the toolbar of the left widget.
        toolbar = QToolBar()
        toolbar.setStyleSheet("QToolBar {border: 0px; spacing:1px;}")
        toolbar.setFloatable(False)
        toolbar.setMovable(False)
        toolbar.setIconSize(get_iconsize('normal'))
        left_widget.addToolBar(Qt.TopToolBarArea, toolbar)

        btn_list = [
            btn_save, self.btn_copy_to_clipboard, btn_draw,
            self.btn_load_layout, self.btn_save_layout,
            None, btn_bestfit_waterlvl, btn_bestfit_time, None,
            self.btn_page_setup, btn_color_pick, self.btn_language,
            None, zoom_pan]
        for col, widget in enumerate(btn_list):
            if widget is None:
                toolbar.addSeparator()
            else:
                toolbar.addWidget(widget)

        # =====================================================================
        # Setup the right side layout.
        # =====================================================================
        self.tabscales = self.__init_scalesTabWidget__()

        self.right_panel = QFrame()
        right_panel_layout = QGridLayout(self.right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.addWidget(self.dmngr, 0, 0)
        right_panel_layout.addWidget(self.tabscales, 1, 0)
        right_panel_layout.setRowStretch(2, 100)
        right_panel_layout.setSpacing(15)

        self.Ptot_scale.valueChanged.connect(self.layout_changed)
        self.qweather_bin.currentIndexChanged.connect(self.layout_changed)

        # =====================================================================
        # Setup the main layout.
        # =====================================================================
        main_layout = QGridLayout(self)
        main_layout.addWidget(left_widget, 0, 0)
        main_layout.addWidget(VSep(), 0, 1)
        main_layout.addWidget(self.right_panel, 0, 2)
        main_layout.setSpacing(15)
        main_layout.setColumnStretch(0, 500)

        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)

    def __init_scalesTabWidget__(self):

        class QRowLayout(QGridLayout):
            def __init__(self, items, parent=None):
                super(QRowLayout, self).__init__(parent)

                for col, item in enumerate(items):
                    self.addWidget(item, 0, col)

                self.setContentsMargins(0, 0, 0, 0)
                self.setColumnStretch(0, 100)

        # ---- Time axis properties

        # Generate the widgets :

        self.date_start_widget = QDateEdit()
        self.date_start_widget.setDisplayFormat('01 / MM / yyyy')
        self.date_start_widget.setAlignment(Qt.AlignCenter)
        self.date_start_widget.dateChanged.connect(self.layout_changed)

        self.date_end_widget = QDateEdit()
        self.date_end_widget.setDisplayFormat('01 / MM / yyyy')
        self.date_end_widget.setAlignment(Qt.AlignCenter)
        self.date_end_widget.dateChanged.connect(self.layout_changed)

        self.time_scale_label = QComboBox()
        self.time_scale_label.setEditable(False)
        self.time_scale_label.setInsertPolicy(QComboBox.NoInsert)
        self.time_scale_label.addItems(['Month', 'Year'])
        self.time_scale_label.setCurrentIndex(0)
        self.time_scale_label.currentIndexChanged.connect(self.layout_changed)

        self.dateDispFreq_spinBox = QSpinBox()
        self.dateDispFreq_spinBox.setSingleStep(1)
        self.dateDispFreq_spinBox.setMinimum(1)
        self.dateDispFreq_spinBox.setMaximum(100)
        self.dateDispFreq_spinBox.setValue(
            self.hydrograph.date_labels_pattern)
        self.dateDispFreq_spinBox.setAlignment(Qt.AlignCenter)
        self.dateDispFreq_spinBox.setKeyboardTracking(False)
        self.dateDispFreq_spinBox.valueChanged.connect(self.layout_changed)

        # Setting up the layout :

        widget_time_scale = QFrame()
        widget_time_scale.setFrameStyle(0)
        grid_time_scale = QGridLayout()

        GRID = [[QLabel('From :'), self.date_start_widget],
                [QLabel('To :'), self.date_end_widget],
                [QLabel('Scale :'), self.time_scale_label],
                [QLabel('Date Disp. Pattern:'),
                 self.dateDispFreq_spinBox]]

        for i, ROW in enumerate(GRID):
            grid_time_scale.addLayout(QRowLayout(ROW), i, 1)

        grid_time_scale.setVerticalSpacing(5)
        grid_time_scale.setContentsMargins(10, 10, 10, 10)

        widget_time_scale.setLayout(grid_time_scale)

        # ----- Water level axis properties

        # Widget :

        self.waterlvl_scale = QDoubleSpinBox()
        self.waterlvl_scale.setSingleStep(0.05)
        self.waterlvl_scale.setMinimum(0.05)
        self.waterlvl_scale.setSuffix('  m')
        self.waterlvl_scale.setAlignment(Qt.AlignCenter)
        self.waterlvl_scale.setKeyboardTracking(False)
        self.waterlvl_scale.valueChanged.connect(self.layout_changed)
        self.waterlvl_scale.setFixedWidth(100)

        self.waterlvl_max = QDoubleSpinBox()
        self.waterlvl_max.setSingleStep(0.1)
        self.waterlvl_max.setSuffix('  m')
        self.waterlvl_max.setAlignment(Qt.AlignCenter)
        self.waterlvl_max.setMinimum(-1000)
        self.waterlvl_max.setMaximum(1000)
        self.waterlvl_max.setKeyboardTracking(False)
        self.waterlvl_max.valueChanged.connect(self.layout_changed)
        self.waterlvl_max.setFixedWidth(100)

        self.NZGridWL_spinBox = QSpinBox()
        self.NZGridWL_spinBox.setSingleStep(1)
        self.NZGridWL_spinBox.setMinimum(1)
        self.NZGridWL_spinBox.setMaximum(50)
        self.NZGridWL_spinBox.setValue(self.hydrograph.NZGrid)
        self.NZGridWL_spinBox.setAlignment(Qt.AlignCenter)
        self.NZGridWL_spinBox.setKeyboardTracking(False)
        self.NZGridWL_spinBox.valueChanged.connect(self.layout_changed)
        self.NZGridWL_spinBox.setFixedWidth(100)

        self.datum_widget = QComboBox()
        self.datum_widget.addItems(['Ground Surface', 'Sea Level'])
        self.datum_widget.currentIndexChanged.connect(self.layout_changed)

        # Layout :

        subgrid_WLScale = QGridLayout()

        GRID = [[QLabel('Minimum :'), self.waterlvl_max],
                [QLabel('Scale :'), self.waterlvl_scale],
                [QLabel('Grid Divisions :'), self.NZGridWL_spinBox],
                [QLabel('Datum :'), self.datum_widget]]

        for i, ROW in enumerate(GRID):
            subgrid_WLScale.addLayout(QRowLayout(ROW), i, 1)

        subgrid_WLScale.setVerticalSpacing(5)
        subgrid_WLScale.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        WLScale_widget = QFrame()
        WLScale_widget.setFrameStyle(0)
        WLScale_widget.setLayout(subgrid_WLScale)

        # ---- Weather Axis

        # Widgets :

        self.Ptot_scale = QSpinBox()
        self.Ptot_scale.setSingleStep(5)
        self.Ptot_scale.setMinimum(5)
        self.Ptot_scale.setMaximum(500)
        self.Ptot_scale.setValue(20)
        self.Ptot_scale.setSuffix('  mm')
        self.Ptot_scale.setAlignment(Qt.AlignCenter)

        self.qweather_bin = QComboBox()
        self.qweather_bin.setEditable(False)
        self.qweather_bin.setInsertPolicy(QComboBox.NoInsert)
        self.qweather_bin.addItems(['day', 'week', 'month'])
        self.qweather_bin.setCurrentIndex(1)

        # Layout :

        layout = QGridLayout()

        GRID = [[QLabel('Precip. Scale :'), self.Ptot_scale],
                [QLabel('Resampling :'), self.qweather_bin]]

        for i, row in enumerate(GRID):
            layout.addLayout(QRowLayout(row), i, 1)

        layout.setVerticalSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)  # (L,T,R,B)
        layout.setRowStretch(i+1, 100)

        widget_weather_scale = QFrame()
        widget_weather_scale.setFrameStyle(0)
        widget_weather_scale.setLayout(layout)

        # ---- ASSEMBLING TABS

        tabscales = QTabWidget()
        tabscales.addTab(widget_time_scale, 'Time')
        tabscales.addTab(WLScale_widget, 'Water Level')
        tabscales.addTab(widget_weather_scale, 'Weather')

        return tabscales

    def emit_warning(self, message, title='Warning'):
        QMessageBox.warning(self, title, message, QMessageBox.Ok)

    def close(self):
        """Close HydroPrint widget."""
        self.color_palette_win.close()
        super().close()

    @property
    def workdir(self):
        return self.dmngr.workdir

    # ---- Utilities
    def save_figure(self, fname):
        """Save the hydrograph figure in a file."""
        self.hydrograph.generate_hydrograph()
        self.hydrograph.savefig(fname)

    def copyfig_to_clipboard(self):
        """Saves the current BRF figure to the clipboard."""
        buf = io.BytesIO()
        self.hydrograph.generate_hydrograph()
        self.hydrograph.savefig(buf)
        QApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
        buf.close()

    def zoom_in(self):
        self.hydrograph_scrollarea.zoomIn()

    def zoom_out(self):
        self.hydrograph_scrollarea.zoomOut()

    def update_colors(self):
        self.hydrograph.update_colors()
        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)

    # ---- Datasets Handlers
    @property
    def wldset(self):
        return self.dmngr.get_current_wldset()

    @property
    def wxdset(self):
        return self.dmngr.get_current_wxdset()

    def wldset_changed(self):
        """Handle when the water level dataset of the datamanager changes."""
        if self.wldset is None:
            self.clear_hydrograph()
            return
        else:
            self.hydrograph.set_wldset(self.wldset)
            self.hydrograph.gluedf = self.wldset.get_glue_at(-1)

        # Load the manual measurements.
        fname = os.path.join(
            osp.dirname(self.dmngr.projet.filename),
            "Water Levels",
            'waterlvl_manual_measurements')
        tmeas, wlmeas = load_waterlvl_measures(fname, self.wldset['Well'])
        self.wldset.set_wlmeas(tmeas, wlmeas)

        # Setup the layout of the hydrograph.
        layout = self.wldset.get_layout()
        if layout is not None:
            msg = ("Loading existing graph layout for well %s." %
                   self.wldset['Well'])
            print(msg)
            self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
            self.load_graph_layout(layout)
        else:
            print('No graph layout exists for well %s.' % self.wldset['Well'])
            # Fit Water Level in Layout :
            self.__updateUI = False
            self.best_fit_waterlvl()
            self.best_fit_time()
            if self.dmngr.set_closest_wxdset() is None:
                self.draw_hydrograph()
            self.__updateUI = True

    def wxdset_changed(self):
        """Handle when the weather dataset of the datamanager changes."""
        if self.wldset is None:
            self.clear_hydrograph()
        else:
            self.hydrograph.set_wxdset(self.wxdset)
            QCoreApplication.processEvents()
            self.draw_hydrograph()

    # ---- Draw Hydrograph Handlers
    def best_fit_waterlvl(self):
        wldset = self.dmngr.get_current_wldset()
        if wldset is not None:
            WLscale, WLmin = self.hydrograph.best_fit_waterlvl()
            self.waterlvl_scale.setValue(WLscale)
            self.waterlvl_max.setValue(WLmin)

    def best_fit_time(self):
        wldset = self.dmngr.get_current_wldset()
        if wldset is not None:
            date0, date1 = self.hydrograph.best_fit_time(wldset.xldates)
            self.date_start_widget.setDate(QDate(date0[0], date0[1], date0[2]))
            self.date_end_widget.setDate(QDate(date1[0], date1[1], date1[2]))

    @QSlot()
    def mrc_wl_changed(self):
        """
        Force a redraw of the MRC water levels after the results have
        changed for the dataset.
        """
        self.hydrograph.draw_mrc_wl()
        self.hydrograph.setup_legend()
        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)

    @QSlot(GLUEDataFrameBase)
    def glue_wl_changed(self, gluedf):
        """
        Force a redraw of the GLUE water levels after the results have
        changed for the dataset.
        """
        self.hydrograph.set_gluedf(gluedf)
        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)

    def layout_changed(self):
        """
        When an element of the graph layout is changed in the UI.
        """

        if self.__updateUI is False:
            return

        self.update_graph_layout_parameter()

        if self.hydrograph.isHydrographExists is False:
            return

        sender = self.sender()

        if sender == self.btn_language:
            self.hydrograph.draw_ylabels()
            self.hydrograph.setup_xticklabels()
            self.hydrograph.setup_legend()
        elif sender in [self.waterlvl_max, self.waterlvl_scale]:
            self.hydrograph.setup_waterlvl_scale()
            self.hydrograph.draw_ylabels()
        elif sender == self.NZGridWL_spinBox:
            self.hydrograph.setup_waterlvl_scale()
            self.hydrograph.update_precip_scale()
            self.hydrograph.draw_ylabels()
        elif sender == self.Ptot_scale:
            self.hydrograph.update_precip_scale()
            self.hydrograph.draw_ylabels()
        elif sender == self.datum_widget:
            yoffset = int(self.wldset['Elevation']/self.hydrograph.WLscale)
            yoffset *= self.hydrograph.WLscale

            self.hydrograph.WLmin = (yoffset - self.hydrograph.WLmin)

            self.waterlvl_max.blockSignals(True)
            self.waterlvl_max.setValue(self.hydrograph.WLmin)
            self.waterlvl_max.blockSignals(False)

            # This is calculated so that trailing zeros in the altitude of the
            # well is not carried to the y axis labels, so that they remain a
            # int multiple of *WLscale*.

            self.hydrograph.setup_waterlvl_scale()
            self.hydrograph.draw_waterlvl()
            self.hydrograph.draw_ylabels()
        elif sender in [self.date_start_widget, self.date_end_widget]:
            self.hydrograph.set_time_scale()
            self.hydrograph.draw_weather()
            self.hydrograph.draw_figure_title()
        elif sender == self.dateDispFreq_spinBox:
            self.hydrograph.set_time_scale()
            self.hydrograph.setup_xticklabels()
        elif sender == self.page_setup_win:
            self.hydrograph.update_fig_size()
            # Implicitly call : set_margins()
            #                   draw_ylabels()
            #                   set_time_scale()
            #                   draw_figure_title
            self.hydrograph.draw_waterlvl()
            self.hydrograph.setup_legend()
        elif sender == self.qweather_bin:
            self.hydrograph.resample_bin()
            self.hydrograph.draw_weather()
            self.hydrograph.draw_ylabels()
        elif sender == self.time_scale_label:
            self.hydrograph.set_time_scale()
            self.hydrograph.draw_weather()
        else:
            print('No action for this widget yet.')

        # !!!! temporary fix until I can find a better solution !!!!

#        sender.blockSignals(True)
        if type(sender) in [QDoubleSpinBox, QSpinBox]:
            sender.setReadOnly(True)

        for i in range(10):
            QCoreApplication.processEvents()
        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)
        for i in range(10):
            QCoreApplication.processEvents()

        if type(sender) in [QDoubleSpinBox, QSpinBox]:
            sender.setReadOnly(False)
#        sender.blockSignals(False)

    def update_graph_layout_parameter(self):

        # language :

        self.hydrograph.language = self.btn_language.language

        # Scales :

        self.hydrograph.WLmin = self.waterlvl_max.value()
        self.hydrograph.WLscale = self.waterlvl_scale.value()
        self.hydrograph.RAINscale = self.Ptot_scale.value()
        self.hydrograph.NZGrid = self.NZGridWL_spinBox.value()

        # WL Datum :

        self.hydrograph.WLdatum = self.datum_widget.currentIndex()

        # Dates :

        self.hydrograph.datemode = self.time_scale_label.currentText()

        year = self.date_start_widget.date().year()
        month = self.date_start_widget.date().month()
        self.hydrograph.TIMEmin = xldate_from_date_tuple((year, month, 1), 0)

        year = self.date_end_widget.date().year()
        month = self.date_end_widget.date().month()
        self.hydrograph.TIMEmax = xldate_from_date_tuple((year, month, 1), 0)

        self.hydrograph.date_labels_pattern = self.dateDispFreq_spinBox.value()

        # Page Setup :

        self.hydrograph.fwidth = self.page_setup_win.pageSize[0]
        self.hydrograph.fheight = self.page_setup_win.pageSize[1]
        self.hydrograph.va_ratio = self.page_setup_win.va_ratio

        self.hydrograph.trend_line = self.page_setup_win.isTrendLine
        self.hydrograph.isLegend = self.page_setup_win.isLegend
        self.hydrograph.isGraphTitle = self.page_setup_win.isGraphTitle
        self.hydrograph.set_meteo_on(self.page_setup_win.is_meteo_on)
        self.hydrograph.set_glue_wl_on(self.page_setup_win.is_glue_wl_on)
        self.hydrograph.set_mrc_wl_on(self.page_setup_win.is_mrc_wl_on)
        self.hydrograph.set_figframe_lw(self.page_setup_win.figframe_lw)

        # Weather bins :

        self.hydrograph.bwidth_indx = self.qweather_bin.currentIndex()

    def clear_hydrograph(self):
        """Clear the hydrograph figure to show only a blank canvas."""
        self.hydrograph.clf()
        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)

    def draw_hydrograph(self):
        if self.dmngr.wldataset_count() == 0:
            msg = 'Please import a valid water level data file first.'
            self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
            self.emit_warning(msg)
            return

        self.update_graph_layout_parameter()

        # Generate and Display Graph :

        for i in range(5):
            QCoreApplication.processEvents()

        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.hydrograph.set_wldset(self.dmngr.get_current_wldset())
        self.hydrograph.set_wxdset(self.dmngr.get_current_wxdset())
        self.hydrograph.generate_hydrograph()

        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)

        QApplication.restoreOverrideCursor()

    def select_save_path(self):
        """
        Open a dialog where the user can select a file name to save the
        hydrograph.
        """
        if self.wldset is None:
            return

        ffmat = "*.pdf;;*.svg;;*.png"
        fname = find_unique_filename(osp.join(
            get_select_file_dialog_dir(),
            'hydrograph_{}.pdf'.format(self.wldset['Well'])))

        fname, ftype = QFileDialog.getSaveFileName(
            self, "Save Figure", fname, ffmat)
        if fname:
            ftype = ftype.replace('*', '')
            fname = fname if fname.endswith(ftype) else fname + ftype
            set_select_file_dialog_dir(os.path.dirname(fname))

            try:
                self.save_figure(fname)
            except PermissionError:
                msg = "The file is in use by another application or user."
                QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
                self.select_save_path()

    # ---- Graph Layout Handlers
    def load_layout_isClicked(self):
        """Handle when the button to load the graph layout is clicked."""
        if self.wldset is None:
            self.emit_warning(
                "Please import a valid water level data file first.")
            return

        layout = self.wldset.get_layout()
        if layout is None:
            self.emit_warning(
                "No graph layout exists for well %s." % self.wldset['Well'])
        else:
            self.load_graph_layout(layout)

    def load_graph_layout(self, layout):
        """Load the graph layout into the GUI."""

        self.__updateUI = False

        # Scales :

        date = layout['TIMEmin']
        date = xldate_as_tuple(date, 0)
        self.date_start_widget.setDate(QDate(date[0], date[1], date[2]))

        date = layout['TIMEmax']
        date = xldate_as_tuple(date, 0)
        self.date_end_widget.setDate(QDate(date[0], date[1], date[2]))

        self.dateDispFreq_spinBox.setValue(layout['date_labels_pattern'])

        self.waterlvl_scale.setValue(layout['WLscale'])
        self.waterlvl_max.setValue(layout['WLmin'])
        self.NZGridWL_spinBox.setValue(layout['NZGrid'])
        self.Ptot_scale.setValue(layout['RAINscale'])

        x = ['mbgs', 'masl'].index(layout['WLdatum'])
        self.datum_widget.setCurrentIndex(x)

        self.qweather_bin.setCurrentIndex(layout['bwidth_indx'])
        self.time_scale_label.setCurrentIndex(
            self.time_scale_label.findText(layout['datemode']))

        # ---- Language and colors
        self.btn_language.set_language(layout['language'])
        self.color_palette_win.load_colors()

        # ---- Page Setup

        self.page_setup_win.pageSize = (layout['fwidth'], layout['fheight'])
        self.page_setup_win.va_ratio = layout['va_ratio']
        self.page_setup_win.isLegend = layout['legend_on']
        self.page_setup_win.isGraphTitle = layout['title_on']
        self.page_setup_win.isTrendLine = layout['trend_line']
        self.page_setup_win.is_meteo_on = layout['meteo_on']
        self.page_setup_win.is_glue_wl_on = layout['glue_wl_on']
        self.page_setup_win.is_mrc_wl_on = layout['mrc_wl_on']
        self.page_setup_win.figframe_lw = layout['figframe_lw']

        self.page_setup_win.legend_on.set_value(layout['legend_on'])
        self.page_setup_win.title_on.set_value(layout['title_on'])
        self.page_setup_win.wltrend_on.set_value(layout['trend_line'])
        self.page_setup_win.meteo_on.set_value(layout['meteo_on'])
        self.page_setup_win.glue_wl_on.set_value(layout['glue_wl_on'])
        self.page_setup_win.mrc_wl_on.set_value(layout['mrc_wl_on'])
        self.page_setup_win.fframe_lw_widg.setValue(layout['figframe_lw'])

        self.page_setup_win.fwidth.setValue(layout['fwidth'])
        self.page_setup_win.fheight.setValue(layout['fheight'])
        self.page_setup_win.va_ratio_spinBox.setValue(layout['va_ratio'])

        # Check if Weather Dataset :

        if layout['wxdset'] in self.dmngr.wxdsets:
            self.dmngr.set_current_wxdset(layout['wxdset'])
        else:
            if self.dmngr.set_closest_wxdset() is None:
                self.draw_hydrograph()
        self.__updateUI = True

    def save_layout_isClicked(self):
        wldset = self.wldset
        if wldset is None:
            self.emit_warning(
                "Please import a valid water level data file first.")
            return

        layout = wldset.get_layout()
        if layout is not None:
            msg = ('A graph layout already exists for well %s.Do you want to'
                   ' you want to replace it?') % wldset['Well']
            reply = QMessageBox.question(self, 'Save Graph Layout', msg,
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.save_graph_layout()
            elif reply == QMessageBox.No:
                msg = "Graph layout not saved for well %s." % wldset['Well']
                self.ConsoleSignal.emit('<font color=black>%s' % msg)
        else:
            self.save_graph_layout()

    def save_graph_layout(self):
        """Save the graph layout in the project hdf5 file."""
        print("Saving the graph layout for well %s..." % self.wldset['Well'],
              end=" ")

        layout = {'WLmin': self.waterlvl_max.value(),
                  'WLscale': self.waterlvl_scale.value(),
                  'RAINscale': self.Ptot_scale.value(),
                  'fwidth': self.page_setup_win.pageSize[0],
                  'fheight': self.page_setup_win.pageSize[1],
                  'va_ratio': self.page_setup_win.va_ratio,
                  'NZGrid': self.NZGridWL_spinBox.value(),
                  'bwidth_indx': self.qweather_bin.currentIndex(),
                  'date_labels_pattern': self.dateDispFreq_spinBox.value(),
                  'datemode': self.time_scale_label.currentText()}
        layout['wxdset'] = None if self.wxdset is None else self.wxdset.name

        year = self.date_start_widget.date().year()
        month = self.date_start_widget.date().month()
        layout['TIMEmin'] = xldate_from_date_tuple((year, month, 1), 0)

        year = self.date_end_widget.date().year()
        month = self.date_end_widget.date().month()
        layout['TIMEmax'] = xldate_from_date_tuple((year, month, 1), 0)

        if self.datum_widget.currentIndex() == 0:
            layout['WLdatum'] = 'mbgs'
        else:
            layout['WLdatum'] = 'masl'

        # ---- Page Setup

        layout['title_on'] = bool(self.page_setup_win.isGraphTitle)
        layout['legend_on'] = bool(self.page_setup_win.isLegend)
        layout['language'] = self.btn_language.language
        layout['trend_line'] = bool(self.page_setup_win.isTrendLine)
        layout['meteo_on'] = bool(self.page_setup_win.is_meteo_on)
        layout['glue_wl_on'] = bool(self.page_setup_win.is_glue_wl_on)
        layout['mrc_wl_on'] = bool(self.page_setup_win.is_mrc_wl_on)
        layout['figframe_lw'] = self.page_setup_win.figframe_lw

        # Save the colors :

        cdb = ColorsManager()
        layout['colors'] = cdb.RGB

        # Save the layout :

        self.wldset.save_layout(layout)
        msg = 'Layout saved successfully for well %s.' % self.wldset['Well']
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
        print("done")


class PageSetupWin(QWidget):

    newPageSetupSent = QSignal(bool)

    def __init__(self, parent=None):
        super(PageSetupWin, self).__init__(parent)

        self.setWindowTitle('Page and Figure Setup')
        self.setWindowIcon(get_icon('master'))
        self.setWindowFlags(Qt.Window |
                            Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        # ---- Default Values ----

        self.pageSize = (11, 7)
        self.isLegend = True
        self.isGraphTitle = True
        self.isTrendLine = False
        self.is_meteo_on = True
        self.is_glue_wl_on = False
        self.is_mrc_wl_on = False
        self.va_ratio = 0.2
        self.figframe_lw = 0

        self.__initUI__()

    def __initUI__(self):

        # ---- Toolbar ----

        toolbar_widget = QWidget()

        self.btn_apply = btn_apply = QPushButton('Apply')
        btn_apply.clicked.connect(self.btn_apply_isClicked)
        self.btn_cancel = btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self.close)
        self.btn_OK = btn_OK = QPushButton('OK')
        btn_OK.clicked.connect(self.btn_OK_isClicked)

        toolbar_layout = QGridLayout()
        toolbar_layout.addWidget(btn_OK, 0, 1)
        toolbar_layout.addWidget(btn_cancel, 0, 2)
        toolbar_layout.addWidget(btn_apply, 0, 3)
        toolbar_layout.setColumnStretch(0, 100)

        toolbar_widget.setLayout(toolbar_layout)

        # ---- Main Layout

        main_layout = QGridLayout()
        main_layout.addWidget(self._setup_figure_layout_grpbox(), 0, 0)
        main_layout.addWidget(self._setup_element_visibility_grpbox(), 1, 0)
        main_layout.setRowStretch(2, 100)
        main_layout.setRowMinimumHeight(2, 15)
        main_layout.addWidget(toolbar_widget, 3, 0)

        self.setLayout(main_layout)

    def _setup_figure_layout_grpbox(self):
        """
        Setup a groupbox containing various widget to control the layout
        of the figure.
        """
        self.fwidth = QDoubleSpinBox()
        self.fwidth.setSingleStep(0.05)
        self.fwidth.setMinimum(5.)
        self.fwidth.setValue(self.pageSize[0])
        self.fwidth.setSuffix('  in')
        self.fwidth.setAlignment(Qt.AlignCenter)
        self.fwidth.label = "Figure Width"

        self.fheight = QDoubleSpinBox()
        self.fheight.setSingleStep(0.05)
        self.fheight.setMinimum(5.)
        self.fheight.setValue(self.pageSize[1])
        self.fheight.setSuffix('  in')
        self.fheight.setAlignment(Qt.AlignCenter)
        self.fheight.label = "Figure Heigh"

        self.va_ratio_spinBox = QDoubleSpinBox()
        self.va_ratio_spinBox.setSingleStep(0.01)
        self.va_ratio_spinBox.setMinimum(0.1)
        self.va_ratio_spinBox.setMaximum(0.95)
        self.va_ratio_spinBox.setValue(self.va_ratio)
        self.va_ratio_spinBox.setAlignment(Qt.AlignCenter)
        self.va_ratio_spinBox.label = "Top/Bottom Axes Ratio"

        self.fframe_lw_widg = QDoubleSpinBox()
        self.fframe_lw_widg.setSingleStep(0.1)
        self.fframe_lw_widg.setDecimals(1)
        self.fframe_lw_widg.setMinimum(0)
        self.fframe_lw_widg.setMaximum(99.9)
        self.fframe_lw_widg.setSuffix('  pt')
        self.fframe_lw_widg.setAlignment(Qt.AlignCenter)
        self.fframe_lw_widg.label = "Frame Thickness"
        self.fframe_lw_widg.setValue(self.figframe_lw)

        # Setup the layout of the groupbox.

        grpbox = QGroupBox("Figure Size :")
        layout = QGridLayout(grpbox)
        widgets = [self.fwidth, self.fheight, self.va_ratio_spinBox,
                   self.fframe_lw_widg]
        for row, widget in enumerate(widgets):
            layout.addWidget(QLabel("%s :" % widget.label), row, 0)
            layout.addWidget(widget, row, 2)

        layout.setColumnStretch(1, 100)
        layout.setContentsMargins(10, 10, 10, 10)
        return grpbox

    def _setup_element_visibility_grpbox(self):
        """
        Setup a groupbox containing all the options to set the visibility of
        various elements of the graph.
        """
        # Legend

        self.legend_on = OnOffToggleWidget('Legend', True)
        self.title_on = OnOffToggleWidget('Figure Title', True)
        self.wltrend_on = OnOffToggleWidget('Water Level Trend', False)
        self.meteo_on = OnOffToggleWidget('Weather Data', True)
        self.glue_wl_on = OnOffToggleWidget('GLUE Water Levels', False)
        self.mrc_wl_on = OnOffToggleWidget('MRC Water Levels', False)

        grpbox = QGroupBox("Graph Components Visibility :")
        layout = QGridLayout(grpbox)
        for i, widget in enumerate([self.legend_on, self.title_on,
                                    self.wltrend_on, self.meteo_on,
                                    self.glue_wl_on, self.mrc_wl_on]):
            layout.addWidget(widget, i, 0)
        layout.setContentsMargins(10, 10, 10, 10)

        return grpbox

    # ---- Handlers

    def btn_OK_isClicked(self):
        """Apply the selected settings and close the window."""
        self.btn_apply_isClicked()
        self.close()

    def btn_apply_isClicked(self):
        """Apply the selected settings and emit a signal."""
        self.pageSize = (self.fwidth.value(), self.fheight.value())
        self.isLegend = self.legend_on.value()
        self.isGraphTitle = self.title_on.value()
        self.isTrendLine = self.wltrend_on.value()
        self.is_meteo_on = self.meteo_on.value()
        self.is_glue_wl_on = self.glue_wl_on.value()
        self.is_mrc_wl_on = self.mrc_wl_on.value()
        self.va_ratio = self.va_ratio_spinBox.value()
        self.figframe_lw = self.fframe_lw_widg.value()

        self.newPageSetupSent.emit(True)

    def closeEvent(self, event):
        """Qt method override."""
        super(PageSetupWin, self).closeEvent(event)

        # ---- Refresh UI ----

        # If cancel or X is clicked, the parameters will be reset to
        # the values they had the last time "Accept" button was
        # clicked.

        self.fwidth.setValue(self.pageSize[0])
        self.fheight.setValue(self.pageSize[1])
        self.va_ratio_spinBox.setValue(self.va_ratio)
        self.fframe_lw_widg.setValue(self.figframe_lw)

        self.legend_on.set_value(self.isLegend)
        self.title_on.set_value(self.isGraphTitle)
        self.wltrend_on.set_value(self.isTrendLine)
        self.meteo_on.set_value(self.is_meteo_on)
        self.glue_wl_on.set_value(self.is_glue_wl_on)
        self.mrc_wl_on.set_value(self.is_mrc_wl_on)

    def show(self):
        """Qt method override."""
        super(PageSetupWin, self).show()
        self.activateWindow()
        self.raise_()

        qr = self.frameGeometry()
        if self.parentWidget():
            parent = self.parentWidget()

            wp = parent.frameGeometry().width()
            hp = parent.frameGeometry().height()
            cp = parent.mapToGlobal(QPoint(wp // 2, hp // 2))
        else:
            cp = QDesktopWidget().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setMinimumSize(self.size())
        self.setFixedSize(self.size())


# %% if __name__ == '__main__'

if __name__ == '__main__':
    from projet.manager_data import DataManager
    from projet.reader_projet import ProjetReader
    from gwhat.qthelpers import create_qapplication
    app = create_qapplication(ft_ptsize=10, ft_family='Segoe UI')

    pf = ("C:\\Users\\User\\gwhat\\Projects\\Example\\Example.gwt")
    pr = ProjetReader(pf)
    dm = DataManager()
    dm.set_projet(pr)

    Hydroprint = HydroprintGUI(dm)
    Hydroprint.show()
    Hydroprint.wldset_changed()

    sys.exit(app.exec_())
