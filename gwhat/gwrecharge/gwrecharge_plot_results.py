# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports

import os
import os.path as osp

# ---- Imports: third parties

import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure as MPLFigure

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (
    QGridLayout, QAbstractSpinBox, QApplication, QComboBox, QDoubleSpinBox,
    QFileDialog, QGroupBox, QLabel, QMessageBox, QScrollArea, QScrollBar,
    QSizePolicy, QSpinBox, QTabWidget, QToolBar, QVBoxLayout, QWidget, QStyle)


# ---- Imports: local

from gwhat.gwrecharge.glue import (
    calcul_glue, calcul_hydro_yrly_budget)
from gwhat.common import icons, QToolButtonNormal, QToolButtonSmall
from gwhat.common.utils import find_unique_filename
from gwhat.common.widgets import QFrameLayout
from gwhat.mplFigViewer3 import ImageViewer

mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Arial']})
LOCS = ['left', 'top', 'right', 'bottom']
LANGUAGES = ['French', 'English']


class FigureStackManager(QWidget):
    def __init__(self, parent=None):
        super(FigureStackManager, self).__init__(parent)
        self.setMinimumSize(1250, 650)
        self.setWindowTitle('Recharge Results')
        self.setWindowFlags(Qt.Window)
        self.setWindowIcon(icons.get_icon('master'))

        self.setup()

    def setup(self):
        """Setup the FigureStackManager withthe provided options."""
        self.setup_stack()
        layout = QGridLayout(self)
        layout.addWidget(self.stack, 0, 0)

    def setup_stack(self):
        self.fig_wl_glue = FigManagerBase(
            FigWaterLevelGLUE,
            setp_panels=[FigSizePanel(),
                         MarginSizePanel()])
        self.fig_rechg_glue = FigManagerBase(
            FigYearlyRechgGLUE,
            setp_panels=[FigSizePanel(),
                         MarginSizePanel(),
                         YAxisOptPanel(),
                         YearLimitsPanel(),
                         TextOptPanel()])
        self.fig_watbudg_glue = FigManagerBase(
            FigWaterBudgetGLUE,
            setp_panels=[FigSizePanel(),
                         MarginSizePanel(),
                         YAxisOptPanel(),
                         YearLimitsPanel(),
                         TextOptPanel()])

        self.stack = QTabWidget()
        self.stack.addTab(self.fig_wl_glue, 'Hydrograph')
        self.stack.addTab(self.fig_rechg_glue, 'Recharge')
        self.stack.addTab(self.fig_watbudg_glue, 'Water Budget')

    def plot_results(self, glue_df):
        self.fig_wl_glue.figcanvas.plot(glue_df)
        self.fig_rechg_glue.figcanvas.plot(glue_df)
        self.fig_watbudg_glue.figcanvas.plot(glue_df)


# ---- Figure setp panels

class FigSetpPanelManager(QWidget):
    """
    A widget that hold the panels that contains widget to setup the figure
    layout.
    """

    def __init__(self, figcanvas, parent=None):
        super(FigSetpPanelManager, self).__init__(parent)
        self.figsetp_panels = []
        self.set_figcanvas(figcanvas)
        self.setup()

    def setup(self):
        """Setup the main layout of the widget."""
        self.view = QWidget()

        self.scrollarea = QScrollArea()
        self.scrollarea.setWidget(self.view)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # This is required to avoid a "RuntimeError: no access to protected
        # functions or signals for objects not created from Python" in Linux.
        self.scrollarea.setVerticalScrollBar(QScrollBar())

        self.scene = QGridLayout(self.view)
        self.scene.setColumnStretch(1, 100)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.scrollarea)

    def set_figcanvas(self, figcanvas):
        """Set the namespace for the FigureCanvas."""
        self.figcanvas = figcanvas

    def add_figsetp_panel(self, figsetp_panel):
        self.figsetp_panels.append(figsetp_panel)
        figsetp_panel.register_figcanvas(self.figcanvas)

        self.scene.setRowStretch(self.scene.rowCount()-1, 0)
        self.scene.addWidget(figsetp_panel, self.scene.rowCount()-1, 1)
        self.scene.setRowStretch(self.scene.rowCount(), 100)


class SetpPanelBase(QWidget):
    def __init__(self, parent=None):
        super(SetpPanelBase, self).__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

    def register_figcanvas(self, figcanvas):
        self.figcanvas = figcanvas
        figcanvas.sig_newfig_plotted.connect(self.update_from_setp)


class MarginSizePanel(SetpPanelBase):
    def __init__(self, parent=None):
        super(MarginSizePanel, self).__init__(parent)
        self.setup()

    def setup(self):
        """Setup the gui of the panel."""
        self.layout().addWidget(self._setup_margins_grpbox())
        self.layout().setRowStretch(self.layout().rowCount(), 100)

    @property
    def fig_margins(self):
        return [self._spb_margins[loc].value() for loc in LOCS]

    def _setup_margins_grpbox(self):
        """
        Setup a group box with spin boxes that allows to set the figure
        margins size in inches.
        """
        grpbox = QGroupBox("Margins Size :")
        layout = QGridLayout(grpbox)

        self._spb_margins = {}
        for row, loc in enumerate(LOCS):
            self._spb_margins[loc] = QDoubleSpinBox()
            self._spb_margins[loc].setSingleStep(0.05)
            self._spb_margins[loc].setMinimum(0)
            self._spb_margins[loc].setSuffix('  in')
            self._spb_margins[loc].setAlignment(Qt.AlignCenter)
            self._spb_margins[loc].setKeyboardTracking(False)
            self._spb_margins[loc].valueChanged.connect(self._margins_changed)

            layout.addWidget(QLabel("%s :" % loc), row, 0)
            layout.addWidget(self._spb_margins[loc], row, 2)
        layout.setColumnStretch(1, 100)
        layout.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        return grpbox

    @QSlot()
    def _margins_changed(self):
        """Handle when one of the margin size is changed by the user."""
        self.figcanvas.set_axes_margins_inches(self.fig_margins)

    @QSlot(dict)
    def update_from_setp(self, setp):
        self._spb_margins['left'].blockSignals(True)
        self._spb_margins['left'].setValue(setp['left margin'])
        self._spb_margins['left'].blockSignals(False)

        self._spb_margins['right'].blockSignals(True)
        self._spb_margins['right'].setValue(setp['right margin'])
        self._spb_margins['right'].blockSignals(False)

        self._spb_margins['top'].blockSignals(True)
        self._spb_margins['top'].setValue(setp['top margin'])
        self._spb_margins['top'].blockSignals(False)

        self._spb_margins['bottom'].blockSignals(True)
        self._spb_margins['bottom'].setValue(setp['bottom margin'])
        self._spb_margins['bottom'].blockSignals(False)


