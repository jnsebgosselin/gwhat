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

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (
    QGridLayout, QAbstractSpinBox, QApplication, QComboBox, QDoubleSpinBox,
    QFileDialog, QGroupBox, QLabel, QMessageBox, QSpinBox, QTabWidget,
    QToolBar, QWidget)


# ---- Imports: local

from gwhat.gwrecharge.gwrecharge_calc2 import calcul_glue
from gwhat.gwrecharge.gwrecharge_calc2 import calcul_glue_yearly_rechg
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
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowIcon(icons.get_icon('master'))

        self.setup()

    def setup(self):
        """Setup the FigureStackManager withthe provided options."""
        self.setup_stack()
        layout = QGridLayout(self)
        layout.addWidget(self.stack, 0, 0)

    def setup_stack(self):
        self.fig_wl_glue = FigManagerWaterLevelGLUE(self)
        self.fig_rechg_glue = FigManagerRechgGLUE(self)

        self.stack = QTabWidget()
        self.stack.addTab(self.fig_wl_glue, 'Hydrograph')
        self.stack.addTab(self.fig_rechg_glue, 'Recharge')

    def plot_results(self, glue_data):
        self.fig_wl_glue.plot_prediction(glue_data)
        self.fig_rechg_glue.plot_recharge(glue_data)


# ---- Figure Managers

class FigureSetupPanel(QWidget):

    def __init__(self, figcanvas, parent=None):
        super(FigureSetupPanel, self).__init__(parent)
        self.figcanvas = figcanvas
        # self.setVisible(True)
        self.setup()

    @property
    def fig_width(self):
        return self._spb_fwidth.value()

    @property
    def fig_height(self):
        return self._spb_fheight.value()

    @property
    def fig_margins(self):
        return [self._spb_margins[loc].value() for loc in LOCS]

    def setup(self):
        """Setup the gui of the panel."""
        layout = QGridLayout(self)

        layout.addWidget(self._setup_figsize_grpbox(), 0, 0)
        layout.addWidget(self._setup_margins_grpbox(), 1, 0)

        layout.setRowStretch(layout.rowCount(), 100)
        layout.setContentsMargins(0, 0, 0, 0)

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
        self._spb_fwidth.setValue(self.figcanvas.FWIDTH)
        self._spb_fwidth.valueChanged.connect(self._fig_size_changed)

        self._spb_fheight = QDoubleSpinBox()
        self._spb_fheight.setSingleStep(0.1)
        self._spb_fheight.setDecimals(1)
        self._spb_fheight.setMinimum(3)
        self._spb_fheight.setSuffix('  in')
        self._spb_fheight.setAlignment(Qt.AlignCenter)
        self._spb_fheight.setKeyboardTracking(False)
        self._spb_fheight.setValue(self.figcanvas.FHEIGHT)
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
            self._spb_margins[loc].setMinimum(0.05)
            self._spb_margins[loc].setSuffix('  in')
            self._spb_margins[loc].setAlignment(Qt.AlignCenter)
            self._spb_margins[loc].setKeyboardTracking(False)
            self._spb_margins[loc].setValue(self.figcanvas.MARGINS[row])
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


class FigManagerBase(QWidget):
    """
    Abstract manager to show the results from GLUE.
    """
    def __init__(self, figure_canvas, parent=None):
        super(FigManagerBase, self).__init__(parent)
        self.savefig_dir = os.getcwd()

        self.figcanvas = figure_canvas()
        self.figviewer = ImageViewer()
        self.figcanvas.sig_fig_changed.connect(self.figviewer.load_mpl_figure)

        self.setup_toolbar()
        self.figsetp = FigureSetupPanel(self.figcanvas)

        layout = QGridLayout(self)
        layout.addWidget(self.figviewer, 0, 0)
        layout.addWidget(self.toolbar, 1, 0)
        layout.addWidget(self.figsetp, 0, 1, 2, 1)

        layout.setColumnStretch(0, 100)
        layout.setRowStretch(0, 100)

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


class FigManagerWaterLevelGLUE(FigManagerBase):
    """
    Figure manager with toolbar to show the results for the predicted
    water level versus the observations.
    """
    def __init__(self, parent=None):
        super(FigManagerWaterLevelGLUE, self).__init__(
            FigWaterLevelGLUE, parent)

    def plot_prediction(self, glue_data):
        self.figcanvas.plot_prediction(glue_data)
        self.figviewer.load_mpl_figure(self.figcanvas.figure)


class FigManagerRechgGLUE(FigManagerBase):
    """
    Figure manager with a toolbar to show the results for the yearly
    ground-water recharge and its uncertainty evaluated with GLUE.
    """
    def __init__(self, parent=None):
        super(FigManagerRechgGLUE, self).__init__(FigYearlyRechgGLUE, parent)

    def plot_recharge(self, data, Ymin0=None, Ymax0=None, yrs_range=None):
        self.figcanvas.plot_recharge(data, Ymin0, Ymax0, yrs_range)
        self.figviewer.load_mpl_figure(self.figcanvas.figure)


# ---- Figure Canvas

