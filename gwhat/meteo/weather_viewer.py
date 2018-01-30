# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# ---- Imports: Standard Libraries

import sys
import os
import os.path as osp
from datetime import datetime

# ---- Imports: Third Parties

import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QMenu, QToolButton, QGridLayout, QWidget,
                             QFileDialog, QApplication, QTableWidget,
                             QTableWidgetItem, QLabel, QHBoxLayout,
                             QHeaderView)

# ---- Imports: Local

from gwhat.colors2 import ColorsReader
from gwhat.common import StyleDB
from gwhat.common import icons
from gwhat.common.icons import QToolButtonVRectSmall, QToolButtonNormal
from gwhat.common.widgets import DialogWindow, VSep
from gwhat.widgets.buttons import RangeSpinBoxes
from gwhat.meteo.weather_reader import calcul_monthly_normals
from gwhat.common.utils import save_content_to_file

mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Arial']})


class WeatherViewer(DialogWindow):
    """
    GUI that allows to plot weather normals, save the graphs to file, see
    various stats about the dataset, etc...
    """
    def __init__(self, parent=None):
        super(WeatherViewer, self).__init__(parent, False, False)

        self.wxdset = None
        self.normals = None

        self.save_fig_dir = os.getcwd()
        self.meteo_dir = os.getcwd()
        self.language = 'English'

        self.__initUI__()

    def __initUI__(self):
        self.setWindowTitle('Weather Averages')
        self.setWindowIcon(icons.get_icon('master'))

        # ---- Toolbar

        # Initialize the widgets :

        menu_save = QMenu()
        menu_save.addAction('Save normals graph as...', self.save_graph)
        menu_save.addAction('Save normals table as...', self.save_normals)

        btn_save = QToolButtonNormal(icons.get_icon('save'))
        btn_save.setToolTip('Save normals')
        btn_save.setMenu(menu_save)
        btn_save.setPopupMode(QToolButton.InstantPopup)
        btn_save.setStyleSheet("QToolButton::menu-indicator {image: none;}")

        menu_export = QMenu()
        menu_export.addAction('Export daily time series as...',
                              self.select_export_file)
        menu_export.addAction('Export monthly time series as...',
                              self.select_export_file)
        menu_export.addAction('Export yearly time series as...',
                              self.select_export_file)

        self.btn_export = QToolButtonNormal(icons.get_icon('export_data'))
        self.btn_export.setToolTip('Export time series')
        self.btn_export.setPopupMode(QToolButton.InstantPopup)
        self.btn_export.setMenu(menu_export)
        self.btn_export.setStyleSheet(
                "QToolButton::menu-indicator {image: none;}")

        btn_showStats = QToolButtonNormal(icons.get_icon('showGrid'))
        btn_showStats.setToolTip(
                "Show the monthly weather normals data table.")
        btn_showStats.clicked.connect(self.show_monthly_grid)

        # Instantiate and define a layout for the year range widget :

        self.year_rng = RangeSpinBoxes(1000, 9999)
        self.year_rng.setRange(1800, datetime.now().year)
        self.year_rng.sig_range_changed.connect(self.update_normals)

        btn_expand = QToolButtonVRectSmall(icons.get_icon('expand_range_vert'))
        btn_expand.clicked.connect(self.expands_year_range)
        btn_expand.setToolTip("Set the maximal possible year range.")

        lay_expand = QGridLayout()
        lay_expand.addWidget(self.year_rng.spb_upper, 0, 0)
        lay_expand.addWidget(btn_expand, 0, 1)
        lay_expand.setContentsMargins(0, 0, 0, 0)
        lay_expand.setSpacing(1)

        qgrid = QHBoxLayout(self.year_rng)
        qgrid.setContentsMargins(0, 0, 0, 0)
        qgrid.addWidget(QLabel('Year Range :'))
        qgrid.addWidget(self.year_rng.spb_lower)
        qgrid.addWidget(QLabel('to'))
        qgrid.addLayout(lay_expand)

        # Generate the layout of the toolbar :

        toolbar_widget = QWidget()
        subgrid_toolbar = QGridLayout(toolbar_widget)

        buttons = [btn_save, self.btn_export, btn_showStats, VSep(),
                   self.year_rng]
        for col, btn in enumerate(buttons):
            subgrid_toolbar.addWidget(btn, 0, col)

        subgrid_toolbar.setColumnStretch(subgrid_toolbar.columnCount(), 4)
        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)

        # ---- Main Layout

        # Initialize the widgets :

        self.fig_weather_normals = FigWeatherNormals()
        self.grid_weather_normals = GridWeatherNormals()
        self.grid_weather_normals.hide()

        # Generate the layout :

        mainGrid = QGridLayout()

        row = 0
        mainGrid.addWidget(toolbar_widget, row, 0)
        row += 1
        mainGrid.addWidget(self.fig_weather_normals, row, 0)
        row += 1
        mainGrid.addWidget(self.grid_weather_normals, row, 0)

        mainGrid.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)
        mainGrid.setSpacing(10)
        mainGrid.setRowStretch(row, 500)
        mainGrid.setColumnStretch(0, 500)

        self.setLayout(mainGrid)

    def show_monthly_grid(self):
        if self.grid_weather_normals.isHidden():
            self.grid_weather_normals.show()
            self.setFixedHeight(self.size().height() +
                                self.layout().verticalSpacing() +
                                self.grid_weather_normals.calcul_height())
            self.sender().setAutoRaise(False)
        else:
            self.grid_weather_normals.hide()
            self.setFixedHeight(self.size().height() -
                                self.layout().verticalSpacing() -
                                self.grid_weather_normals.calcul_height())
            self.sender().setAutoRaise(True)

    def set_lang(self, lang):
        """Sets the language of all the labels in the figure."""
        self.language = lang
        self.fig_weather_normals.set_lang(lang)
        self.fig_weather_normals.draw()

    def set_weather_dataset(self, wxdset):
        """
        Generates the graph, updates the table, and updates the GUI for
        the new weather dataset.
        """
        self.wxdset = wxdset

        # Update the GUI :
        self.setWindowTitle('Weather Averages for %s' % wxdset['Station Name'])
        self.year_rng.setRange(np.min(wxdset['monthly']['Year']),
                               np.max(wxdset['monthly']['Year']))
        self.update_normals()

    def expands_year_range(self):
        """Sets the maximal possible year range."""
        self.year_rng.spb_upper.setValueSilently(
                np.max(self.wxdset['monthly']['Year']))
        self.year_rng.spb_lower.setValueSilently(
                np.min(self.wxdset['monthly']['Year']))
        self.update_normals()

    # ---- Normals

    def update_normals(self):
        """
        Forces a replot of the normals and an update of the table with the
        values calculated over the new range of years.
        """
        self.normals = self.calcul_normals()
        # Redraw the normals in the graph :
        self.fig_weather_normals.plot_monthly_normals(self.normals)
        self.fig_weather_normals.draw()
        # Update the values in the table :
        self.grid_weather_normals.populate_table(self.normals)

    def calcul_normals(self):
        """
        Calcul the normal values of the weather dataset for the currently
        defined period in the year range widget.
        """
        keys = ['Tmax', 'Tmin', 'Tavg', 'Ptot', 'Rain', 'Snow', 'PET']
        monthly = self.wxdset['monthly']
        normals = {}
        for key in keys:
            if monthly[key] is None:
                normals[key] = None
            else:
                normals[key] = calcul_monthly_normals(
                        monthly['Year'], monthly['Month'], monthly[key],
                        self.year_rng.lower_bound, self.year_rng.upper_bound)

        normals['Period'] = (self.year_rng.lower_bound,
                             self.year_rng.upper_bound)

        return normals

    def save_graph(self):
        yrmin = np.min(self.wxdset['Year'])
        yrmax = np.max(self.wxdset['Year'])
        staname = self.wxdset['Station Name']

        defaultname = 'WeatherAverages_%s (%d-%d)' % (staname, yrmin, yrmax)
        ddir = os.path.join(self.save_fig_dir, defaultname)

        dialog = QFileDialog()
        filename, ftype = dialog.getSaveFileName(
                self, 'Save graph', ddir, '*.pdf;;*.svg')

        if filename:
            if filename[-4:] != ftype[1:]:
                # Add a file extension if there is none.
                filename = filename + ftype[1:]

            self.save_fig_dir = os.path.dirname(filename)
            self.fig_weather_normals.figure.savefig(filename)

    def save_normals(self):
        """
        Save the montly and yearly normals in a file.
        """
        # Define a default name for the file :
        yrmin = self.normals['Period'][0]
        yrmax = self.normals['Period'][1]
        staname = self.wxdset['Station Name']

        defaultname = 'WeatherNormals_%s (%d-%d)' % (staname, yrmin, yrmax)
        ddir = osp.join(self.save_fig_dir, defaultname)

        # Open a dialog to get a save file name :
        dialog = QFileDialog()
        filename, ftype = dialog.getSaveFileName(
                self, 'Save normals', ddir, '*.xlsx;;*.xls;;*.csv')
        if filename:
            self.save_fig_dir = osp.dirname(filename)

            # Organise the content to save to file.
            hheader = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                       'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'YEAR']

            vrbs = ['Tmin', 'Tavg', 'Tmax', 'Rain', 'Snow', 'Ptot', 'PET']

            lbls = ['Daily Tmin (\u00B0C)', 'Daily Tavg (\u00B0C)',
                    'Daily Tmax (\u00B0C)', 'Rain (mm)', 'Snow (mm)',
                    'Total Precip. (mm)', 'ETP (mm)']

            fcontent = [hheader]
            for i, (vrb, lbl) in enumerate(zip(vrbs, lbls)):
                fcontent.append([lbl])
                fcontent[-1].extend(self.normals[vrb].tolist())
                if vrb in ['Tmin', 'Tavg', 'Tmax']:
                    fcontent[-1].append(np.mean(self.normals[vrb]))
                else:
                    fcontent[-1].append(np.sum(self.normals[vrb]))
            save_content_to_file(filename, fcontent)

    # ---- Export Time Series

    def select_export_file(self):
        if self.sender() == self.btn_export.menu().actions()[0]:
            time_frame = 'daily'
        elif self.sender() == self.btn_export.menu().actions()[1]:
            time_frame = 'monthly'
        elif self.sender() == self.btn_export.menu().actions()[2]:
            time_frame = 'yearly'
        else:
            return

        staname = self.wxdset['Station Name']
        defaultname = 'Weather%s_%s' % (time_frame.capitalize(), staname)

        ddir = os.path.join(self.save_fig_dir, defaultname)
        dialog = QFileDialog()

        filename, ftype = dialog.getSaveFileName(
                self, 'Export %s' % time_frame, ddir, '*.xlsx;;*.xls;;*.csv')

        if filename:
            self.save_fig_dir = osp.dirname(filename)
            self.export_series_tofile(filename, time_frame)

    def export_series_tofile(self, filename, time_frame):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.wxdset.export_dataset_to_file(filename, time_frame)
        QApplication.restoreOverrideCursor()