class TextOptPanel(SetpPanelBase):
    def __init__(self, parent=None):
        super(TextOptPanel, self).__init__(parent)
        self.setup()

    def setup(self):
        """Setup the gui of the panel."""
        self.layout().addWidget(self._setup_textprop_grpbox())
        self.layout().setRowStretch(self.layout().rowCount(), 100)

    @QSlot(dict)
    def update_from_setp(self, setp):
        self._spb_xlabelsize.blockSignals(True)
        self._spb_xlabelsize.setValue(setp['xlabel size'])
        self._spb_xlabelsize.blockSignals(False)

        self._spb_xticksize.blockSignals(True)
        self._spb_xticksize.setValue(setp['xticks size'])
        self._spb_xticksize.blockSignals(False)

        self._spb_ylabelsize.blockSignals(True)
        self._spb_ylabelsize.setValue(setp['ylabel size'])
        self._spb_ylabelsize.blockSignals(False)

        self._spb_ylabelsize.blockSignals(True)
        self._spb_ylabelsize.setValue(setp['ylabel size'])
        self._spb_ylabelsize.blockSignals(False)

        self._spb_yticksize.blockSignals(True)
        self._spb_yticksize.setValue(setp['yticks size'])
        self._spb_yticksize.blockSignals(False)

        self._spb_yticksize.blockSignals(True)
        self._spb_legendsize.setValue(setp['legend size'])
        self._spb_yticksize.blockSignals(False)

        self._spb_notesize.blockSignals(True)
        self._spb_notesize.setValue(setp['notes size'])
        self._spb_notesize.blockSignals(False)

    def _setup_textprop_grpbox(self):
        """
        Setup a group box with widgets that allows to set the figure
        text properties.
        """
        self._spb_xlabelsize = QSpinBox()
        self._spb_xlabelsize.setSingleStep(1)
        self._spb_xlabelsize.setMinimum(1)
        self._spb_xlabelsize.setAlignment(Qt.AlignCenter)
        self._spb_xlabelsize.setKeyboardTracking(False)
        self._spb_xlabelsize.valueChanged.connect(self._axes_labels_changed)

        self._spb_xticksize = QSpinBox()
        self._spb_xticksize.setSingleStep(1)
        self._spb_xticksize.setMinimum(1)
        self._spb_xticksize.setAlignment(Qt.AlignCenter)
        self._spb_xticksize.setKeyboardTracking(False)
        self._spb_xticksize.valueChanged.connect(self._ticks_changed)

        self._spb_ylabelsize = QSpinBox()
        self._spb_ylabelsize.setSingleStep(1)
        self._spb_ylabelsize.setMinimum(1)
        self._spb_ylabelsize.setAlignment(Qt.AlignCenter)
        self._spb_ylabelsize.setKeyboardTracking(False)
        self._spb_ylabelsize.valueChanged.connect(self._axes_labels_changed)

        self._spb_yticksize = QSpinBox()
        self._spb_yticksize.setSingleStep(1)
        self._spb_yticksize.setMinimum(1)
        self._spb_yticksize.setAlignment(Qt.AlignCenter)
        self._spb_yticksize.setKeyboardTracking(False)
        self._spb_yticksize.valueChanged.connect(self._ticks_changed)

        self._spb_legendsize = QSpinBox()
        self._spb_legendsize.setSingleStep(1)
        self._spb_legendsize.setMinimum(1)
        self._spb_legendsize.setAlignment(Qt.AlignCenter)
        self._spb_legendsize.setKeyboardTracking(False)
        self._spb_legendsize.valueChanged.connect(self._legend_changed)

        self._spb_notesize = QSpinBox()
        self._spb_notesize.setSingleStep(1)
        self._spb_notesize.setMinimum(1)
        self._spb_notesize.setAlignment(Qt.AlignCenter)
        self._spb_notesize.setKeyboardTracking(False)
        self._spb_notesize.valueChanged.connect(self._notes_changed)

        grpbox = QGroupBox("Text Properties :")
        layout = QGridLayout(grpbox)

        layout.addWidget(QLabel('xlabel size:'), 0, 0)
        layout.addWidget(self._spb_xlabelsize, 0, 2)
        layout.addWidget(QLabel('xticks size:'), 1, 0)
        layout.addWidget(self._spb_xticksize, 1, 2)
        layout.addWidget(QLabel('ylabel size:'), 2, 0)
        layout.addWidget(self._spb_ylabelsize, 2, 2)
        layout.addWidget(QLabel('yticks size:'), 3, 0)
        layout.addWidget(self._spb_yticksize, 3, 2)
        layout.addWidget(QLabel('legend size:'), 4, 0)
        layout.addWidget(self._spb_legendsize, 4, 2)
        layout.addWidget(QLabel('notes size:'), 5, 0)
        layout.addWidget(self._spb_notesize, 5, 2)

        layout.setColumnStretch(1, 100)
        layout.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        return grpbox

    def _legend_changed(self):
        self.figcanvas.set_legend_fontsize(self._spb_legendsize.value())

    def _axes_labels_changed(self):
        self.figcanvas.set_axes_labels_size(
            self._spb_xlabelsize.value(), self._spb_ylabelsize.value())

    def _ticks_changed(self):
        self.figcanvas.set_tick_labels_size(
            self._spb_xticksize.value(), self._spb_yticksize.value())

    def _notes_changed(self):
        self.figcanvas.set_notes_size(self._spb_notesize.value())