class FigCanvasBase(FigureCanvasQTAgg):
    """
    This is the base figure format to plot GLUE results.
    """
    sig_fig_changed = QSignal(MPLFigure)

    colors = {'dark grey': '0.65',
              'light grey': '0.85'}

    FWIDTH, FHEIGHT = 8.5, 5
    MARGINS = [1, 0.15, 0.15, 0.65]  # left, top, right, bottom

    def __init__(self, language='English'):
        super(FigCanvasBase, self).__init__(mpl.figure.Figure())

        self.language = language

        self.figure.set_size_inches(self.FWIDTH, self.FHEIGHT)
        self.figure.patch.set_facecolor('white')

        self.ax0 = ax0 = self.figure.add_axes([0, 0, 1, 1])
        self.set_axes_margins_inches(self.MARGINS)
        ax0.patch.set_visible(False)
        for axis in ['top', 'bottom', 'left', 'right']:
            ax0.spines[axis].set_linewidth(0.5)

    def set_axes_margins_inches(self, margins):
        """Set the margins of the figure axes in inches."""
        fheight = self.figure.get_figheight()
        fwidth = self.figure.get_figwidth()

        left = margins[0]/fwidth
        top = margins[1]/fheight
        right = margins[2]/fwidth
        bottom = margins[3]/fheight

        self.ax0.set_position([left, bottom, 1-left-right, 1-top-bottom])

        self.sig_fig_changed.emit(self.figure)

    def set_fig_size(self, fw, fh, units='IP'):
        """
        Set the figure width and height in inches if units is IP
        or in cm if units is SI.
        """
        if units == 'SI':
            # Convert values from cm to in.
            fw = fw / 2.54
            fh = fh / 2.54
        self.figure.set_size_inches(fw, fh)
        self.sig_fig_changed.emit(self.figure)

    def set_fig_language(self, language):
        """
        Set the language of the text shown in the figure. This needs to be
        impemented in the derived class.
        """
        raise NotImplementedError


class FigWaterLevelGLUE(FigCanvasBase):
    """
    This is a graph that shows observed ground-water levels and GLUE 5/95
    predicted water levels.
    """

    FIGNAME = "water_level_glue"

    def __init__(self, *args, **kargs):
        super(FigWaterLevelGLUE, self).__init__(*args, **kargs)
        fig = self.figure

        ax = self.ax0

        # ---- Axes labels

        self.set_axes_labels()

        # ---- Grids

        ax.grid(axis='x', color='0.35', ls=':', lw=1, zorder=200)
        ax.grid(axis='y', color='0.35', ls=':', lw=1, zorder=200)
        ax.invert_yaxis()

        # ----- Plot Observation

        self.plot_wlobs, = ax.plot([], [], color='b', ls='None',
                                   marker='.', ms=3, zorder=100)
        fig.canvas.draw()

        # ---- Yticks format

        ax.yaxis.set_ticks_position('left')
        ax.tick_params(axis='y', direction='out', labelsize=12)

        # ---- Xticks format

        ax.xaxis.set_ticks_position('bottom')
        ax.tick_params(axis='x', direction='out')
        fig.autofmt_xdate()

        # ---- Legend

        dum1 = mpl.patches.Rectangle((0, 0), 1, 1, fc='0.85', ec='0.65')
        dum2, = ax.plot([], [], color='b', ls='None', marker='.', ms=10)

        lg_handles = [dum2, dum1]
        lg_labels = ['Observations', 'GLUE 5/95']

        ax.legend(lg_handles, lg_labels, ncol=2, fontsize=12, frameon=False,
                  numpoints=1)

    def plot_prediction(self, glue_data):
        glue_dly = calcul_glue(glue_data, [0.05, 0.95], varname='hydrograph')

        dates, wlobs = glue_data['wl_date'], glue_data['wl_obs']
        ax = self.figure.axes[0]
        self.plot_wlobs.set_xdata(dates)
        self.plot_wlobs.set_ydata(wlobs)
        ax.fill_between(dates, glue_dly[:, -1]/1000, glue_dly[:, 0]/1000,
                        facecolor='0.85', lw=1, edgecolor='0.65', zorder=0)

    def set_fig_language(self, language):
        """
        Set the language of the text shown in the figure.
        """
        self.language = language
        self.set_axes_labels()
        self.sig_fig_changed.emit(self.figure)

    def set_axes_labels(self):
        """
        Set the text and position of the axes labels.
        """
        if self.language == 'French':
            xlabel = "Niveau d'eau (m sous la surface)"
        else:
            xlabel = 'Water Level (mbgs)'
        self.ax0.set_ylabel(xlabel, fontsize=16, labelpad=20)