class FigureLabels(object):

    LANGUAGES = ['english', 'french']

    def __init__(self, language):

        # Legend :

        self.Pyrly = 'Annual total precipitation = %0.0f mm'
        self.Tyrly = 'Average annual air temperature = %0.1f °C'
        self.rain = 'Rain'
        self.snow = 'Snow'
        self.Tmax = 'Temp. max.'
        self.Tmin = 'Temp. min.'
        self.Tavg = 'Temp. mean'

        # Labels :

        self.Tlabel = 'Monthly Air Temperature (°C)'
        self.Plabel = 'Monthly Total Precipitation (mm)'
        self.month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

        if language.lower() == 'french':

            # Legend :

            self.Pyrly = 'Précipitations totales annuelles = %0.0f mm'
            self.Tyrly = 'Température moyenne annuelle = %0.1f °C'
            self.rain = 'Pluie'
            self.snow = 'Neige'
            self.Tmax = 'Températures max.'
            self.Tmin = 'Températures min.'
            self.Tavg = 'Températures moy.'

            # Labels :

            self.Tlabel = 'Températures moyennes mensuelles (°C)'
            self.Plabel = 'Précipitations totales mensuelles (mm)'
            self.month_names = ["JAN", "FÉV", "MAR", "AVR", "MAI", "JUN",
                                "JUL", "AOÛ", "SEP", "OCT", "NOV", "DÉC"]