class FigSizePanel(SetpPanelBase):

    def __init__(self, parent=None):
        super(FigSizePanel, self).__init__(parent)
        self.setup()

    def setup(self):
        """Setup the gui of the panel."""
        self.layout().addWidget(self._setup_figsize_grpbox())
        self.layout().setRowStretch(self.layout().rowCount(), 100)

    @property
    def fig_width(self):
        return self._spb_fwidth.value()

    @property
    def fig_height(self):
        return self._spb_fheight.value()

    @QSlot(dict)
    def update_from_setp(self, setp):
        self._spb_fwidth.blockSignals(True)
        self._spb_fwidth.setValue(setp['fwidth'])
        self._spb_fwidth.blockSignals(False)

        self._spb_fheight.blockSignals(True)
        self._spb_fheight.setValue(setp['fheight'])
        self._spb_fheight.blockSignals(False)

    def _setup_figsize_grpbox(self):
        """
        Setup a group box with spin boxes that allows to set the figure
        size in inches.
        """
        self._spb_fwidth = QDoubleSpinBox()
        self._spb_fwidth.setSingleStep(0.1)
        self._spb_fwidth.setDecimals(1)
        self._spb_fwidth.setMinimum(3)
        self._spb_fwidth.setSuffix('  in')
        self._spb_fwidth.setAlignment(Qt.AlignCenter)
        self._spb_fwidth.setKeyboardTracking(False)
        self._spb_fwidth.valueChanged.connect(self._fig_size_changed)

        self._spb_fheight = QDoubleSpinBox()
        self._spb_fheight.setSingleStep(0.1)
        self._spb_fheight.setDecimals(1)
        self._spb_fheight.setMinimum(3)
        self._spb_fheight.setSuffix('  in')
        self._spb_fheight.setAlignment(Qt.AlignCenter)
        self._spb_fheight.setKeyboardTracking(False)
        self._spb_fheight.valueChanged.connect(self._fig_size_changed)

        grpbox = QGroupBox("Figure Size :")
        layout = QGridLayout(grpbox)

        layout.addWidget(QLabel('width :'), 0, 0)
        layout.addWidget(self._spb_fwidth, 0, 2)
        layout.addWidget(QLabel('height :'), 1, 0)
        layout.addWidget(self._spb_fheight, 1, 2)

        layout.setColumnStretch(1, 100)
        layout.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        return grpbox

    @QSlot()
    def _fig_size_changed(self):
        """Handle when the size of the figure is changed by the user."""
        self.figcanvas.set_fig_size(
            self.fig_width, self.fig_height, units='IP')


class YearLimitsPanel(SetpPanelBase):

    def __init__(self, parent=None):
        super(YearLimitsPanel, self).__init__(parent)
        self.setup()

    def setup(self):
        """Setup the gui of the panel."""
        self.layout().addWidget(self._setup_xaxis_grpbox())
        self.layout().setRowStretch(self.layout().rowCount(), 100)

    @QSlot(dict)
    def update_from_setp(self, setp):
        self._spb_xmin.blockSignals(True)
        self._spb_xmin.setValue(setp['xmin'])
        self._spb_xmin.blockSignals(False)

        self._spb_xmax.blockSignals(True)
        self._spb_xmax.setValue(setp['xmax'])
        self._spb_xmax.blockSignals(False)

    def _setup_xaxis_grpbox(self):
        self._spb_xmin = QDoubleSpinBox()
        self._spb_xmin.setValue(1900)
        self._spb_xmin.setDecimals(0)
        self._spb_xmin.setSingleStep(1)
        self._spb_xmin.setRange(1900, 2100)
        self._spb_xmin.setKeyboardTracking(False)
        self._spb_xmin.valueChanged.connect(self._xaxis_changed)

        self._spb_xmax = QDoubleSpinBox()
        self._spb_xmax.setValue(1900)
        self._spb_xmax.setDecimals(0)
        self._spb_xmax.setSingleStep(1)
        self._spb_xmax.setRange(1900, 2100)
        self._spb_xmax.setKeyboardTracking(False)
        self._spb_xmax.valueChanged.connect(self._xaxis_changed)

        grpbox = QGroupBox("X-Axis :")
        layout = QGridLayout(grpbox)

        layout.addWidget(QLabel('minimum :'), 0, 0)
        layout.addWidget(self._spb_xmin, 0, 2)
        layout.addWidget(QLabel('maximum :'), 1, 0)
        layout.addWidget(self._spb_xmax, 1, 2)

        layout.setColumnStretch(1, 100)
        layout.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        return grpbox

    @QSlot()
    def _xaxis_changed(self):
        self.figcanvas.set_xlimits(
            self._spb_xmin.value(), self._spb_xmax.value())


class YAxisOptPanel(SetpPanelBase):
    def __init__(self, parent=None):
        super(YAxisOptPanel, self).__init__(parent)
        self.setup()

    def setup(self):
        """Setup the gui of the panel."""
        self.layout().addWidget(self._setup_yaxis_grpbox())
        self.layout().setRowStretch(self.layout().rowCount(), 100)

    @QSlot(dict)
    def update_from_setp(self, setp):
        self._spb_ymin.blockSignals(True)
        self._spb_ymin.setValue(setp['ymin'])
        self._spb_ymin.blockSignals(False)

        self._spb_ymax.blockSignals(True)
        self._spb_ymax.setValue(setp['ymax'])
        self._spb_ymax.blockSignals(False)

        self._spb_yscl.blockSignals(True)
        self._spb_yscl.setValue(setp['yscl'])
        self._spb_yscl.blockSignals(False)

        self._spb_yscl_minor.blockSignals(True)
        self._spb_yscl_minor.setValue(setp['yscl minor'])
        self._spb_yscl_minor.blockSignals(False)

    def _setup_yaxis_grpbox(self):
        self._spb_ymin = QDoubleSpinBox()
        self._spb_ymin.setDecimals(0)
        self._spb_ymin.setSingleStep(50)
        self._spb_ymin.setRange(0, 10000)
        self._spb_ymin.setKeyboardTracking(False)
        self._spb_ymin.valueChanged.connect(self._yaxis_changed)

        self._spb_ymax = QDoubleSpinBox()
        self._spb_ymax.setDecimals(0)
        self._spb_ymax.setSingleStep(50)
        self._spb_ymax.setRange(0, 10000)
        self._spb_ymax.setKeyboardTracking(False)
        self._spb_ymax.valueChanged.connect(self._yaxis_changed)

        self._spb_yscl = QDoubleSpinBox()
        self._spb_yscl.setDecimals(0)
        self._spb_yscl.setSingleStep(50)
        self._spb_yscl.setRange(10, 999)
        self._spb_yscl.setKeyboardTracking(False)
        self._spb_yscl.valueChanged.connect(self._yaxis_changed)

        self._spb_yscl_minor = QDoubleSpinBox()
        self._spb_yscl_minor.setDecimals(0)
        self._spb_yscl_minor.setSingleStep(10)
        self._spb_yscl_minor.setRange(10, 999)
        self._spb_yscl_minor.setKeyboardTracking(False)
        self._spb_yscl_minor.valueChanged.connect(self._yaxis_changed)

        grpbox = QGroupBox("Y-Axis :")
        layout = QGridLayout(grpbox)

        layout.addWidget(QLabel('minimum :'), 0, 0)
        layout.addWidget(self._spb_ymin, 0, 2)
        layout.addWidget(QLabel('maximum :'), 1, 0)
        layout.addWidget(self._spb_ymax, 1, 2)
        layout.addWidget(QLabel('scale major :'), 2, 0)
        layout.addWidget(self._spb_yscl, 2, 2)
        layout.addWidget(QLabel('scale minor :'), 3, 0)
        layout.addWidget(self._spb_yscl_minor, 3, 2)

        layout.setColumnStretch(1, 100)
        layout.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)

        return grpbox

    @QSlot()
    def _yaxis_changed(self):
        self.figcanvas.set_ylimits(
            self._spb_ymin.value(), self._spb_ymax.value(),
            self._spb_yscl.value(), self._spb_yscl_minor.value()
        )


