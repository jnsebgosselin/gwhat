# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# ---- Standard library imports

import sys
import os
import csv
from time import strftime

# ---- Third party imports

import xlsxwriter
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QMenu, QToolButton, QGridLayout, QWidget,
                             QFileDialog, QApplication, QTableWidget,
                             QTableWidgetItem)

# ---- Local imports

from gwhat.colors2 import ColorsReader
from gwhat.common import StyleDB, QToolButtonNormal
from gwhat.common import icons
from gwhat.common.widgets import DialogWindow
from gwhat import __namever__
from gwhat.common.utils import save_content_to_file

mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Arial']})


class LabelDB(object):

    def __init__(self, language):

        # ---- Legend ----

        self.Pyrly = 'Annual total precipitation = %0.0f mm'
        self.Tyrly = 'Average annual air temperature = %0.1f °C'
        self.rain = 'Rain'
        self.snow = 'Snow'
        self.Tmax = 'Temp. max.'
        self.Tmin = 'Temp. min.'
        self.Tavg = 'Temp. mean'

        # ---- Labels ----

        self.Tlabel = 'Monthly Air Temperature (°C)'
        self.Plabel = 'Monthly Total Precipitation (mm)'
        self.month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

        if language == 'French':

            # ---- Legend ----

            self.Pyrly = 'Précipitations totales annuelles = %0.0f mm'
            self.Tyrly = 'Température moyenne annuelle = %0.1f °C'
            self.rain = 'Pluie'
            self.snow = 'Neige'
            self.Tmax = 'Températures min.'
            self.Tmin = 'Températures max.'
            self.Tavg = 'Températures moy.'

            # ---- Labels ----

            self.Tlabel = 'Températures moyennes mensuelles (°C)'
            self.Plabel = 'Précipitations totales mensuelles (mm)'
            self.month_names = ["JAN", u"FÉV", "MAR", "AVR", "MAI", "JUN",
                                "JUL", u"AOÛ", "SEP", "OCT", "NOV", u"DÉC"]


class WeatherAvgGraph(DialogWindow):
    """
    GUI that allows to plot weather normals, save the graphs to file, see
    various stats about the dataset, etc...
    """
    def __init__(self, parent=None):
        super(WeatherAvgGraph, self).__init__(parent)

        self.wxdset = None

        self.save_fig_dir = os.getcwd()
        self.meteo_dir = os.getcwd()
        self.language = 'English'

        self.__initUI__()

    # =========================================================================

    def __initUI__(self):

        self.setWindowTitle('Weather Averages')
        self.setWindowIcon(icons.get_icon('master'))

        # ---------------------------------------------------- TOOLBAR ----

        # Widgets :

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
        btn_showStats.setToolTip('Show monthly weather normals data table.')
        btn_showStats.clicked.connect(self.show_monthly_grid)

        # Layout :

        subgrid_toolbar = QGridLayout()
        toolbar_widget = QWidget()

        col = 0
        row = 0
        subgrid_toolbar.addWidget(btn_save, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_export, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_showStats, row, col)
        col += 1
        subgrid_toolbar.setColumnStretch(col, 4)

        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)

        toolbar_widget.setLayout(subgrid_toolbar)

        # -------------------------------------------------- MAIN GRID ----

        # ---- widgets ----

        self.fig_weather_normals = FigWeatherNormals()
        self.grid_weather_normals = GridWeatherNormals()
        self.grid_weather_normals.hide()

        # ---- layout ----

        mainGrid = QGridLayout()

        row = 0
        mainGrid.addWidget(toolbar_widget, row, 0)
        row += 1
        mainGrid.addWidget(self.fig_weather_normals, row, 0)
        row += 1
        mainGrid.addWidget(self.grid_weather_normals, row, 0)

        mainGrid.setContentsMargins(10, 10, 10, 10)  # (L,T,R,B)
        mainGrid.setSpacing(10)
        mainGrid.setRowStretch(row, 500)
        mainGrid.setColumnStretch(0, 500)

        self.setLayout(mainGrid)

    # =========================================================================

    def show_monthly_grid(self):
        if self.grid_weather_normals.isHidden():
            self.grid_weather_normals.show()
            self.setFixedHeight(self.size().height()+250)
#            self.setFixedWidth(self.size().width()+75)
            self.sender().setAutoRaise(False)
        else:
            self.grid_weather_normals.hide()
            self.setFixedHeight(self.size().height()-250)