class FigWeatherNormals(FigureCanvasQTAgg):
    """
    This is the class that does all the plotting of the weather normals.

    ax0 is used to plot precipitation
    ax1 is used to plot air temperature
    ax3 is used to plot the legend on top of the graph.

    """

    def __init__(self, lang='English'):
        lang = lang if lang.lower() in FigureLabels.LANGUAGES else 'English'
        self.__figlang = lang
        self.__figlabels = FigureLabels(lang)
        self.normals = None

        fw, fh = 8.5, 5.
        fig = mpl.figure.Figure(figsize=(fw, fh), facecolor='white')
        super(FigWeatherNormals, self).__init__(fig)

        # Define the Margins :

        left_margin = 1/fw
        right_margin = 1/fw
        bottom_margin = 0.7/fh
        top_margin = 0.1/fh

        # ---- Yearly Avg Labels

        # The yearly yearly averages for the mean air temperature and
        # the total precipitation are displayed in <ax3>, which is placed on
        # top of the axes that display the data (<ax0> and <ax1>).

        ax3 = fig.add_axes([0, 0, 1, 1], zorder=1)  # temporary position
        ax3.patch.set_visible(False)
        ax3.spines['bottom'].set_visible(False)
        ax3.tick_params(axis='both', bottom='off', top='off', left='off',
                        right='off', labelbottom='off', labeltop='off',
                        labelleft='off', labelright='off')

        # Mean Annual Air Temperature :

        # Places first label at the top left corner of <ax3> with a horizontal
        # padding of 5 points and downward padding of 3 points.

        dx, dy = 5/72., -3/72.
        padding = mpl.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)
        transform = ax3.transAxes + padding

        ax3.text(0., 1., 'Mean Annual Air Temperature',
                 fontsize=13, va='top', transform=transform)

        # Mean Annual Precipitation :

        # Get the bounding box of the first label.

        renderer = self.get_renderer()
        bbox = ax3.texts[0].get_window_extent(renderer)
        bbox = bbox.transformed(ax3.transAxes.inverted())

        # Places second label below the first label with a horizontal
        # padding of 5 points and downward padding of 3 points.

        ax3.text(0., bbox.y0, 'Mean Annual Precipitation',
                 fontsize=13, va='top', transform=transform)

        bbox = ax3.texts[1].get_window_extent(renderer)
        bbox = bbox.transformed(fig.transFigure.inverted())

        # Update geometry :

        # Updates the geometry and position of <ax3> to accomodate the text.

        x0 = left_margin
        axw = 1 - (left_margin + right_margin)
        axh = 1 - bbox.y0 - (dy / fw)
        y0 = 1 - axh - top_margin

        ax3.set_position([x0, y0, axw, axh])

        # ---- Data Axes

        axh = y0 - bottom_margin
        y0 = y0 - axh

        # Precipitation :

        ax0 = fig.add_axes([x0, y0, axw, axh], zorder=1)
        ax0.patch.set_visible(False)
        ax0.spines['top'].set_visible(False)
        ax0.set_axisbelow(True)

        # Air Temperature :

        ax1 = fig.add_axes(ax0.get_position(), frameon=False, zorder=5,
                           sharex=ax0)

        # ---- Initialize the Artists

        # This is only to initiates the artists and to set their parameters
        # in advance. The plotting of the data is actually done by calling
        # the <plot_monthly_normals> method.

        XPOS = np.arange(-0.5, 12.51, 1)
        XPOS[0] = 0
        XPOS[-1] = 12
        y = range(len(XPOS))
        colors = ['#990000', '#FF0000', '#FF6666']

        # Dashed lines for Tmax, Tavg, and Tmin :

        for i in range(3):
            ax1.plot(XPOS, y, color=colors[i], ls='--', lw=1.5, zorder=100)

        # Markers for Tavg :

        ax1.plot(XPOS[1:-1], y[1:-1], color=colors[1], marker='o', ls='none',
                 ms=6, zorder=100, mec=colors[1], mfc='white', mew=1.5)

        # ---- Xticks Formatting

        Xmin0 = 0
        Xmax0 = 12.001

        # Major ticks
        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x', direction='out')
        ax0.xaxis.set_ticklabels([])
        ax0.set_xticks(np.arange(Xmin0, Xmax0))

        ax1.tick_params(axis='x', which='both', bottom='off', top='off',
                        labelbottom='off')

        # Minor ticks
        ax0.set_xticks(np.arange(Xmin0+0.5, Xmax0+0.49, 1), minor=True)
        ax0.tick_params(axis='x', which='minor', direction='out',
                        length=0, labelsize=13)
        ax0.xaxis.set_ticklabels(self.fig_labels.month_names, minor=True)

        # ---- Y-ticks Formatting

        # Precipitation
        ax0.yaxis.set_ticks_position('right')
        ax0.tick_params(axis='y', direction='out', labelsize=13)

        ax0.tick_params(axis='y', which='minor', direction='out')
        ax0.yaxis.set_ticklabels([], minor=True)

        # Air Temperature
        ax1.yaxis.set_ticks_position('left')
        ax1.tick_params(axis='y', direction='out', labelsize=13)

        ax1.tick_params(axis='y', which='minor', direction='out')
        ax1.yaxis.set_ticklabels([], minor=True)

        # ---- Grid Parameters

    #    ax0.grid(axis='y', color=[0.5, 0.5, 0.5], linestyle=':', linewidth=1,
    #             dashes=[1, 5])
    #    ax0.grid(axis='y', color=[0.75, 0.75, 0.75], linestyle='-',