# ---- Figure managers

class FigManagerBase(QWidget):
    """
    Abstract manager to show the results from GLUE.
    """
    def __init__(self, figure_canvas, setp_panels=[], parent=None):
        super(FigManagerBase, self).__init__(parent)
        self.savefig_dir = os.getcwd()

        self.figcanvas = figure_canvas(setp={})
        self.figviewer = ImageViewer()
        self.figcanvas.sig_fig_changed.connect(self.figviewer.load_mpl_figure)

        self.setup_toolbar()
        self.figsetp_manager = FigSetpPanelManager(self.figcanvas)
        for setp_panel in setp_panels:
            self.figsetp_manager.add_figsetp_panel(setp_panel)

        layout = QGridLayout(self)
        layout.addWidget(self.figviewer, 1, 0)
        layout.addWidget(self.toolbar, 0, 0, 1, 2)
        layout.addWidget(self.figsetp_manager, 1, 1)

        layout.setColumnStretch(0, 100)
        layout.setRowStretch(0, 100)

    def resizeEvent(self, event):
        super(FigManagerBase, self).resizeEvent(event)
        self.figsetp_manager.setMinimumWidth(
            self.figsetp_manager.view.minimumSizeHint().width() +
            2*self.figsetp_manager.scrollarea.frameWidth() +
            QApplication.style().pixelMetric(QStyle.PM_ScrollBarExtent)
            )

    def setup_toolbar(self):
        """Setup the toolbar of the figure manager."""

        self.btn_save = QToolButtonNormal(icons.get_icon('save'))
        self.btn_save.setToolTip('Save current graph as...')
        self.btn_save.clicked.connect(self._select_savefig_path)

        # Setup the layout of the toolbar

        self.toolbar = QToolBar()
        self.toolbar.addWidget(self.btn_save)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self._setup_zoom_widget())
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self._setup_language_widget())

    def _setup_zoom_widget(self):
        """Setup a toolbar widget to zoom in and zoom out the figure."""

        btn_zoom_out = QToolButtonSmall(icons.get_icon('zoom_out'))
        btn_zoom_out.setToolTip('Zoom out (ctrl + mouse-wheel-down)')
        btn_zoom_out.clicked.connect(self.figviewer.zoomOut)

        btn_zoom_in = QToolButtonSmall(icons.get_icon('zoom_in'))
        btn_zoom_in.setToolTip('Zoom in (ctrl + mouse-wheel-up)')
        btn_zoom_in.clicked.connect(self.figviewer.zoomIn)

        self.zoom_disp = QSpinBox()
        self.zoom_disp.setAlignment(Qt.AlignCenter)
        self.zoom_disp.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.zoom_disp.setReadOnly(True)
        self.zoom_disp.setSuffix(' %')
        self.zoom_disp.setRange(0, 9999)
        self.zoom_disp.setValue(100)
        self.figviewer.zoomChanged.connect(self.zoom_disp.setValue)

        zoom_pan = QFrameLayout()
        zoom_pan.setSpacing(3)
        zoom_pan.addWidget(btn_zoom_out, 0, 0)
        zoom_pan.addWidget(btn_zoom_in, 0, 1)
        zoom_pan.addWidget(self.zoom_disp, 0, 2)
        zoom_pan.setContentsMargins(5, 0, 5, 0)  # (L, T, R, B)

        return zoom_pan

    @property
    def fig_language(self):
        return self._cbb_language.currentText()

    def _setup_language_widget(self):
        """
        Setup a toolbar widget to change the language of the text shown in the
        figure.
        """
        self._cbb_language = QComboBox()
        self._cbb_language.setEditable(False)
        self._cbb_language.setInsertPolicy(QComboBox.NoInsert)
        self._cbb_language.addItems(LANGUAGES)
        self._cbb_language.setCurrentIndex(1)
        self._cbb_language.currentIndexChanged.connect(self._language_changed)
        self._cbb_language.setToolTip(
            "Set the language of the text shown in the figure.")

        grp_lang = QWidget()
        lay_lang = QGridLayout(grp_lang)
        lay_lang.addWidget(QLabel('Language :'), 0, 0)
        lay_lang.addWidget(self._cbb_language, 0, 1)
        lay_lang.setSpacing(5)
        lay_lang.setContentsMargins(5, 0, 5, 0)  # (L, T, R, B)

        return grp_lang

    @QSlot()
    def _language_changed(self):
        """Handle when the language is changed by the user."""
        self.figcanvas.set_fig_language(self.fig_language)

    def _select_savefig_path(self):
        """Open a dialog window to select a file to save the figure."""
        figname = find_unique_filename(
            osp.join(self.savefig_dir, self.figcanvas.FIGNAME) + ".pdf")
        ffmat = "*.pdf;;*.svg;;*.png"

        fname, ftype = QFileDialog.getSaveFileName(
                self, "Save Figure", figname, ffmat)
        if fname:
            ftype = ftype.replace('*', '')
            fname = fname if fname.endswith(ftype) else fname + ftype
            self.savefig_dir = osp.dirname(fname)
            self.save_figure_tofile(fname)

    def save_figure_tofile(self, fname):
        """Save the figure to fname."""
        try:
            self.figcanvas.figure.savefig(fname)
        except PermissionError:
            msg = "The file is in use by another application or user."
            QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
            self._select_savefig_path()


# ---- Figure canvas

