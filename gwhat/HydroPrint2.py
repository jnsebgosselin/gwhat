# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# ---- Standard library imports

import sys
import os

# ---- Third party imports

from PyQt5.QtCore import Qt, QDate, QCoreApplication, QPoint
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (QSpinBox, QDoubleSpinBox, QWidget, QDateEdit,
                             QAbstractSpinBox, QGridLayout, QFrame,
                             QMessageBox, QComboBox, QLabel, QTabWidget,
                             QFileDialog, QApplication, QPushButton,
                             QRadioButton, QDesktopWidget, QGroupBox)

from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

# ---- Imports: local

import gwhat.hydrograph4 as hydrograph
import gwhat.mplFigViewer3 as mplFigViewer
from gwhat.meteo.weather_viewer import WeatherAvgGraph
from gwhat.colors2 import ColorsReader, ColorsSetupWin

from gwhat.common import QToolButtonNormal, QToolButtonSmall
from gwhat.common import icons
import gwhat.common.widgets as myqt
from gwhat.projet.reader_waterlvl import load_waterlvl_measures


class HydroprintGUI(myqt.DialogWindow):

    ConsoleSignal = QSignal(str)

    def __init__(self, datamanager, parent=None):
        super(HydroprintGUI, self).__init__(parent, maximize=True)

        self.__updateUI = True

        # Child widgets:

        self.dmngr = datamanager
        self.dmngr.wldsetChanged.connect(self.wldset_changed)
        self.dmngr.wxdsetChanged.connect(self.wxdset_changed)

        self.weather_avg_graph = WeatherAvgGraph(self)

        self.page_setup_win = PageSetupWin(self)
        self.page_setup_win.newPageSetupSent.connect(self.layout_changed)

        self.color_palette_win = ColorsSetupWin(self)
        self.color_palette_win.newColorSetupSent.connect(self.update_colors)

        # Memory path variable:

        self.save_fig_dir = self.workdir

        # Generate UI:

        self.__initUI__()

    def __initUI__(self):

        # ---- Toolbar

        self.btn_save = btn_save = QToolButtonNormal(icons.get_icon('save'))
        btn_save.setToolTip('Save the well hydrograph')

        # btn_draw is usefull for debugging purposes
        btn_draw = QToolButtonNormal(icons.get_icon('refresh'))
        btn_draw.setToolTip('Force a refresh of the well hydrograph')
        btn_draw.hide()

        self.btn_load_layout = QToolButtonNormal(
                icons.get_icon('load_graph_config'))
        self.btn_load_layout.setToolTip(
                "<p>Load graph layout for the current water level "
                " datafile if it exists</p>")
        self.btn_load_layout.clicked.connect(self.load_layout_isClicked)

        self.btn_save_layout = QToolButtonNormal(
                icons.get_icon('save_graph_config'))
        self.btn_save_layout.setToolTip('Save current graph layout')
        self.btn_save_layout.clicked.connect(self.save_layout_isClicked)

        btn_bestfit_waterlvl = QToolButtonNormal(icons.get_icon('fit_y'))
        btn_bestfit_waterlvl.setToolTip('Best fit the water level scale')

        btn_bestfit_time = QToolButtonNormal(icons.get_icon('fit_x'))
        btn_bestfit_time.setToolTip('Best fit the time scale')

        btn_weather_normals = QToolButtonNormal(icons.get_icon('meteo'))
        btn_weather_normals.setToolTip(
                'Show current weather dataset normals...')

        self.btn_page_setup = QToolButtonNormal(icons.get_icon('page_setup'))
        self.btn_page_setup.setToolTip('Show the page setup window')
        self.btn_page_setup.clicked.connect(self.page_setup_win.show)

        btn_color_pick = QToolButtonNormal(icons.get_icon('color_picker'))
        btn_color_pick.setToolTip('<p>Show a window to setup the color palette'
                                  ' used to draw the hydrograph</p.')
        btn_color_pick.clicked.connect(self.color_palette_win.show)

        # ---- Zoom Panel

        btn_zoom_out = QToolButtonSmall(icons.get_icon('zoom_out'))
        btn_zoom_out.setToolTip('Zoom out (ctrl + mouse-wheel-down)')
        btn_zoom_out.clicked.connect(self.zoom_out)

        btn_zoom_in = QToolButtonSmall(icons.get_icon('zoom_in'))
        btn_zoom_out.setToolTip('Zoom in (ctrl + mouse-wheel-up)')
        btn_zoom_in.clicked.connect(self.zoom_in)

        self.zoom_disp = QSpinBox()
        self.zoom_disp.setAlignment(Qt.AlignCenter)
        self.zoom_disp.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.zoom_disp.setReadOnly(True)
        self.zoom_disp.setSuffix(' %')
        self.zoom_disp.setRange(0, 9999)
        self.zoom_disp.setValue(100)

        zoom_pan = myqt.QFrameLayout()
        zoom_pan.setSpacing(3)
        zoom_pan.addWidget(btn_zoom_out, 0, 0)
        zoom_pan.addWidget(btn_zoom_in, 0, 1)
        zoom_pan.addWidget(self.zoom_disp, 0, 2)

        # LAYOUT :

        btn_list = [btn_save, btn_draw,
                    self.btn_load_layout, self.btn_save_layout,
                    myqt.VSep(),
                    btn_bestfit_waterlvl, btn_bestfit_time,
                    myqt.VSep(), btn_weather_normals, self.btn_page_setup,
                    btn_color_pick,
                    myqt.VSep(),
                    zoom_pan]

        subgrid_toolbar = QGridLayout()
        toolbar_widget = QWidget()

        row = 0
        for col, btn in enumerate(btn_list):
            subgrid_toolbar.addWidget(btn, row, col)

        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)
        subgrid_toolbar.setColumnStretch(col + 1, 100)

        toolbar_widget.setLayout(subgrid_toolbar)

        # ---- LEFT PANEL

        # SubGrid Hydrograph Frame :

        self.hydrograph = hydrograph.Hydrograph()
        self.hydrograph_scrollarea = mplFigViewer.ImageViewer()
        self.hydrograph_scrollarea.zoomChanged.connect(self.zoom_disp.setValue)

        grid_hydrograph = QGridLayout()
        grid_hydrograph.addWidget(self.hydrograph_scrollarea, 0, 0)
        grid_hydrograph.setRowStretch(0, 500)
        grid_hydrograph.setColumnStretch(0, 500)
        grid_hydrograph.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # ASSEMBLING SubGrids :

        grid_layout = QGridLayout()
        self.grid_layout_widget = QFrame()

        row = 0
        grid_layout.addWidget(toolbar_widget, row, 0)
        row += 1
        grid_layout.addLayout(grid_hydrograph, row, 0)

        grid_layout.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        grid_layout.setSpacing(5)
        grid_layout.setColumnStretch(0, 500)
        grid_layout.setRowStretch(1, 500)

        self.grid_layout_widget.setLayout(grid_layout)

        # ---- Right Panel

        self.tabscales = self.__init_scalesTabWidget__()
        self.qAxeLabelsLanguage = self.__init_labelLangWidget__()

        self.right_panel = myqt.QFrameLayout()
        row = 0
        self.right_panel.addWidget(self.dmngr, row, 0)
        row += 1
        self.right_panel.addWidget(self.tabscales, row, 0)
        row += 1
        self.right_panel.addWidget(self.qAxeLabelsLanguage, 2, 0)
        row += 1
        self.right_panel.setRowStretch(row, 100)

        self.right_panel.setSpacing(15)

        # ---- MAIN GRID

        mainGrid = QGridLayout()

        mainGrid.addWidget(self.grid_layout_widget, 0, 0)
        mainGrid.addWidget(myqt.VSep(), 0, 1)
        mainGrid.addWidget(self.right_panel, 0, 2)

        mainGrid.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)
        mainGrid.setSpacing(15)
        mainGrid.setColumnStretch(0, 500)
        mainGrid.setColumnMinimumWidth(2, 250)

        self.setLayout(mainGrid)

        # ---- EVENTS

        # Toolbox Layout :

        btn_bestfit_waterlvl.clicked.connect(self.best_fit_waterlvl)
        btn_bestfit_time.clicked.connect(self.best_fit_time)
        btn_draw.clicked.connect(self.draw_hydrograph)
        btn_save.clicked.connect(self.select_save_path)
        btn_weather_normals.clicked.connect(self.show_weather_averages)

        # Hydrograph Layout :

        self.language_box.currentIndexChanged.connect(self.layout_changed)
        self.Ptot_scale.valueChanged.connect(self.layout_changed)
        self.qweather_bin.currentIndexChanged.connect(self.layout_changed)

        # ---- Init Image

        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)

    # =========================================================================

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

    def __init_labelLangWidget__(self):  # ------------------------------------

        # Widgets :

        self.language_box = QComboBox()
        self.language_box.setEditable(False)
        self.language_box.setInsertPolicy(QComboBox.NoInsert)
        self.language_box.addItems(['French', 'English'])
        self.language_box.setCurrentIndex(1)

        # Layout :

        layout = QGridLayout()
        layout.addWidget(QLabel('Label Language:'), 0, 0)
        layout.addWidget(self.language_box, 0, 1)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)  # (L, T, R, B)

        qAxeLabelsLanguage = QFrame()
        qAxeLabelsLanguage.setLayout(layout)

        return qAxeLabelsLanguage

    @property
    def workdir(self):
        return self.dmngr.workdir

    # ---- Utilities

    def zoom_in(self):
        self.hydrograph_scrollarea.zoomIn()

    def zoom_out(self):
        self.hydrograph_scrollarea.zoomOut()

    def update_colors(self):
        self.hydrograph.update_colors()
        self.hydrograph_scrollarea.load_mpl_figure(self.hydrograph)

    def show_weather_averages(self):
        if self.wxdset is None:
            msg = 'Please import a valid weather data file first.'
            self.emit_warning(msg)
            return

        self.weather_avg_graph.save_fig_dir = self.workdir
        self.weather_avg_graph.generate_graph(self.wxdset)
        self.weather_avg_graph.show()

    # ---- Datasets Handlers

    @property
    def wldset(self):
        return self.dmngr.get_current_wldset()

    @property
    def wxdset(self):
        return self.dmngr.get_current_wxdset()

    def wldset_changed(self):
        """Handles when the water level dataset of the datamanager changed."""
        if self.wxdset is None or self.wldset is None:
            self.clear_hydrograph()
            return
        else:
            wldset = self.wldset
            self.hydrograph.set_wldset(wldset)

        # Load Manual Measures :

        fname = os.path.join(self.workdir, "Water Levels",
                             'waterlvl_manual_measurements')
        tmeas, wlmeas = load_waterlvl_measures(fname, wldset['Well'])
        wldset.set_wlmeas(tmeas, wlmeas)

        # Hydrograph Layout :

        layout = wldset.get_layout()
        if layout is not None:
            msg = 'Loading existing graph layout for well %s.' % wldset['Well']
            print(msg)
            self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
            self.load_graph_layout(layout)
        else:
            print('No graph layout exists for well %s.' % wldset['Well'])
            # Fit Water Level in Layout :
            self.__updateUI = False
            self.best_fit_waterlvl()
            self.best_fit_time()
            self.dmngr.set_closest_wxdset()
            self.__updateUI = True

    def wxdset_changed(self):
        """Handles when the weather dataset of the datamanager changed."""
        if self.wxdset is None or self.wldset is None:
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
            date0, date1 = self.hydrograph.best_fit_time(wldset['Time'])
            self.date_start_widget.setDate(QDate(date0[0], date0[1], date0[2]))
            self.date_end_widget.setDate(QDate(date1[0], date1[1], date1[2]))

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

        if sender == self.language_box:
            self.hydrograph.draw_ylabels()
            self.hydrograph.draw_xlabels()
            self.hydrograph.set_legend()

        elif sender in [self.waterlvl_max, self.waterlvl_scale]:
            self.hydrograph.update_waterlvl_scale()
            self.hydrograph.draw_ylabels()

        elif sender == self.NZGridWL_spinBox:
            self.hydrograph.update_waterlvl_scale()
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

            self.hydrograph.update_waterlvl_scale()
            self.hydrograph.draw_waterlvl()
            self.hydrograph.draw_ylabels()

        elif sender in [self.date_start_widget, self.date_end_widget]:
            self.hydrograph.set_time_scale()
            self.hydrograph.draw_weather()
            self.hydrograph.draw_figure_title()

        elif sender == self.dateDispFreq_spinBox:
            self.hydrograph.set_time_scale()
            self.hydrograph.draw_xlabels()

        elif sender == self.page_setup_win:
            self.hydrograph.update_fig_size()
            # Implicitly call : set_margins()
            #                   draw_ylabels()
            #                   set_time_scale()
            #                   draw_figure_title

            self.hydrograph.draw_waterlvl()
            self.hydrograph.set_legend()

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

        if self.dmngr.wxdataset_count() == 0:
            msg = 'Please import a valid weather data file first.'
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
        Opens a dialog which allows to select a file path where the hydrograph
        figure can be saved.
        """
        dialog_dir = os.path.join(self.save_fig_dir,
                                  'hydrograph_%s' % self.wldset['Well'])

        dialog = QFileDialog()
        fname, ftype = dialog.getSaveFileName(
                self, "Save Figure", dialog_dir, '*.pdf;;*.svg')
        ftype = ftype.replace('*', '')
        if fname:
            if not fname.endswith(ftype):
                fname = fname + ftype
            self.save_fig_dir = os.path.dirname(fname)
            self.save_figure(fname)

    def save_figure(self, fname):
        """Save the hydrograph figure in a file."""
        self.hydrograph.generate_hydrograph()
        self.hydrograph.savefig(fname)

    # ---- Graph Layout Handlers

    def load_layout_isClicked(self):
        if self.wldset is None:
            msg = 'Please import a valid water level data file first.'
            self.emit_warning(msg)
            return

        layout = self.wldset.get_layout()
        if layout is None:
            msg = 'No graph layout exists for well %s.' % self.wldset['Well']
            self.emit_warning(msg)
        else:
            self.load_graph_layout(layout)

    def load_graph_layout(self, layout):

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

        # Color Palette :

        self.color_palette_win.load_colors()

        # Page Setup :

        self.page_setup_win.pageSize = (layout['fwidth'], layout['fheight'])
        self.page_setup_win.va_ratio = layout['va_ratio']
        self.page_setup_win.isLegend = layout['legend_on']
        self.page_setup_win.isGraphTitle = layout['title_on']
        self.page_setup_win.isTrendLine = layout['trend_line']

        if layout['title_on'] is True:
            self.page_setup_win.title_on.toggle()
        else:
            self.page_setup_win.title_off.toggle()

        if layout['legend_on'] is True:
            self.page_setup_win.legend_on.toggle()
        else:
            self.page_setup_win.legend_off.toggle()

        if layout['trend_line'] is True:
            self.page_setup_win.trend_on.toggle()
        else:
            self.page_setup_win.trend_off.toggle()

        self.page_setup_win.fwidth.setValue(layout['fwidth'])
        self.page_setup_win.fheight.setValue(layout['fheight'])
        self.page_setup_win.va_ratio_spinBox.setValue(layout['va_ratio'])

        # Check if Weather Dataset :

        if layout['wxdset'] in self.dmngr.wxdsets:
            self.dmngr.set_current_wxdset(layout['wxdset'])
        else:
            self.dmngr.set_closest_wxdset()

        self.__updateUI = True

    def save_layout_isClicked(self):
        wldset = self.wldset
        if wldset is None:
            msg = 'Please import a valid water level data file first.'
            self.emit_warning(msg)
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
        """Saves the graph layout in the project hdf5 file."""
        print("Saving the graph layout for well %s..." % self.wldset['Well'],
              end=" ")

        layout = {'wxdset': self.wxdset.name,
                  'WLmin': self.waterlvl_max.value(),
                  'WLscale': self.waterlvl_scale.value(),
                  'RAINscale': self.Ptot_scale.value(),
                  'fwidth': self.page_setup_win.pageSize[0],
                  'fheight': self.page_setup_win.pageSize[1],
                  'va_ratio': self.page_setup_win.va_ratio,
                  'NZGrid': self.NZGridWL_spinBox.value(),
                  'bwidth_indx': self.qweather_bin.currentIndex(),
                  'date_labels_pattern': self.dateDispFreq_spinBox.value(),
                  'datemode': self.time_scale_label.currentText()}

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

        layout['title_on'] = str(bool(self.page_setup_win.isGraphTitle))
        layout['legend_on'] = str(bool(self.page_setup_win.isLegend))
        layout['language'] = self.language_box.currentText()
        layout['trend_line'] = str(bool(self.page_setup_win.isTrendLine))

        # Save the colors :

        cdb = ColorsReader()
        cdb.load_colors_db()
        layout['colors'] = cdb.RGB

        # Save the layout :

        self.wldset.save_layout(layout)
        msg = 'Layout saved successfully for well %s.' % self.wldset['Well']
        self.ConsoleSignal.emit('<font color=black>%s</font>' % msg)
        print("done")

    def update_graph_layout_parameter(self):

        # language :

        self.hydrograph.language = self.language_box.currentText()
        self.weather_avg_graph.set_lang(self.language_box.currentText())

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

        # Weather bins :

        self.hydrograph.bwidth_indx = self.qweather_bin.currentIndex()


class PageSetupWin(QWidget):

    newPageSetupSent = QSignal(bool)

    def __init__(self, parent=None):
        super(PageSetupWin, self).__init__(parent)

        self.setWindowTitle('Page and Figure Setup')
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowFlags(Qt.Window |
                            Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        # ---- Default Values ----

        self.pageSize = (11, 7)
        self.isLegend = True
        self.isGraphTitle = True
        self.isTrendLine = False
        self.va_ratio = 0.2

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

        # ---- Figure Size GroupBox

        self.fwidth = QDoubleSpinBox()
        self.fwidth.setSingleStep(0.05)
        self.fwidth.setMinimum(5.)
        self.fwidth.setValue(self.pageSize[0])
        self.fwidth.setSuffix('  in')
        self.fwidth.setAlignment(Qt.AlignCenter)

        self.fheight = QDoubleSpinBox()
        self.fheight.setSingleStep(0.05)
        self.fheight.setMinimum(5.)
        self.fheight.setValue(self.pageSize[1])
        self.fheight.setSuffix('  in')
        self.fheight.setAlignment(Qt.AlignCenter)

        self.va_ratio_spinBox = QDoubleSpinBox()
        self.va_ratio_spinBox.setSingleStep(0.01)
        self.va_ratio_spinBox.setMinimum(0.1)
        self.va_ratio_spinBox.setMaximum(0.95)
        self.va_ratio_spinBox.setValue(self.va_ratio)
        self.va_ratio_spinBox.setAlignment(Qt.AlignCenter)

        # GroupBox Layout

        figsize_grpbox = QGroupBox("Figure Size :")
        figSize_layout = QGridLayout(figsize_grpbox)
        row = 0
        figSize_layout.addWidget(QLabel('Figure Width :'), row, 0)
        figSize_layout.addWidget(self.fwidth, row, 2)
        row += 1
        figSize_layout.addWidget(QLabel('Figure Height :'), row, 0)
        figSize_layout.addWidget(self.fheight, row, 2)
        row += 1
        figSize_layout.addWidget(QLabel('Top/Bottom Axes Ratio :'), row, 0)
        figSize_layout.addWidget(self.va_ratio_spinBox, row, 2)

        figSize_layout.setColumnStretch(1, 100)
        figSize_layout.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        # ---- Graph Element Visibility GroupBox

        # Legend

        self.legend_on = QRadioButton('On')
        self.legend_on.toggle()
        self.legend_off = QRadioButton('Off')

        legend_grpwidget = QWidget()
        legend_layout = QGridLayout(legend_grpwidget)
        legend_layout.addWidget(QLabel('Legend :'), 0, 0)
        legend_layout.addWidget(self.legend_on, 0, 2)
        legend_layout.addWidget(self.legend_off, 0, 3)
        legend_layout.setColumnStretch(1, 100)
        legend_layout.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # Graph title

        self.title_on = QRadioButton('On')
        self.title_on.toggle()
        self.title_off = QRadioButton('Off')

        title_grpwidget = QWidget()
        title_layout = QGridLayout(title_grpwidget)
        title_layout.addWidget(QLabel('Graph Title :'), 0, 0)
        title_layout.addWidget(self.title_on, 0, 2)
        title_layout.addWidget(self.title_off, 0, 3)
        title_layout.setColumnStretch(1, 100)
        title_layout.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # Trend Line

        self.trend_on = QRadioButton('On')
        self.trend_off = QRadioButton('Off')
        self.trend_off.toggle()

        trend_grpwidget = QWidget()
        trend_layout = QGridLayout(trend_grpwidget)
        trend_layout.addWidget(QLabel('Water Level Trend :'), 0, 0)
        trend_layout.addWidget(self.trend_on, 0, 2)
        trend_layout.addWidget(self.trend_off, 0, 3)
        trend_layout.setColumnStretch(1, 100)
        trend_layout.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # GroupBox Layout

        eleviz_grpbox = QGroupBox("Graph Components Visibility :")
        eleviz_layout = QGridLayout(eleviz_grpbox)
        eleviz_layout.addWidget(legend_grpwidget, 0, 0)
        eleviz_layout.addWidget(title_grpwidget, 1, 0)
        eleviz_layout.addWidget(trend_grpwidget, 2, 0)

        eleviz_layout.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        # ---- Main Layout

        main_layout = QGridLayout()
        main_layout.addWidget(figsize_grpbox, 0, 0)
        main_layout.addWidget(eleviz_grpbox, 1, 0)
        main_layout.setRowStretch(2, 100)
        main_layout.setRowMinimumHeight(2, 15)
        main_layout.addWidget(toolbar_widget, 3, 0)

        self.setLayout(main_layout)

    # ---- Handlers

    def btn_OK_isClicked(self):
        self.btn_apply_isClicked()
        self.close()

    def btn_apply_isClicked(self):
        self.pageSize = (self.fwidth.value(), self.fheight.value())
        self.isLegend = self.legend_on.isChecked()
        self.isGraphTitle = self.title_on.isChecked()
        self.isTrendLine = self.trend_on.isChecked()
        self.va_ratio = self.va_ratio_spinBox.value()

        self.newPageSetupSent.emit(True)

    def closeEvent(self, event):
        super(PageSetupWin, self).closeEvent(event)

        # ---- Refresh UI ----

        # If cancel or X is clicked, the parameters will be reset to
        # the values they had the last time "Accept" button was
        # clicked.

        self.fwidth.setValue(self.pageSize[0])
        self.fheight.setValue(self.pageSize[1])
        self.va_ratio_spinBox.setValue(self.va_ratio)

        if self.isLegend is True:
            self.legend_on.toggle()
        else:
            self.legend_off.toggle()

        if self.isGraphTitle is True:
            self.title_on.toggle()
        else:
            self.title_off.toggle()

        if self.isTrendLine is True:
            self.trend_on.toggle()
        else:
            self.trend_off.toggle()

    def show(self):
        super(PageSetupWin, self).show()
        self.activateWindow()
        self.raise_()

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
        self.setMinimumSize(self.size())
        self.setFixedSize(self.size())


# %% if __name__ == '__main__'

if __name__ == '__main__':
    from projet.manager_data import DataManager
    from projet.reader_projet import ProjetReader
    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

    pf = ("C:/Users/jsgosselin/GWHAT/gwhat/tests/"
          "@ new-prô'jèt!/@ new-prô'jèt!.gwt")
    pr = ProjetReader(pf)
    dm = DataManager()
    dm.set_projet(pr)

    Hydroprint = HydroprintGUI(dm)
    Hydroprint.show()
    Hydroprint.wldset_changed()

    sys.exit(app.exec_())