#            self.setFixedWidth(self.size().width()-75)
            self.sender().setAutoRaise(True)

    # =========================================================================

    def set_lang(self, lang):
        self.language = lang
        self.fig_weather_normals.set_lang(lang)
        self.fig_weather_normals.draw()

    # =========================================================================

    def generate_graph(self, wxdset):
        self.wxdset = wxdset
        self.fig_weather_normals.plot_monthly_normals(wxdset['normals'])
        self.fig_weather_normals.draw()

        self.setWindowTitle('Weather Averages for %s' % wxdset['Station Name'])

        self.grid_weather_normals.populate_table(wxdset['normals'])

    # ---------------------------------------------------------------------

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

    # =========================================================================

    def save_normals(self):
        yrmin = np.min(self.wxdset['Year'])
        yrmax = np.max(self.wxdset['Year'])
        staname = self.wxdset['Station Name']

        defaultname = 'WeatherNormals_%s (%d-%d)' % (staname, yrmin, yrmax)
        ddir = os.path.join(self.save_fig_dir, defaultname)

        dialog = QFileDialog()
        filename, ftype = dialog.getSaveFileName(
                self, 'Save normals', ddir, '*.xlsx;;*.xls;;*.csv')

        hheader = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                   'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'YEAR']

        vrbs = ['Tmin', 'Tavg', 'Tmax', 'Rain', 'Snow', 'Ptot', 'PET']

        lbls = ['Daily Tmin (\u00B0C)', 'Daily Tavg (\u00B0C)',
                'Daily Tmax (\u00B0C)', 'Rain (mm)', 'Snow (mm)',
                'Total Precip. (mm)', 'ETP (mm)']

        if ftype in ['*.xlsx', '*.xls']:
            wb = xlsxwriter.Workbook(filename)
            ws = wb.add_worksheet()

            ws.write_row(0, 0, hheader)
            for i, (vrb, lbl) in enumerate(zip(vrbs, lbls)):
                ws.write(i+1, 0, lbl)
                ws.write_row(i+1, 1, self.wxdset['normals'][vrb])
                if vrb in ['Tmin', 'Tavg', 'Tmax']:
                    ws.write(i+1, 13, np.mean(self.wxdset['normals'][vrb]))
                else:
                    ws.write(i+1, 13, np.sum(self.wxdset['normals'][vrb]))
        elif ftype == '*.csv':
            fcontent = [hheader]
            for i, (vrb, lbl) in enumerate(zip(vrbs, lbls)):
                fcontent.append([lbl])
                fcontent[-1].extend(self.wxdset['normals'][vrb].tolist())
                if vrb in ['Tmin', 'Tavg', 'Tmax']:
                    fcontent[-1].append(np.mean(self.wxdset['normals'][vrb]))
                else:
                    fcontent[-1].append(np.sum(self.wxdset['normals'][vrb]))

            with open(filename, 'w', encoding='utf8')as f:
                writer = csv.writer(f, delimiter=',', lineterminator='\n')
                writer.writerows(fcontent)

    # ================================================= Export Time Series ====

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
            self.export_series_tofile(filename, time_frame)

    def export_series_tofile(self, filename, time_frame):
        if time_frame == 'daily':
            vrbs = ['Year', 'Month', 'Day']
            lbls = ['Year', 'Month', 'Day']
        elif time_frame == 'monthly':
            vrbs = ['Year', 'Month']
            lbls = ['Year', 'Month']
        elif time_frame == 'yearly':
            vrbs = ['Year']
            lbls = ['Year']
        else:
            raise ValueError('"time_frame" must be either "yearly", "monthly"'
                             ' or "daily".')

        vrbs.extend(['Tmin', 'Tavg', 'Tmax', 'Rain', 'Snow', 'Ptot', 'PET'])
        lbls.extend(['Tmin (\u00B0C)', 'Tavg (\u00B0C)', 'Tmax (\u00B0C)',
                     'Rain (mm)', 'Snow (mm)', 'Ptot (mm)',
                     'PET (mm)'])

        QApplication.setOverrideCursor(Qt.WaitCursor)

        startdate = '%02d/%02d/%d' % (self.wxdset['Day'][0],
                                      self.wxdset['Month'][0],
                                      self.wxdset['Year'][0])
        enddate = '%02d/%02d/%d' % (self.wxdset['Day'][-1],
                                    self.wxdset['Month'][-1],
                                    self.wxdset['Year'][-1])

        fcontent = [['Station Name', self.wxdset['Station Name']],
                    ['Province', self.wxdset['Province']],
                    ['Latitude', self.wxdset['Longitude']],
                    ['Longitude', self.wxdset['Longitude']],
                    ['Elevation', self.wxdset['Elevation']],
                    ['Climate Identifier', self.wxdset['Climate Identifier']],
                    ['', ''],
                    ['Start Date ', startdate],
                    ['End Date ', enddate],
                    ['', ''],
                    ['Created by', __namever__],
                    ['Created on', strftime("%d/%m/%Y")],
                    ['', '']
                    ]
        fcontent.append(lbls)

        N = len(self.wxdset[time_frame]['Year'])
        M = len(vrbs)
        data = np.zeros((N, M))
        for j, vrb in enumerate(vrbs):
            data[:, j] = self.wxdset[time_frame][vrb]
        fcontent.extend(data.tolist())

        save_content_to_file(filename, fcontent)
        QApplication.restoreOverrideCursor()


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class FigWeatherNormals(FigureCanvasQTAgg):
    """
    This is the class that does all the plotting of the weather normals.

    ax0 is used to plot precipitation
    ax1 is used to plot air temperature
    ax3 is used to plot the legend on top of the graph.

    """

    def __init__(self, lang='English'):

        fw, fh = 8.5, 5.
        fig = mpl.figure.Figure(figsize=(fw, fh), facecolor='white')

        super(FigWeatherNormals, self).__init__(fig)

        self.lang = lang
        self.normals = None

        labelDB = LabelDB(self.lang)
        month_names = labelDB.month_names

        # --------------------------------------------------- Define Margins --

        left_margin = 1/fw
        right_margin = 1/fw
        bottom_margin = 0.35/fh
        top_margin = 0.1/fh

        # ------------------------------------------------ Yearly Avg Labels --

        # The yearly yearly averages for the mean air temperature and
        # the total precipitation are displayed in <ax3>, which is placed on
        # top of the axes that display the data (<ax0> and <ax1>).

        ax3 = fig.add_axes([0, 0, 1, 1], zorder=1)  # temporary position
        ax3.patch.set_visible(False)
        ax3.spines['bottom'].set_visible(False)
        ax3.tick_params(axis='both', bottom='off', top='off', left='off',
                        right='off', labelbottom='off', labeltop='off',
                        labelleft='off', labelright='off')

        # ---- Mean Annual Air Temperature ----

        # Places first label at the top left corner of <ax3> with a horizontal
        # padding of 5 points and downward padding of 3 points.

        dx, dy = 5/72., -3/72.
        padding = mpl.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)
        transform = ax3.transAxes + padding

        ax3.text(0., 1., 'Mean Annual Air Temperature',
                 fontsize=13, va='top', transform=transform)

        # ---- Mean Annual Precipitation ----

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

        # ---- update geometry ----

        # Updates the geometry and position of <ax3> to accomodate the text.

        x0 = left_margin
        axw = 1 - (left_margin + right_margin)
        axh = 1 - bbox.y0 - (dy / fw)
        y0 = 1 - axh - top_margin

        ax3.set_position([x0, y0, axw, axh])

        # -------------------------------------------------------- Data Axes --

        axh = y0 - bottom_margin
        y0 = y0 - axh

        # ---- Precip ----

        ax0 = fig.add_axes([x0, y0, axw, axh], zorder=1)
        ax0.patch.set_visible(False)
        ax0.spines['top'].set_visible(False)
        ax0.set_axisbelow(True)

        # ---- Air Temp. ----

        ax1 = fig.add_axes(ax0.get_position(), frameon=False, zorder=5,
                           sharex=ax0)

        # ----------------------------------------------------- INIT ARTISTS --

        # This is only to initiates the artists and to set their parameters
        # in advance. The plotting of the data is actually done by calling
        # the <plot_monthly_normals> method.

        XPOS = np.arange(-0.5, 12.51, 1)
        XPOS[0] = 0
        XPOS[-1] = 12
        y = range(len(XPOS))
        colors = ['#990000', '#FF0000', '#FF6666']

        # dashed lines for Tmax, Tavg, and Tmin :

        for i in range(3):
            ax1.plot(XPOS, y, color=colors[i], ls='--', lw=1.5, zorder=100)

        # markers for Tavg :

        ax1.plot(XPOS[1:-1], y[1:-1], color=colors[1], marker='o', ls='none',
                 ms=6, zorder=100, mec=colors[1], mfc='white', mew=1.5)

        # ------------------------------------------------- XTICKS FORMATING --

        Xmin0 = 0
        Xmax0 = 12.001

        # ---- major ----

        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x', direction='out')
        ax0.xaxis.set_ticklabels([])
        ax0.set_xticks(np.arange(Xmin0, Xmax0))

        ax1.tick_params(axis='x', which='both', bottom='off', top='off',
                        labelbottom='off')

        # ---- minor ----

        ax0.set_xticks(np.arange(Xmin0+0.5, Xmax0+0.49, 1), minor=True)
        ax0.tick_params(axis='x', which='minor', direction='out',
                        length=0, labelsize=13)
        ax0.xaxis.set_ticklabels(month_names, minor=True)

        # ------------------------------------------------- Yticks Formating --

        # ---- Precipitation ----

        ax0.yaxis.set_ticks_position('right')
        ax0.tick_params(axis='y', direction='out', labelsize=13)

        ax0.tick_params(axis='y', which='minor', direction='out')
        ax0.yaxis.set_ticklabels([], minor=True)

        # ---- Air Temp. ----

        ax1.yaxis.set_ticks_position('left')
        ax1.tick_params(axis='y', direction='out', labelsize=13)

        ax1.tick_params(axis='y', which='minor', direction='out')
        ax1.yaxis.set_ticklabels([], minor=True)

        # ------------------------------------------------------------- GRID --

    #    ax0.grid(axis='y', color=[0.5, 0.5, 0.5], linestyle=':', linewidth=1,
    #             dashes=[1, 5])
    #    ax0.grid(axis='y', color=[0.75, 0.75, 0.75], linestyle='-',