class FigCanvasBase(FigureCanvasQTAgg):
    """
    This is the base figure format to plot GLUE results.
    """
    FIGNAME = "figure_name"
    sig_fig_changed = QSignal(MPLFigure)
    sig_newfig_plotted = QSignal(dict)

    colors = {'dark grey': '0.65',
              'light grey': '0.85'}

    FWIDTH, FHEIGHT = 8.5, 5
    MARGINS = [1, 0.15, 0.15, 0.65]  # left, top, right, bottom

    def __init__(self, setp={}):
        super(FigCanvasBase, self).__init__(mpl.figure.Figure())
        self.xticklabels = []
        self.notes = []
        self._xticklabels_yt = 0
        self.ax0 = self.figure.add_axes([0, 0, 1, 1])
        self.ax0.patch.set_visible(False)
        for axis in ['top', 'bottom', 'left', 'right']:
            self.ax0.spines[axis].set_linewidth(0.75)

        self.figure.patch.set_facecolor('white')
        self.set_figure_setp(setp)

    def clear(self):
        self.ax0.clear()
        self.xticklabels = []
        self.notes = []

    def set_figure_setp(self, setp):
        self.setp = setp
        if 'language' not in self.setp.keys():
            self.setp['language'] = 'english'
        if 'fwidth' not in self.setp.keys():
            self.setp['fwidth'] = self.FWIDTH
        if 'fheight' not in self.setp.keys():
            self.setp['fheight'] = self.FHEIGHT
        if 'left margin' not in self.setp.keys():
            self.setp['left margin'] = self.MARGINS[0]
        if 'top margin' not in self.setp.keys():
            self.setp['top margin'] = self.MARGINS[1]
        if 'right margin' not in self.setp.keys():
            self.setp['right margin'] = self.MARGINS[2]
        if 'bottom margin' not in self.setp.keys():
            self.setp['bottom margin'] = self.MARGINS[3]
        if 'xlabel size' not in self.setp.keys():
            self.setp['xlabel size'] = 16
        if 'xticks size' not in self.setp.keys():
            self.setp['xticks size'] = 14
        if 'ylabel size' not in self.setp.keys():
            self.setp['ylabel size'] = 16
        if 'yticks size' not in self.setp.keys():
            self.setp['yticks size'] = 14
        if 'legend size' not in self.setp.keys():
            self.setp['legend size'] = 14
        if 'notes size' not in self.setp.keys():
            self.setp['notes size'] = 10

        self.figure.set_size_inches(self.setp['fwidth'], self.setp['fheight'])
        self.refresh_margins()

    def set_fig_size(self, fw, fh, units='IP'):
        """
        Set the figure width and height in inches if units is IP
        or in cm if units is SI.
        """
        if units == 'SI':
            # Convert values from cm to in.
            fw = fw / 2.54
            fh = fh / 2.54
        self.setp['fwidth'], self.setp['fheight'] = fw, fh
        self.figure.set_size_inches(fw, fh)
        self.refresh_margins()

    def set_axes_margins_inches(self, margins):
        """Set the margins of the figure axes in inches."""
        self.setp['left margin'] = margins[0]
        self.setp['top margin'] = margins[1]
        self.setp['right margin'] = margins[2]
        self.setp['bottom margin'] = margins[3]
        self.refresh_margins()

    def refresh_margins(self):
        left = self.setp['left margin']/self.setp['fwidth']
        top = self.setp['top margin']/self.setp['fheight']
        right = self.setp['right margin']/self.setp['fwidth']
        bottom = self.setp['bottom margin']/self.setp['fheight']
        for ax in self.figure.axes:
            ax.set_position([left, bottom, 1-left-right, 1-top-bottom])

        self.sig_fig_changed.emit(self.figure)

    def set_fig_language(self, language):
        """
        Set the language of the text shown in the figure. This needs to be
        impemented in the derived class.
        """
        pass

    def set_xlimits(self, xmin, xmax):
        """Set the limits of the xaxis to the provided values."""
        pass

    def set_ylimits(self, ymin, ymax):
        """Set the limits of the yaxis to the provided values."""
        pass

    def set_legend_fontsize(self, fontsize):
        """Set the font size of the text in the legend in points."""
        self.setp['legend size'] = fontsize
        self.setup_legend()
        self.sig_fig_changed.emit(self.figure)

    def set_tick_labels_size(self, xtick_size, ytick_size):
        """Set the tick labels font size in points."""
        self.setp['xticks size'] = xtick_size
        self.setp['yticks size'] = ytick_size
        self.setup_xticklabels()
        self.setup_yticklabels()
        self.sig_fig_changed.emit(self.figure)

    def set_axes_labels_size(self, xlabel_size, ylabel_size):
        """Set the axes label font size in points."""
        self.setp['xlabel size'] = xlabel_size
        self.setp['ylabel size'] = ylabel_size
        self.setup_axes_labels()
        self.sig_fig_changed.emit(self.figure)

    def set_notes_size(self, notes_size):
        """Set the font size of all annotated text in points."""
        self.setp['notes size'] = notes_size
        for note in self.notes:
            note.set_fontsize(notes_size)
        self.sig_fig_changed.emit(self.figure)

    def _get_xaxis_labelpad(self):
        """
        Calcul the vertical padding in points between the xaxis and its label.
        This corresponds to the sum of the xtick labels height and their
        vertical padding.
        """
        # Random text bbox height :
        renderer = self.get_renderer()
        bbox, _ = self.ax0.xaxis.get_ticklabel_extents(renderer)
        bbox = bbox.transformed(self.figure.dpi_scale_trans.inverted())
        xticklabels_height = bbox.height*72
        for i, xticklabel in enumerate(self.xticklabels):
            bbox = xticklabel.get_window_extent(renderer)
            bbox = bbox.transformed(self.figure.dpi_scale_trans.inverted())
            xticklabels_height = max(bbox.height*72, xticklabels_height)
        return xticklabels_height + self._xticklabels_yt

    def _get_xlabel_xt(self, fontsize, rotation):
        """
        Calcul the horizontal translation that is required to align the top
        right corner (before rotation) of the text box with the tick.
        """
        # Random text bbox height :
        dummytxt = self.ax0.text(0.5, 0.5, 'some_dummy_text',
                                 fontsize=fontsize, ha='right', va='top',
                                 transform=self.ax0.transAxes)

        renderer = self.get_renderer()
        bbox = dummytxt.get_window_extent(renderer)
        bbox = bbox.transformed(self.figure.dpi_scale_trans.inverted())
        dx = bbox.height * np.sin(np.radians(45))

        dummytxt.remove()
        return dx