#                 linewidth=0.5)

        # ---- Limits of the Axes

        ax0.set_xlim(Xmin0, Xmax0)

        # ---- Legend

        self.plot_legend()

    @property
    def fig_labels(self):
        return self.__figlabels

    @property
    def fig_language(self):
        return self.__figlang

    def set_lang(self, lang):
        """Sets the language of the figure labels."""
        lang = lang if lang.lower() in FigureLabels.LANGUAGES else 'English'
        self.__figlabels = FigureLabels(lang)
        self.__figlang = lang

        # Update the labels in the plot :
        self.plot_legend()
        self.figure.axes[1].xaxis.set_ticklabels(
                self.fig_labels.month_names, minor=True)
        if self.normals is not None:
            self.set_axes_labels()
            self.update_yearly_avg()

    def plot_legend(self):
        """Plot the legend of the figure."""
        ax = self.figure.axes[2]

        # bbox transform :

        padding = mpl.transforms.ScaledTranslation(5/72, -5/72,
                                                   self.figure.dpi_scale_trans)
        transform = ax.transAxes + padding

        # Define proxy artists :

        colors = ColorsReader()
        colors.load_colors_db()

        rec1 = mpl.patches.Rectangle((0, 0), 1, 1,
                                     fc=colors.rgb['Snow'], ec='none')
        rec2 = mpl.patches.Rectangle((0, 0), 1, 1,
                                     fc=colors.rgb['Rain'], ec='none')

        # Define the legend labels and markers :

        lines = [ax.lines[0], ax.lines[1], ax.lines[2], rec2, rec1]
        labels = [self.fig_labels.Tmax, self.fig_labels.Tavg,
                  self.fig_labels.Tmin, self.fig_labels.rain,
                  self.fig_labels.snow]

        # Plot the legend :

        leg = ax.legend(lines, labels, numpoints=1, fontsize=13,
                        borderaxespad=0, loc='upper left', borderpad=0,
                        bbox_to_anchor=(0, 1), bbox_transform=transform)
        leg.draw_frame(False)

    def plot_monthly_normals(self, normals):
        """Plot the normals on the figure."""

        self.normals = normals

        # Assign local variables :

        Tmax_norm = normals['Tmax']
        Tmin_norm = normals['Tmin']
        Tavg_norm = normals['Tavg']
        Ptot_norm = normals['Ptot']
        Rain_norm = normals['Rain']
        Snow_norm = Ptot_norm - Rain_norm

        # Define the range of the axis :

        Yscale0 = 10 if np.sum(Ptot_norm) < 500 else 20  # Precipitation (mm)
        Yscale1 = 5  # Temperature (deg C)

        SCA0 = np.arange(0, 10000, Yscale0)
        SCA1 = np.arange(-100, 100, Yscale1)

        # ---- Precipitation ----

        indx = np.where(SCA0 > np.max(Ptot_norm))[0][0]
        Ymax0 = SCA0[indx+1]

        indx = np.where(SCA0 <= np.min(Snow_norm))[0][-1]
        Ymin0 = SCA0[indx]

        NZGrid0 = (Ymax0 - Ymin0) / Yscale0

        # ---- Temperature ----

        indx = np.where(SCA1 > np.max(Tmax_norm))[0][0]
        Ymax1 = SCA1[indx]

        indx = np.where(SCA1 < np.min(Tmin_norm))[0][-1]
        Ymin1 = SCA1[indx]

        NZGrid1 = (Ymax1 - Ymin1) / Yscale1

        # ---- Uniformization Of The Grids ----

        if NZGrid0 > NZGrid1:
            Ymin1 = Ymax1 - NZGrid0 * Yscale1
        elif NZGrid0 < NZGrid1:
            Ymax0 = Ymin0 + NZGrid1 * Yscale0
        elif NZGrid0 == NZGrid1:
            pass

        # ---- Adjust Space For Text ----

        # In case there is a need to force the value
        # ----
        if False:
            Ymax0 = 100
            Ymax1 = 30
            Ymin1 = -20
        # ----

        # Define the fomatting of the yticks :

        ax0 = self.figure.axes[1]
        ax1 = self.figure.axes[2]
        ax3 = self.figure.axes[0]

        # ---- Precip (host) ----

        yticks = np.arange(Ymin0, Ymax0 + Yscale0/10, Yscale0)
        ax0.set_yticks(yticks)

        yticks_minor = np.arange(yticks[0], yticks[-1], 5)
        ax0.set_yticks(yticks_minor, minor=True)

        # ---- Air Temp ----

        yticks1 = np.arange(Ymin1, Ymax1 + Yscale1/10., Yscale1)
        ax1.set_yticks(yticks1)

        yticks1_minor = np.arange(yticks1[0], yticks1[-1], Yscale1/5.)
        ax1.set_yticks(yticks1_minor, minor=True)

        # Set the range of the axis :

        ax0.set_ylim(Ymin0, Ymax0)
        ax1.set_ylim(Ymin1, Ymax1)

        # ---- LABELS

        self.set_axes_labels()
        self.set_year_range()

        # ---- PLOTTING

        self.plot_precip(Ptot_norm, Snow_norm)
        self.plot_air_temp(Tmax_norm, Tavg_norm, Tmin_norm)
        self.update_yearly_avg()

        # ---- Clipping

        # There is currently a bug regarding this. So we need to do a
        # workaround

        x0, x1 = ax1.get_position().x0, ax1.get_position().x1
        y0, y1 = ax1.get_position().y0, ax3.get_position().y1

        dummy_ax = self.figure.add_axes([x0, y0, x1-x0, y1-y0])
        dummy_ax.patch.set_visible(False)
        dummy_ax.axis('off')

        dummy_plot, = dummy_ax.plot([], [], clip_on=True)

        clip_bbox = dummy_plot.get_clip_box()

        for line in ax1.lines:
            line.set_clip_box(clip_bbox)

    def set_axes_labels(self):
        """Sets the labels of the y axis."""
        # Set the label fo the precipitation :
        ax0 = self.figure.axes[1]
        ax0.set_ylabel(self.fig_labels.Plabel, va='bottom',
                       fontsize=16, rotation=270)
        ax0.yaxis.set_label_coords(1.09, 0.5)

        # Set the label fo the air temperature :
        ax1 = self.figure.axes[2]
        ax1.set_ylabel(self.fig_labels.Tlabel, va='bottom', fontsize=16)
        ax1.yaxis.set_label_coords(-0.09, 0.5)

    def set_year_range(self):
        """Sets the year range label that is displayed below the x axis."""
        if self.normals is not None:
            ax0 = self.figure.axes[1]
            yearmin, yearmax = self.normals['Period']
            if yearmin == yearmax:
                ax0.set_xlabel("%d" % yearmin, fontsize=16, labelpad=10)
            else:
                ax0.set_xlabel("%d - %d" % (yearmin, yearmax), fontsize=16,
                               labelpad=10)

    # ---- Plot the Data

    def plot_precip(self, PNORM, SNORM):

        # Define the vertices manually :

        Xmid = np.arange(0.5, 12.5, 1)
        n = 0.5   # Controls the width of the bins
        f = 0.75  # Controls the spacing between the bins

        Xpos = np.vstack((Xmid - n * f, Xmid - n * f,
                          Xmid + n * f, Xmid + n * f)).transpose().flatten()

        Ptot = np.vstack((PNORM * 0, PNORM,
                          PNORM, PNORM * 0)).transpose().flatten()

        Snow = np.vstack((SNORM * 0, SNORM,
                          SNORM, SNORM * 0)).transpose().flatten()

        # Plot the data :

        ax = self.figure.axes[1]
        for collection in reversed(ax.collections):
            collection.remove()

        colors = ColorsReader()
        colors.load_colors_db()

        ax.fill_between(Xpos, 0, Ptot, edgecolor='none',
                        color=colors.rgb['Rain'])
        ax.fill_between(Xpos, 0, Snow, edgecolor='none',
                        color=colors.rgb['Snow'])

    def plot_air_temp(self, Tmax_norm, Tavg_norm, Tmin_norm):
        for i, Tnorm in enumerate([Tmax_norm, Tavg_norm, Tmin_norm]):
            T0 = (Tnorm[-1]+Tnorm[0])/2
            T = np.hstack((T0, Tnorm, T0))
            self.figure.axes[2].lines[i].set_ydata(T)
        self.figure.axes[2].lines[3].set_ydata(Tavg_norm)

    def update_yearly_avg(self):

        Tavg_norm = self.normals['Tavg']
        Ptot_norm = self.normals['Ptot']
        ax = self.figure.axes[0]

        # Update the position of the labels :

        bbox = ax.texts[0].get_window_extent(self.get_renderer())
        bbox = bbox.transformed(ax.transAxes.inverted())
        ax.texts[1].set_position((0, bbox.y0))

        # Update the text of the labels :

        ax.texts[0].set_text(self.fig_labels.Tyrly % np.mean(Tavg_norm))
        ax.texts[1].set_text(self.fig_labels.Pyrly % np.sum(Ptot_norm))