class FigYearlyRechgGLUE(FigCanvasBase):
    """
    This is a graph that shows annual ground-water recharge and its
    uncertainty.
    """

    MARGINS = [1, 0.15, 0.15, 1.1]  # left, top, right, bottom
    FIGNAME = "gw_rechg_glue"

    def __init__(self, *args, **kargs):
        super(FigYearlyRechgGLUE, self).__init__(*args, **kargs)

        # ---- Customize Ax0

        self.ax0.set_axisbelow(True)

    def plot_recharge(self, data, Ymin0=None, Ymax0=None, year_limits=None):
        ax0 = self.ax0

        p = [0.05, 0.25, 0.5, 0.75, 0.95]
        year_labels, year_range, glue_rechg_yr = calcul_glue_yearly_rechg(
            data, p, year_limits)

        glue95_yr = glue_rechg_yr[:, -1]
        glue05_yr = glue_rechg_yr[:, 0]
        glue50_yr = glue_rechg_yr[:, 2]
        glue25_yr = glue_rechg_yr[:, 1]
        glue75_yr = glue_rechg_yr[:, -2]

        self.glue_year_rechg_avg = tuple(
            np.mean(glue_rechg_yr[:, i]) for i in range(5))

        # ---- Axis range

        Xmin0 = min(year_range)-1
        Xmax0 = max(year_range)+1

        if Ymax0 is None:
            Ymax0 = np.max(glue95_yr) + 50
        if Ymin0 is None:
            Ymin0 = 0

        # ---- Xticks format

        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x', direction='out', pad=1)
        ax0.set_xticks(year_range)
        ax0.xaxis.set_ticklabels(year_labels, rotation=45, ha='right')

        # ----- ticks format

        scale_yticks = 25 if np.max(glue95_yr) < 250 else 100
        scale_yticks_minor = 5 if np.max(glue95_yr) < 250 else 25
        yticks = np.arange(0, 2*Ymax0+1, scale_yticks)

        ax0.yaxis.set_ticks_position('left')
        ax0.set_yticks(yticks)
        ax0.tick_params(axis='y', direction='out', gridOn=True, labelsize=12)
        ax0.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle=':',
                 linewidth=0.5, dashes=[0.5, 5])

        ax0.set_yticks(np.arange(0, 2*Ymax0, scale_yticks_minor), minor=True)
        ax0.tick_params(axis='y', direction='out', which='minor', gridOn=False)

        # ---- Axis range

        ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

        # ---- Plot results

        ax0.plot(year_range, glue50_yr, ls='--', color='0.35', zorder=100)

        yerr = [glue50_yr-glue05_yr, glue95_yr-glue50_yr]
        herr = ax0.errorbar(year_range, glue50_yr, yerr=yerr,
                            fmt='o', capthick=1, capsize=4, ecolor='0',
                            elinewidth=1, mfc='White', mec='0', ms=5,
                            markeredgewidth=1, zorder=200)

        h25 = ax0.plot(year_range, glue25_yr, color='red',
                       dashes=[3, 5], alpha=0.65)
        ax0.plot(year_range, glue75_yr, color='red', dashes=[3, 5], alpha=0.65)

        # ---- Axes labels

        self.set_axes_labels()

        # ----- Legend

        lg_handles = [herr[0], herr[1], h25[0]]
        lg_labels = ['Recharge (GLUE 50)', 'Recharge (GLUE 5/95)',
                     'Recharge (GLUE 25/75)']

        ax0.legend(lg_handles, lg_labels, ncol=3, fontsize=12, frameon=False,
                   numpoints=1, loc='upper left')

        self.setup_yearly_avg_legend()

    def set_fig_language(self, language):
        """Set the language of the text shown in the figure."""
        self.language = language
        self.set_axes_labels()
        self.set_yearly_avg_legend_text()
        self.sig_fig_changed.emit(self.figure)

    def set_axes_labels(self):
        """Set the text and position of the axes labels."""
        if self.language.lower() == 'french':
            ylabl = "Recharge annuelle (mm/a)"
            xlabl = ("Années Hydrologiques (1er octobre d'une année "
                     "au 30 septembre de la suivante)")
        else:
            ylabl = "Annual Recharge (mm/y)"
            xlabl = ("Hydrological Years (October 1st of one "
                     "year to September 30th of the next)")
        self.ax0.set_ylabel(ylabl, fontsize=16, labelpad=15)
        self.ax0.set_xlabel(xlabl, fontsize=16, labelpad=20)

    def setup_yearly_avg_legend(self):
        """Setup the yearly average legend."""
        padding = mpl.transforms.ScaledTranslation(
            5/72, 5/72, self.figure.dpi_scale_trans)
        self.txt_yearly_avg = self.ax0.text(
            0, 0, '', va='bottom', ha='left', fontsize=10,
            transform=self.ax0.transAxes + padding)
        self.set_yearly_avg_legend_text()

    def set_yearly_avg_legend_text(self):
        """Set the text and position of for the yearly averages results."""
        if self.language.lower() == 'french':
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


# %% ---- if __name__ == '__main__'

if __name__ == '__main__':
    from gwhat.gwrecharge.gwrecharge_calc2 import RechgEvalWorker
    import sys

    app = QApplication(sys.argv)

    rechg_worker = RechgEvalWorker()
    data = rechg_worker.load_glue_from_npy("..\GLUE.npy")

    figstack = FigureStackManager()
    figstack.plot_results(data)
    figstack.show()

    sys.exit(app.exec_())