class FigWaterBudgetGLUE(FigCanvasBase):
    FIGNAME = "water_budget_glue"
    FWIDTH, FHEIGHT = 15, 7
    MARGINS = [1, 0.15, 0.15, 1.1]
    COLOR = [[0/255, 25/255, 51/255],
             [0/255, 76/255, 153/255],
             [0/255, 128/255, 255/255],
             [102/255, 178/255, 255/255]]

    def __init__(self, setp={}):
        super(FigWaterBudgetGLUE, self).__init__(setp)
        self._xticklabels_yt = -2/72

    def plot(self, glue_df):
        ax = self.ax0
        self.clear()

        glue_yrly = glue_df['budget']['hydrol yearly']
        years = glue_yrly['years']
        precip = glue_yrly['precip']
        rechg = glue_yrly['recharge'][:, 2]
        evapo = glue_yrly['evapo'][:, 2]
        runoff = glue_yrly['runoff'][:, 2]

        # Setup xticks

        ax.tick_params(axis='x', length=0, direction='out')
        ax.tick_params(axis='x', which='minor', length=5, direction='out')

        # Setup yticks

        self.setup_yticklabels()
        ax.yaxis.set_ticks_position('left')
        ax.set_axisbelow(True)

        # Setup axis range.

        self.setp['xmin'] = years[0]
        self.setp['xmax'] = years[-1]
        self.setp['ymin'] = 0
        self.setp['ymax'] = np.ceil(np.max(precip)/100)*100
        self.setp['yscl'] = 250
        self.setp['yscl_minor'] = 50

        self.set_ylimits(self.setp['ymin'], self.setp['ymax'],
                         self.setp['yscl'], self.setp['yscl_minor'])
        self.set_xlimits(self.setp['xmin'], self.setp['xmax'])

        self.setup_axes_labels()
        self.setup_legend()

        # Plot the data.

        bwidth = 0.35
        xpad = 1
        xpad_left = mpl.transforms.ScaledTranslation(
            -xpad/72, 0, self.figure.dpi_scale_trans)
        xpad_right = mpl.transforms.ScaledTranslation(
            xpad/72, 0, self.figure.dpi_scale_trans)

        # Plot precipitation.
        ax.bar(years-bwidth/2, precip, align='center', width=bwidth,
               color=self.COLOR[0], edgecolor=None,
               transform=ax.transData + xpad_left)

        # Plot runoff.
        var2plot = rechg + evapo + runoff
        ax.bar(years+bwidth/2, var2plot, align='center', width=bwidth,
               color=self.COLOR[3], edgecolor=None,
               transform=ax.transData + xpad_right)

        # Plot evapotranspiration.
        var2plot = rechg + evapo
        ax.bar(years+bwidth/2, var2plot, align='center', width=bwidth,
               color=self.COLOR[2], edgecolor=None,
               transform=ax.transData + xpad_right)

        # Plot recharge.
        var2plot = rechg
        ax.bar(years+bwidth/2, var2plot, align='center', width=bwidth,
               color=self.COLOR[1], edgecolor=None,
               transform=ax.transData + xpad_right)

        # Plot the text.

        xpad_right = mpl.transforms.ScaledTranslation(
            2*xpad/72, 0, self.figure.dpi_scale_trans)

        self.notes = []
        for i in range(len(years)):
            y = precip[i]/2
            x = years[i] - bwidth/2
            txt = '%d' % precip[i]
            self.notes.append(self.ax0.text(
                x, y, txt, color='white', va='center', ha='center',
                rotation=90, fontsize=self.setp['notes size'], clip_on=True,
                transform=ax.transData + xpad_left))

            y = rechg[i]/2
            x = years[i] + bwidth/2
            txt = '%d' % rechg[i]
            self.notes.append(self.ax0.text(
                x, y, txt, color='white', va='center', ha='center',
                rotation=90, fontsize=self.setp['notes size'], clip_on=True,
                transform=ax.transData + xpad_right))

            y = evapo[i]/2 + rechg[i]
            x = years[i] + bwidth/2
            txt = '%d' % evapo[i]
            self.notes.append(self.ax0.text(
                x, y, txt, color='black', va='center', ha='center',
                rotation=90, fontsize=self.setp['notes size'], clip_on=True,
                transform=ax.transData + xpad_right))

            y = runoff[i]/2 + rechg[i] + evapo[i]
            x = years[i] + bwidth/2
            txt = '%d' % runoff[i]
            self.notes.append(self.ax0.text(
                x, y, txt, color='black', va='center', ha='center',
                rotation=90, fontsize=self.setp['notes size'], clip_on=True,
                transform=ax.transData + xpad_right))

        self.sig_fig_changed.emit(self.figure)
        self.sig_newfig_plotted.emit(self.setp)

    def setup_xticklabels(self):
        """Setup the year labels of the xaxis."""
        # Remove currently plotted labels :
        self.ax0.xaxis.set_ticklabels([])
        for label in self.xticklabels:
            label.remove()
        self.xticklabels = []

        # Draw the labels anew.
        year_range = np.arange(
            self.setp['xmin'], self.setp['xmax']+1).astype(int)
        xlabels = ["'%s - '%s" % (str(y)[-2:], str(y+1)[-2:])
                   for y in year_range]

        xt = self._get_xlabel_xt(self.setp['xticks size'], 45)
        offset = mpl.transforms.ScaledTranslation(
            xt, self._xticklabels_yt, self.figure.dpi_scale_trans)
        for i in range(len(year_range)):
            self.xticklabels.append(self.ax0.text(
                year_range[i], self.setp['ymin'], xlabels[i], rotation=45,
                va='top', ha='right', fontsize=self.setp['xticks size'],
                transform=self.ax0.transData + offset))
        self.setup_axes_labels()

    def setup_yticklabels(self):
        """Setup the labels of the yaxis."""
        self.ax0.tick_params(axis='y', direction='out', gridOn=True,
                             labelsize=self.setp['yticks size'])
        self.ax0.tick_params(axis='y', direction='out', which='minor',
                             gridOn=False)

    def set_xlimits(self, xmin, xmax):
        """Set the limits of the xaxis to the provided values."""
        self.setp['xmin'], self.setp['xmax'] = xmin, xmax
        self.ax0.axis(xmin=xmin-0.5, xmax=xmax+0.5)

        year_range = np.arange(xmin, xmax+1).astype(int)
        self.setup_xticklabels()
        self.ax0.set_xticks(year_range)
        self.ax0.set_xticks(
            np.hstack([year_range-0.5, year_range[-1] + 0.5]), minor=True)

        self.sig_fig_changed.emit(self.figure)

    def set_ylimits(self, ymin, ymax, yscl, yscl_minor):
        """Set the limits of the yaxis to the provided values."""
        self.setp['ymin'], self.setp['ymax'] = ymin, ymax
        self.setp['yscl'], self.setp['yscl minor'] = yscl, yscl_minor

        self.setup_xticklabels()
        self.ax0.set_yticks(np.arange(ymin, ymax+1, yscl))
        self.ax0.set_yticks(np.arange(ymin, ymax+1, yscl_minor), minor=True)
        self.ax0.axis(ymin=ymin, ymax=ymax)

        self.sig_fig_changed.emit(self.figure)

    def set_fig_language(self, language):
        """Set the language of the text shown in the figure."""
        self.setp['language'] = language.lower()
        self.setup_axes_labels()
        self.setup_legend()
        self.sig_fig_changed.emit(self.figure)

    def setup_axes_labels(self):
        """
        Set the text and position of the axes labels.
        """
        if self.setp['language'] == 'french':
            ylabel = "Colonne d'eau équivalente (mm)"
            xlabel = ("Année Hydrologique (1er octobre d'une"
                      " année au 30 septembre de l'année suivante)")
        else:
            ylabel = 'Equivalent Water (mm)'
            xlabel = ("Hydrological Years (October 1st of one"
                      " year to September 30th of the next)")

        xlabelpad = self._get_xaxis_labelpad()
        self.ax0.set_xlabel(xlabel,
                            fontsize=self.setp['xlabel size'],
                            labelpad=xlabelpad)
        self.ax0.set_ylabel(ylabel, fontsize=self.setp['ylabel size'],
                            labelpad=10)

    def setup_legend(self,):
        """Setup the legend of the graph."""
        lg_handles = [
            mpl.patches.Rectangle((0, 0), 1, 1, fc=self.COLOR[i], ec='none')
            for i in range(4)]
        if self.setp['language'] == 'french':
            lg_labels = ['Précipitations totales', 'Recharge', 'Ruissellement',
                         'Évapotranspiration réelle']
        else:
            lg_labels = ['Total Precipitation', 'Recharge', 'Runoff',
                         'Real Evapotranspiration']
        self.ax0.legend(lg_handles, lg_labels, ncol=4, numpoints=1,
                        bbox_to_anchor=[0, 1], loc='upper left',
                        fontsize=self.setp['legend size'], frameon=False,
                        handletextpad=0.2, borderaxespad=0.2, borderpad=0.2)