class GridWeatherNormals(QTableWidget):

    def __init__(self, parent=None):
        super(GridWeatherNormals, self).__init__(parent)

        self.initUI()

    def initUI(self):

        self.setFrameStyle(StyleDB().frame)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)

        HEADER = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                  'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'YEAR')

        self.setColumnCount(len(HEADER))
        self.setHorizontalHeaderLabels(HEADER)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHighlightSections(False)

        self.setRowCount(7)
        self.setVerticalHeaderLabels(['Daily Tmax (°C)', 'Daily Tmin (°C)',
                                      'Daily Tavg (°C)', 'Rain (mm)',
                                      'Snow (mm)', 'Total Precip (mm)',
                                      'ETP (mm)'])

        self.resizeRowsToContents()
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setHighlightSections(False)

    def populate_table(self, NORMALS):

        # ---- Air Temperature

        for row, key in enumerate(['Tmax', 'Tmin', 'Tavg']):
            # Months
            for col in range(12):
                item = QTableWidgetItem('%0.1f' % NORMALS[key][col])
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(item.flags() & Qt.AlignCenter)
                self.setItem(row, col, item)

            # Year
            yearVal = np.mean(NORMALS[key])
            item = QTableWidgetItem('%0.1f' % yearVal)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 12, item)

        # ---- Rain

        row = 3
        # Months
        for col in range(12):
            item = QTableWidgetItem('%0.1f' % NORMALS['Rain'][col])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)

        # Year
        yearVal = np.sum(NORMALS['Rain'])
        item = QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- Snow

        row = 4
        # Months
        for col in range(12):
            snow4cell = NORMALS['Ptot'][col] - NORMALS['Rain'][col]
            item = QTableWidgetItem('%0.1f' % snow4cell)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)

        # Year
        yearVal = np.sum(NORMALS['Ptot'] - NORMALS['Rain'])
        item = QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- Total Precip

        row = 5
        # Months
        for col in range(12):
            item = QTableWidgetItem('%0.1f' % NORMALS['Ptot'][col])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)
        # Year
        yearVal = np.sum(NORMALS['Ptot'])
        item = QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- ETP

        row = 6
        # Months
        for col in range(12):
            item = QTableWidgetItem('%0.1f' % NORMALS['PET'][col])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)
        # Year
        yearVal = np.sum(NORMALS['PET'])
        item = QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 12, item)

    def calcul_height(self):
        h = self.horizontalHeader().height() + 2*self.frameWidth()
        for i in range(self.rowCount()):
            h += self.rowHeight(i)
        return h


# %% if __name__ == '__main__'

if __name__ == '__main__':
    from gwhat.meteo.weather_reader import WXDataFrame
    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

    fmeteo = ("C:\\Users\\jsgosselin\\GWHAT\\Projects\\"
              "Example\\Meteo\\Output\\FARNHAM (7022320)\\"
              "FARNHAM (7022320)_2005-2010.out")
    wxdset = WXDataFrame(fmeteo)

    w = WeatherViewer()
    w.save_fig_dir = os.getcwd()

    w.set_lang('French')
    w.set_weather_dataset(wxdset)
    w.show()

    app.exec_()