#                 linewidth=0.5)

        # ------------------------------------------------------------ XLIMS --

        ax0.set_xlim(Xmin0, Xmax0)

        # ------------------------------------------------------ Plot Legend --

        self.plot_legend()

    # =========================================================== Language ====

    def set_lang(self, lang):
        self.lang = lang
        if self.normals is None:
            return

        self.plot_legend()
        self.set_axes_labels()
        self.update_yearly_avg()
        month_names = LabelDB(self.lang).month_names
        self.figure.axes[1].xaxis.set_ticklabels(month_names, minor=True)

    # ============================================================ Legend =====

    def plot_legend(self):

        ax = self.figure.axes[2]  # Axe on which the legend is hosted

        # --- bbox transform --- #

        padding = mpl.transforms.ScaledTranslation(5/72, -5/72,
                                                   self.figure.dpi_scale_trans)
        transform = ax.transAxes + padding

        # --- proxy artists --- #

        colors = ColorsReader()
        colors.load_colors_db()

        rec1 = mpl.patches.Rectangle((0, 0), 1, 1,
                                     fc=colors.rgb['Snow'], ec='none')
        rec2 = mpl.patches.Rectangle((0, 0), 1, 1,
                                     fc=colors.rgb['Rain'], ec='none')

        # --- legend entry --- #

        lines = [ax.lines[0], ax.lines[1], ax.lines[2], rec2, rec1]
        labelDB = LabelDB(self.lang)
        labels = [labelDB.Tmax, labelDB.Tavg, labelDB.Tmin,
                  labelDB.rain, labelDB.snow]

        # --- plot legend --- #

        leg = ax.legend(lines, labels, numpoints=1, fontsize=13,
                        borderaxespad=0, loc='upper left', borderpad=0,
                        bbox_to_anchor=(0, 1), bbox_transform=transform)
        leg.draw_frame(False)

    # ========================================================= Plot data =====

    def plot_monthly_normals(self, normals):

        self.normals = normals

        # ------------------------------------------- assign local variables --

        Tmax_norm = normals['Tmax']
        Tmin_norm = normals['Tmin']
        Tavg_norm = normals['Tavg']
        Ptot_norm = normals['Ptot']
        Rain_norm = normals['Rain']
        Snow_norm = Ptot_norm - Rain_norm

        print('Tmax Yearly Avg. = %0.1f' % np.mean(Tmax_norm))
        print('Tmin Yearly Avg. = %0.1f' % np.mean(Tmin_norm))
        print('Tavg Yearly Avg. = %0.1f' % np.mean(Tavg_norm))
        print('Ptot Yearly Acg. = %0.1f' % np.sum(Ptot_norm))

        # ------------------------------------------------ DEFINE AXIS RANGE --

        if np.sum(Ptot_norm) < 500:
            Yscale0 = 10  # Precipitation (mm)
        else:
            Yscale0 = 20

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

        # ------------------------------------------------- YTICKS FORMATING --

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

        # --------------------------------------------------- SET AXIS RANGE --

        ax0.set_ylim(Ymin0, Ymax0)
        ax1.set_ylim(Ymin1, Ymax1)

        # ----------------------------------------------------------- LABELS --

        self.set_axes_labels()

        # --------------------------------------------------------- PLOTTING --

        self.plot_precip(Ptot_norm, Snow_norm)
        self.plot_air_temp(Tmax_norm, Tavg_norm, Tmin_norm)
        self.update_yearly_avg()

        # --------------------------------------------------------- Clipping --

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
        labelDB = LabelDB(self.lang)

        ax0 = self.figure.axes[1]
        ax0.set_ylabel(labelDB.Plabel, va='bottom', fontsize=16, rotation=270)
        ax0.yaxis.set_label_coords(1.09, 0.5)

        ax1 = self.figure.axes[2]
        ax1.set_ylabel(labelDB.Tlabel, va='bottom', fontsize=16)
        ax1.yaxis.set_label_coords(-0.09, 0.5)

    # =========================================================================

    def plot_precip(self, PNORM, SNORM):

        # ---- define vertices manually ----

        Xmid = np.arange(0.5, 12.5, 1)
        n = 0.5   # Controls the width of the bins
        f = 0.65  # Controls the spacing between the bins

        Xpos = np.vstack((Xmid - n * f,
                          Xmid - n * f,
                          Xmid + n * f,
                          Xmid + n * f)).transpose().flatten()

        Ptot = np.vstack((PNORM * 0,
                          PNORM,
                          PNORM,
                          PNORM * 0)).transpose().flatten()

        Snow = np.vstack((SNORM * 0,
                          SNORM,
                          SNORM,
                          SNORM * 0)).transpose().flatten()

        # -- plot data --

        ax = self.figure.axes[1]

        for collection in reversed(ax.collections):
            collection.remove()

        colors = ColorsReader()
        colors.load_colors_db()

        ax.fill_between(Xpos, 0., Ptot, edgecolor='none',
                        color=colors.rgb['Rain'])
        ax.fill_between(Xpos, 0., Snow, edgecolor='none',
                        color=colors.rgb['Snow'])

    # ---------------------------------------------------------------------

    def plot_air_temp(self, Tmax_norm, Tavg_norm, Tmin_norm):
        for i, Tnorm in enumerate([Tmax_norm, Tavg_norm, Tmin_norm]):
            T0 = (Tnorm[-1]+Tnorm[0])/2
            T = np.hstack((T0, Tnorm, T0))
            self.figure.axes[2].lines[i].set_ydata(T)
        self.figure.axes[2].lines[3].set_ydata(Tavg_norm)

    # =========================================================================

    def update_yearly_avg(self):

        Tavg_norm = self.normals['Tavg']
        Ptot_norm = self.normals['Ptot']

        ax = self.figure.axes[0]

        # ---- update position ----

        bbox = ax.texts[0].get_window_extent(self.get_renderer())
        bbox = bbox.transformed(ax.transAxes.inverted())

        ax.texts[1].set_position((0, bbox.y0))

        # ---- update labels ----

        labelDB = LabelDB(self.lang)

        ax.texts[0].set_text(labelDB.Tyrly % np.mean(Tavg_norm))
        ax.texts[1].set_text(labelDB.Pyrly % np.sum(Ptot_norm))


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class GridWeatherNormals(QTableWidget):

    def __init__(self, parent=None):
        super(GridWeatherNormals, self).__init__(parent)

        self.initUI()

    def initUI(self):

        self.setFrameStyle(StyleDB().frame)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
#        self.setMinimumWidth(650)

        # ------------------------------------------------------- Header --

        HEADER = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                  'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'YEAR')

        self.setColumnCount(len(HEADER))
        self.setHorizontalHeaderLabels(HEADER)

        self.setRowCount(7)
        self.setVerticalHeaderLabels(['Daily Tmax (°C)', 'Daily Tmin (°C)',
                                      'Daily Tavg (°C)', 'Rain (mm)',
                                      'Snow (mm)', 'Total Precip (mm)',
                                      'ETP (mm)'])

    def populate_table(self, NORMALS):

        # ---- Air Temperature ----

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

        # ---- Rain ----

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

        # ---- Snow ----

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

        # ---- Total Precip ----

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

        # ---- ETP ----

        row = 6
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

        self.resizeColumnsToContents()


# ---- if __name__ == '__main__'

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

    w = WeatherAvgGraph()
    w.save_fig_dir = os.getcwd()

    w.set_lang('English')
    w.generate_graph(wxdset)
    w.show()

    app.exec_()