class FigWaterLevelGLUE(FigCanvasBase):
    """
    This is a graph that shows observed ground-water levels and GLUE 5/95
    predicted water levels.
    """

    FIGNAME = "water_level_glue"

    def __init__(self, setp={}):
        super(FigWaterLevelGLUE, self).__init__(setp)

    def plot(self, glue_df):
        self.clear()
        ax = self.ax0

        ax.grid(axis='x', color='0.35', ls=':', lw=1, zorder=200)
        ax.grid(axis='y', color='0.35', ls=':', lw=1, zorder=200)
        ax.invert_yaxis()

        # ---- ticks format

        ax.yaxis.set_ticks_position('left')
        ax.tick_params(axis='y', direction='out', labelsize=12)
        ax.xaxis.set_ticks_position('bottom')
        ax.tick_params(axis='x', direction='out')
        self.figure.autofmt_xdate()

        # ---- Plot the observed and glue predicted water levels.

        wlobs = glue_df['water levels']['observed']
        dates = glue_df['water levels']['date']
        wl05 = glue_df['water levels']['predicted'][:, 0]/1000
        wl95 = glue_df['water levels']['predicted'][:, 2]/1000

        ax = self.figure.axes[0]
        ax.plot(dates, wlobs, color='b', ls='None', marker='.', ms=3,
                zorder=100)
        ax.fill_between(dates, wl95, wl05, facecolor='0.85', lw=1,
                        edgecolor='0.65', zorder=0)

        self.setup_axes_labels()
        self.setup_legend()

        self.sig_fig_changed.emit(self.figure)
        self.sig_newfig_plotted.emit(self.setp)

    def set_xlimits(self, xmin, xmax):
        """Set the limits of the xaxis to the provided values."""
        pass

    def set_ylimits(self, ymin, ymax, yscl=None, yscl_minor=None):
        """Set the limits of the yaxis to the provided values."""
        self.ax0.axis(ymin=ymin, ymax=ymax)
        self.sig_fig_changed.emit(self.figure)

    def set_fig_language(self, language):
        """
        Set the language of the text shown in the figure.
        """
        self.setp['language'] = language.lower()
        self.setup_axes_labels()
        self.sig_fig_changed.emit(self.figure)

    def setup_legend(self):
        dum1 = mpl.patches.Rectangle((0, 0), 1, 1, fc='0.85', ec='0.65')
        dum2, = self.ax0.plot([], [], color='b', ls='None', marker='.', ms=10)

        lg_handles = [dum2, dum1]
        lg_labels = ['Observations', 'GLUE 5/95']

        self.ax0.legend(lg_handles, lg_labels, ncol=2, fontsize=12,
                        frameon=False, numpoints=1)

    def setup_axes_labels(self):
        """
        Set the text and position of the axes labels.
        """
        if self.setp['language'] == 'french':
            xlabel = "Niveau d'eau (m sous la surface)"
        else:
            xlabel = 'Water Level (mbgs)'
        self.ax0.set_ylabel(xlabel, fontsize=16, labelpad=20)


class FigYearlyRechgGLUE(FigCanvasBase):
    """
    This is a graph that shows annual ground-water recharge and its
    uncertainty.
    """

    MARGINS = [1, 0.15, 0.15, 0.9]  # left, top, right, bottom
    FIGNAME = "gw_rechg_glue"

    def __init__(self, setp={}):
        super(FigYearlyRechgGLUE, self).__init__(setp)
        self.ax0.set_axisbelow(True)
        self._xticklabels_yt = -4/72
        self.setp['legend size'] = 12
        self.setp['xticks size'] = 12

    def plot(self, glue_data):
        ax0 = self.ax0
        self.clear()

        year_range = glue_data['budget']['hydrol yearly']['years']
        glue_rechg_yr = glue_data['budget']['hydrol yearly']['recharge']

        glue95_yr = glue_rechg_yr[:, -1]
        glue05_yr = glue_rechg_yr[:, 0]
        glue50_yr = glue_rechg_yr[:, 2]
        glue25_yr = glue_rechg_yr[:, 1]
        glue75_yr = glue_rechg_yr[:, -2]

        self.glue_year_rechg_avg = tuple(
            np.mean(glue_rechg_yr[:, i]) for i in range(5))

        # ---- Xticks format

        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x', direction='out', length=4)
        ax0.set_xticks(year_range)

        # ----- ticks format

        ymax0 = np.ceil(np.max(glue95_yr)/10)*10 + 50
        ymin0 = 0
        scale_yticks = 50 if np.max(glue95_yr) < 250 else 250
        scale_yticks_minor = 10 if np.max(glue95_yr) < 250 else 50

        ax0.yaxis.set_ticks_position('left')
        ax0.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle=':',
                 linewidth=0.5, dashes=[0.5, 5])

        # ---- Axis range

        self.setp['xmin'] = min(year_range)
        self.setp['xmax'] = max(year_range)
        self.setp['ymin'] = ymin0
        self.setp['ymax'] = ymax0
        self.setp['yscl'] = scale_yticks
        self.setp['yscl_minor'] = scale_yticks_minor

        self.set_ylimits(self.setp['ymin'], self.setp['ymax'],
                         self.setp['yscl'], self.setp['yscl_minor'])
        self.set_xlimits(self.setp['xmin'], self.setp['xmax'])

        # ---- Plot results

        ax0.plot(year_range, glue50_yr, ls='-', lw=1, marker=None,
                 color='black', zorder=300)
        self.g50, = ax0.plot(year_range, glue50_yr, ls='none', marker='o',
                             color='black', mew=1, mfc='White', mec='black',
                             ms=6, zorder=300)

        yerr = [glue50_yr-glue05_yr, glue95_yr-glue50_yr]
        self.g0595 = ax0.errorbar(year_range, glue50_yr, yerr=yerr,
                                  fmt='none', capthick=1, capsize=4,
                                  ecolor='0', elinewidth=1, zorder=200)

        self.g2575 = ax0.fill_between(year_range, glue25_yr, glue75_yr,
                                      color="#FFCCCC")

        # ---- Axes labels

        self.setup_yticklabels()
        self.setup_xticklabels()

        # ----- Legend

        self.setup_legend()
        self.setup_yearly_avg_legend()

        self.sig_fig_changed.emit(self.figure)
        self.sig_newfig_plotted.emit(self.setp)

    def set_fig_language(self, language):
        """Set the language of the text shown in the figure."""
        self.setp['language'] = language.lower()
        self.setup_axes_labels()
        self.refresh_yearly_avg_legend_text()
        self.sig_fig_changed.emit(self.figure)

    def setup_xticklabels(self):
        """Setup the year labels of the xaxis."""
        # Remove currently plotted labels :
        self.ax0.xaxis.set_ticklabels([])
        for label in self.xticklabels:
            label.remove()
        self.xticklabels = []

        # Draw the labels anew.
        year_range = np.arange(
            self.setp['xmin'], self.setp['xmax']+1).astype(int)
        xlabels = ["'%s - '%s" % (str(y)[-2:], str(y+1)[-2:])
                   for y in year_range]

        xt = self._get_xlabel_xt(self.setp['xticks size'], 45)
        offset = mpl.transforms.ScaledTranslation(
            xt, self._xticklabels_yt, self.figure.dpi_scale_trans)
        for i in range(len(year_range)):
            self.xticklabels.append(self.ax0.text(
                year_range[i], self.setp['ymin'], xlabels[i], rotation=45,
                va='top', ha='right', fontsize=self.setp['xticks size'],
                transform=self.ax0.transData + offset))
        self.setup_axes_labels()

    def setup_yticklabels(self):
        """Setup the labels of the yaxis."""
        self.ax0.tick_params(axis='y', direction='out', gridOn=True,
                             labelsize=self.setp['yticks size'])
        self.ax0.tick_params(axis='y', direction='out', which='minor',
                             gridOn=False)

    def set_xlimits(self, xmin, xmax):
        """Set the limits of the xaxis to the provided values."""
        self.setp['xmin'], self.setp['xmax'] = xmin, xmax
        self.setup_xticklabels()
        self.ax0.axis(xmin=xmin-0.5, xmax=xmax+0.5)
        self.sig_fig_changed.emit(self.figure)

    def set_ylimits(self, ymin, ymax, yscl, yscl_minor):
        """Set the limits of the yaxis to the provided values."""
        self.setp['ymin'], self.setp['ymax'] = ymin, ymax
        self.setp['yscl'], self.setp['yscl minor'] = yscl, yscl_minor

        self.setup_xticklabels()
        self.ax0.set_yticks(np.arange(0, 2*ymax+1, yscl))
        self.ax0.set_yticks(np.arange(0, 2*ymax, yscl_minor), minor=True)
        self.ax0.axis(ymin=ymin, ymax=ymax)
        self.sig_fig_changed.emit(self.figure)

    def setup_axes_labels(self):
        """Set the text and position of the axes labels."""
        if self.setp['language'] == 'french':
            ylabl = "Recharge annuelle (mm/a)"
            xlabl = ("Années Hydrologiques (1er octobre d'une année "
                     "au 30 septembre de la suivante)")
        else:
            ylabl = "Annual Recharge (mm/y)"
            xlabl = ("Hydrological Years (October 1st of one "
                     "year to September 30th of the next)")

        xlabelpad = self._get_xaxis_labelpad()
        self.ax0.set_xlabel(xlabl,
                            fontsize=self.setp['xlabel size'],
                            labelpad=xlabelpad)
        self.ax0.set_ylabel(ylabl,
                            fontsize=self.setp['ylabel size'],
                            labelpad=10)

    def setup_yearly_avg_legend(self):
        """Setup the yearly average legend."""
        padding = mpl.transforms.ScaledTranslation(
            5/72, 5/72, self.figure.dpi_scale_trans)
        self.txt_yearly_avg = self.ax0.text(
            0, 0, '', va='bottom', ha='left', fontsize=self.setp['notes size'],
            transform=self.ax0.transAxes + padding)
        self.notes.append(self.txt_yearly_avg)
        self.refresh_yearly_avg_legend_text()

    def refresh_yearly_avg_legend_text(self):
        """Set the text and position of for the yearly averages results."""
        if self.setp['language'] == 'french':
            text = ("Recharge annuelle moyenne :\n"
                    "(GLUE 5) %d mm/a ; "
                    "(GLUE 25) %d mm/a ; "
                    "(GLUE 50) %d mm/a ; "
                    "(GLUE 75) %d mm/a ; "
                    "(GLUE 95) %d mm/a"
                    ) % self.glue_year_rechg_avg
        else:
            text = ("Mean annual recharge :\n"
                    "(GLUE 5) %d mm/y ; "
                    "(GLUE 25) %d mm/y ; "
                    "(GLUE 50) %d mm/y ; "
                    "(GLUE 75) %d mm/y ; "
                    "(GLUE 95) %d mm/y"
                    ) % self.glue_year_rechg_avg
        self.txt_yearly_avg.set_text(text)

    def setup_legend(self,):
        """Setup the legend of the graph."""
        lg_handles = [self.g50, self.g2575, self.g0595]
        lg_labels = ['Recharge (GLUE 50)', 'Recharge (GLUE 25/75)',
                     'Recharge (GLUE 5/95)']
        self.ax0.legend(
            lg_handles, lg_labels, ncol=3, fontsize=self.setp['legend size'],
            frameon=False, handletextpad=0.2, borderaxespad=0.2, borderpad=0.2,
            numpoints=1, bbox_to_anchor=[0, 1], loc='upper left')


# %% ---- if __name__ == '__main__'

if __name__ == '__main__':
    from gwhat.gwrecharge.gwrecharge_calc2 import load_glue_from_npy
    from gwhat.gwrecharge.glue import GLUEDataFrame
    import sys

    app = QApplication(sys.argv)

    GLUE_RAWDATA = load_glue_from_npy('glue_rawdata.npy')
    GLUE_DF = GLUEDataFrame(GLUE_RAWDATA)

    figstack = FigureStackManager()
    figstack.plot_results(GLUE_DF)
    figstack.show()

    sys.exit(app.exec_())
