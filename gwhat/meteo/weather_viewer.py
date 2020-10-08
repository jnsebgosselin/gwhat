# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import io
import sys
import os
import os.path as osp
from datetime import datetime

# ---- Third party imports
import numpy as np
import matplotlib as mpl
from matplotlib.patches import Rectangle
from matplotlib.figure import Figure as MplFigure
from matplotlib.transforms import ScaledTranslation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import (
    QMenu, QToolButton, QGridLayout, QFileDialog, QApplication, QTableWidget,
    QTableWidgetItem, QLabel, QHBoxLayout, QHeaderView, QToolBar, QDialog)

# ---- Local library imports
from gwhat.config.ospath import (
    get_select_file_dialog_dir, set_select_file_dialog_dir)
from gwhat.utils import icons
from gwhat.config.gui import FRAME_SYLE
from gwhat.utils.icons import QToolButtonVRectSmall, QToolButtonNormal
from gwhat.widgets.buttons import RangeSpinBoxes
from gwhat.common.utils import save_content_to_file
from gwhat.meteo.weather_reader import WXDataFrameBase
from gwhat.widgets.buttons import ExportDataButton, LangToolButton

mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Arial']})


class WeatherViewer(QDialog):
    """
    GUI that allows to plot weather normals, save the graphs to file, see
    various stats about the dataset, etc...
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle('Weather Normals Viewer')
        self.setWindowIcon(icons.get_icon('master'))

        self.wxdset = None
        self.normals = None
        self.meteo_dir = os.getcwd()

        self.__initUI__()

    def __initUI__(self):

        # ---- Toolbar

        # Initialize the widgets :

        menu_save = QMenu()
        menu_save.addAction('Save normals graph as...', self.save_graph)
        menu_save.addAction('Save normals table as...', self.save_normals)

        btn_save = QToolButtonNormal('save')
        btn_save.setToolTip('Save normals')
        btn_save.setMenu(menu_save)
        btn_save.setPopupMode(QToolButton.InstantPopup)
        btn_save.setStyleSheet("QToolButton::menu-indicator {image: none;}")

        self.btn_copy = QToolButtonNormal('copy_clipboard')
        self.btn_copy.setToolTip('Copy figure to clipboard as image.')
        self.btn_copy.clicked.connect(self.copyfig_figure_to_clipboard)

        self.btn_export = ExportWeatherButton()
        self.btn_export.setIconSize(icons.get_iconsize('normal'))

        btn_showStats = QToolButtonNormal(icons.get_icon('showGrid'))
        btn_showStats.setToolTip(
            "Show the monthly weather normals data table.")
        btn_showStats.clicked.connect(self.show_monthly_grid)

        self.btn_language = LangToolButton()
        self.btn_language.setToolTip(
            "Set the language of the text shown in the graph.")
        self.btn_language.sig_lang_changed.connect(self.set_language)
        self.btn_language.setIconSize(icons.get_iconsize('normal'))

        # Instantiate and define a layout for the year range widget.

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

        # Setup the toolbar.
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("QToolBar {border: 0px; spacing:1px;}")
        buttons = [btn_save, self.btn_copy, self.btn_export, btn_showStats,
                   self.btn_language, None, self.year_rng]
        for button in buttons:
            if button is None:
                self.toolbar.addSeparator()
            else:
                self.toolbar.addWidget(button)

        # Setup the figure widget.
        self.fig_weather_normals = FigWeatherNormals()
        self.grid_weather_normals = GridWeatherNormals()
        self.grid_weather_normals.hide()

        # Setup the main layout.
        main_layout = QGridLayout(self)
        main_layout.addWidget(self.toolbar, 0, 0)
        main_layout.addWidget(self.fig_weather_normals, 1, 0)
        main_layout.addWidget(self.grid_weather_normals, 2, 0)
        main_layout.setRowStretch(2, 1)
        main_layout.setColumnStretch(0, 1)
        main_layout.setSizeConstraint(main_layout.SetFixedSize)

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

    def get_language(self):
        """Return the language used for the figure labels."""
        return self.btn_language.language

    def set_language(self, language):
        """Sets the language of all the labels in the figure."""
        if language.lower() != self.btn_language.language.lower():
            self.btn_language.set_language(language)
        else:
            self.fig_weather_normals.set_lang(language)
            self.fig_weather_normals.draw()

    def set_weather_dataset(self, wxdset):
        """
        Generate the graph, update the table, and update the GUI for
        the new weather dataset.
        """
        self.btn_export.set_model(wxdset)
        self.wxdset = wxdset

        # Update the GUI :
        self.setWindowTitle('Weather Averages for {}'.format(
                            wxdset.metadata['Station Name']))
        self.year_rng.setRange(*wxdset.get_data_period())
        self.update_normals()

    def expands_year_range(self):
        """Sets the maximal possible year range."""
        year_range = self.wxdset.get_data_period()
        self.year_rng.spb_lower.setValueSilently(min(year_range))
        self.year_rng.spb_upper.setValueSilently(max(year_range))
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
        period = (self.year_rng.lower_bound, self.year_rng.upper_bound)
        normals = {'data': self.wxdset.get_monthly_normals(period),
                   'period': period}
        return normals

    def copyfig_figure_to_clipboard(self):
        """Saves the current figure to the clipboard."""
        buf = io.BytesIO()
        self.fig_weather_normals.figure.savefig(buf, dpi=150)
        QApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
        buf.close()

    def save_graph(self):
        yrmin = self.year_rng.lower_bound
        yrmax = self.year_rng.upper_bound
        staname = self.wxdset.metadata['Station Name']

        defaultname = 'WeatherAverages_%s (%d-%d)' % (staname, yrmin, yrmax)
        ddir = os.path.join(get_select_file_dialog_dir(), defaultname)

        filename, ftype = QFileDialog.getSaveFileName(
            self, 'Save graph', ddir, '*.pdf;;*.svg')
        if filename:
            if not filename.endswith(ftype[1:]):
                filename += ftype[1:]
            set_select_file_dialog_dir(os.path.dirname(filename))
            self.fig_weather_normals.figure.savefig(filename)

    def save_normals(self):
        """
        Save the montly and yearly normals in a file.
        """
        # Define a default name for the file.
        defaultname = 'WeatherNormals_{} ({}-{})'.format(
            self.wxdset.metadata['Station Name'],
            self.year_rng.lower_bound,
            self.year_rng.upper_bound)
        ddir = osp.join(get_select_file_dialog_dir(), defaultname)

        # Open a dialog to get a save file name.
        filename, ftype = QFileDialog.getSaveFileName(
            self, 'Save normals', ddir, '*.xlsx;;*.xls;;*.csv')
        if filename:
            if not filename.endswith(ftype[1:]):
                filename += ftype[1:]
            set_select_file_dialog_dir(osp.dirname(filename))

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
                fcontent[-1].extend(self.normals['data'][vrb].tolist())
                if vrb in ['Tmin', 'Tavg', 'Tmax']:
                    fcontent[-1].append(self.normals['data'][vrb].mean())
                else:
                    fcontent[-1].append(self.normals['data'][vrb].sum())
            save_content_to_file(filename, fcontent)


class FigureLabels(object):

    LANGUAGES = ['english', 'french']

    def __init__(self, language):

        # Legend :

        self.Pyrly = 'Annual precipitation = %0.0f mm'
        self.Tyrly = 'Average annual temperature = %0.1f °C'
        self.rain = 'Rain'
        self.snow = 'Snow'
        self.Tmax = 'Maximum Temperature'
        self.Tmin = 'Minimum Temperature'
        self.Tavg = 'Average Temperature'

        # Labels :

        self.Tlabel = 'Temperature (°C)'
        self.Plabel = 'Precipitation (mm)'
        self.month_names = ["jan", "feb", "mar", "apr", "may", "jun",
                            "jul", "aug", "sep", "oct", "nov", "dec"]

        if language.lower() == 'french':

            # Legend :

            self.Pyrly = 'Précipitations annuelles = %0.0f mm'
            self.Tyrly = 'Température moyenne annuelle = %0.1f °C'
            self.rain = 'Pluie'
            self.snow = 'Neige'
            self.Tmax = 'Température maximale'
            self.Tmin = 'Température minimale'
            self.Tavg = 'Température moyenne'

            # Labels :

            self.Tlabel = 'Température (°C)'
            self.Plabel = 'Précipitations (mm)'
            self.month_names = ["jan", "fév", "mar", "avr", "mai", "jun",
                                "jul", "aoû", "sep", "oct", "nov", "déc"]


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
        self._dummy_ax = None

        fw, fh = 8.5, 5.
        fig = MplFigure(figsize=(fw, fh), facecolor='white')
        super(FigWeatherNormals, self).__init__(fig)

        # Define the margins.
        left_margin = 1 / fw
        right_margin = 1 / fw
        bottom_margin = 0.7 / fh
        top_margin = 20 / 72 / fh

        # Setup the axe to plot precipitation.
        x0 = left_margin
        y0 = bottom_margin
        axw = 1 - (left_margin + right_margin)
        axh = 1 - (bottom_margin + top_margin)
        # Setup the axe for precipitation.
        self._axe_precip = fig.add_axes(
            [x0, y0, axw, axh], zorder=1, label='precipitation')
        self._axe_precip.patch.set_visible(False)
        self._axe_precip.set_axisbelow(True)

        # Setup the axe to plot air temperature.
        self._axe_airtemp = fig.add_axes(
            self._axe_precip.get_position(), frameon=False, zorder=5,
            sharex=self._axe_precip, label='temperature')

        # Setup the air temperature and total precipitation
        # yearly average text artists.
        padding = ScaledTranslation(0/72, 3/72, fig.dpi_scale_trans)
        self._axe_precip.text(
            0, 1, 'Mean Annual Air Temperature', fontsize=10,
            va='bottom', ha='left',
            transform=self._axe_precip.transAxes + padding)
        self._axe_precip.text(
            1, 1, 'Mean Annual Precipitation', fontsize=10,
            va='bottom', ha='right',
            transform=self._axe_precip.transAxes + padding)

        # Initialize the Artists.

        # This is only to initiates the artists and to set their parameters
        # in advance. The plotting of the data is actually done by calling
        # the 'plot_monthly_normals' method.

        # Dashed lines for Tmax, Tavg, and Tmin.
        xpos = [0] + [0.5 + i for i in range(12)] + [12]
        colors = ['#990000', '#FF0000', '#FF6666']
        for i in range(3):
            self._axe_airtemp.plot(
                xpos, xpos, color=colors[i], ls='--', lw=1.5, zorder=100)

        # Markers for Tavg.
        self._axe_airtemp.plot(
            xpos[1:-1], xpos[1:-1], color=colors[1], marker='o', ls='none',
            ms=6, zorder=100, mec=colors[1], mfc='white', mew=1.5)

        # Setup major xticks.
        xpos_major = [0 + i for i in range(13)]
        self._axe_precip.xaxis.set_ticks_position('bottom')
        self._axe_precip.tick_params(axis='x', direction='out')
        self._axe_precip.xaxis.set_ticklabels([])
        self._axe_precip.set_xticks(xpos_major)
        self._axe_airtemp.tick_params(
            axis='x', which='both', bottom=False, top=False, labelbottom=False)
        self._axe_precip.set_xlim(0, 12)

        # Setup minor xticks.
        xpos_minor = [0.5 + i for i in range(12)]
        self._axe_precip.set_xticks(xpos_minor, minor=True)
        self._axe_precip.tick_params(
            axis='x', which='minor', direction='out', length=0, labelsize=13)
        self._axe_precip.xaxis.set_ticklabels(
            self.fig_labels.month_names, minor=True)

        # Format the yticks for the precipitation axis.
        self._axe_precip.yaxis.set_ticks_position('right')
        self._axe_precip.tick_params(axis='y', direction='out', labelsize=13)

        self._axe_precip.tick_params(axis='y', which='minor', direction='out')
        self._axe_precip.yaxis.set_ticklabels([], minor=True)

        # Format the yticks for the temperature axis.
        self._axe_airtemp.yaxis.set_ticks_position('left')
        self._axe_airtemp.tick_params(axis='y', direction='out', labelsize=13)

        self._axe_airtemp.tick_params(axis='y', which='minor', direction='out')
        self._axe_airtemp.yaxis.set_ticklabels([], minor=True)

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
        self._axe_precip.xaxis.set_ticklabels(
            self.fig_labels.month_names, minor=True)
        if self.normals is not None:
            self.set_axes_labels()
            self.update_yearly_avg()

    def plot_legend(self):
        """Plot the legend of the figure."""
        # Define the proxy artists.
        snow_rec = Rectangle((0, 0), 1, 1, fc='#a5a5a5', ec='none')
        rain_rec = Rectangle((0, 0), 1, 1, fc='#173458', ec='none')

        # Define the legend labels and markers.
        lines = [rain_rec, snow_rec, self._axe_airtemp.lines[0],
                 (self._axe_airtemp.lines[1], self._axe_airtemp.lines[3]),
                 self._axe_airtemp.lines[2]]
        labels = [self.fig_labels.rain, self.fig_labels.snow,
                  self.fig_labels.Tmax, self.fig_labels.Tavg,
                  self.fig_labels.Tmin]

        # Plot the legend.
        leg = self._axe_precip.legend(
            lines, labels, numpoints=1, fontsize=13, ncol=3,
            loc='upper left', mode='expand')
        leg.draw_frame(False)

    def plot_monthly_normals(self, normals, ygrid_are_aligned=False):
        """Plot the normals on the figure."""
        self.normals = normals

        legend = self._axe_precip.get_legend()
        legend_bbox = legend.get_window_extent(self.get_renderer())
        legend_bbox = legend_bbox.transformed(
            self._axe_precip.transAxes.inverted())

        # Assign local variables.
        Tmax_norm = normals['data']['Tmax'].values
        Tmin_norm = normals['data']['Tmin'].values
        Tavg_norm = normals['data']['Tavg'].values
        Ptot_norm = normals['data']['Ptot'].values
        Rain_norm = normals['data']['Rain'].values
        Snow_norm = Ptot_norm - Rain_norm

        # Define the range of the axis.
        precip_scale = 10 if np.sum(Ptot_norm) < 500 else 20
        airtemp_scale = 5

        SCA0 = np.arange(0, 10000, precip_scale)
        SCA1 = np.arange(-100, 100, airtemp_scale)

        # ---- Precipitation
        ptot_max_value = np.max(Ptot_norm) / (1 - legend_bbox.height)
        indx = np.where(SCA0 > ptot_max_value)[0][0]
        Ymax0 = SCA0[indx]
        Ymin0 = 0

        NZGrid0 = (Ymax0 - Ymin0) / precip_scale

        # ---- Temperature
        airtemp_max_value = np.max(Tmax_norm) / (1 - legend_bbox.height)
        indx = np.where(SCA1 > airtemp_max_value)[0][0]
        Ymax1 = SCA1[indx]

        indx = np.where(SCA1 < np.min(Tmin_norm))[0][-1]
        Ymin1 = SCA1[indx]

        NZGrid1 = (Ymax1 - Ymin1) / airtemp_scale

        # Align the vertical grid for the precipitation and air temperature.
        if ygrid_are_aligned:
            if NZGrid0 > NZGrid1:
                Ymin1 = Ymax1 - NZGrid0 * airtemp_scale
            elif NZGrid0 < NZGrid1:
                Ymax0 = Ymin0 + NZGrid1 * precip_scale
            elif NZGrid0 == NZGrid1:
                pass

        # In case there is a need to force the value.
        if False:
            Ymax0 = 100
            Ymax1 = 30
            Ymin1 = -20

        # Define the yticks for precipitation.
        yticks = np.arange(Ymin0, Ymax0 + precip_scale / 10, precip_scale)
        self._axe_precip.set_yticks(yticks)

        yticks_minor = np.arange(yticks[0], yticks[-1], 5)
        self._axe_precip.set_yticks(yticks_minor, minor=True)

        # Define the yticks for air temperature.
        yticks1 = np.arange(Ymin1, Ymax1 + airtemp_scale / 10, airtemp_scale)
        self._axe_airtemp.set_yticks(yticks1)

        yticks1_minor = np.arange(yticks1[0], yticks1[-1], airtemp_scale / 5)
        self._axe_airtemp.set_yticks(yticks1_minor, minor=True)

        # Set the range of the axis :

        self._axe_precip.set_ylim(Ymin0, Ymax0)
        self._axe_airtemp.set_ylim(Ymin1, Ymax1)

        # ---- LABELS

        self.set_axes_labels()
        self.set_year_range()

        # ---- PLOTTING

        self.plot_precip(Ptot_norm, Snow_norm)
        self.plot_air_temp(Tmax_norm, Tavg_norm, Tmin_norm)
        self.update_yearly_avg()

    def set_axes_labels(self):
        """Sets the labels of the y axis."""
        # Set the label fo the precipitation :
        self._axe_precip.set_ylabel(
            self.fig_labels.Plabel, va='bottom', fontsize=16, rotation=270)
        self._axe_precip.yaxis.set_label_coords(1.09, 0.5)

        # Set the label fo the air temperature :
        self._axe_airtemp.set_ylabel(
            self.fig_labels.Tlabel, va='bottom', fontsize=16)
        self._axe_airtemp.yaxis.set_label_coords(-0.09, 0.5)

    def set_year_range(self):
        """Sets the year range label that is displayed below the x axis."""
        if self.normals is not None:
            yearmin, yearmax = self.normals['period']
            if yearmin == yearmax:
                self._axe_precip.set_xlabel(
                    "%d" % yearmin, fontsize=16, labelpad=10)
            else:
                self._axe_precip.set_xlabel(
                    "%d - %d" % (yearmin, yearmax), fontsize=16, labelpad=10)

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

        # Plot the data.
        for collection in reversed(self._axe_precip.collections):
            collection.remove()
        self._axe_precip.fill_between(
            Xpos, 0, Ptot, edgecolor='none', color='#173458')
        self._axe_precip.fill_between(
            Xpos, 0, Snow, edgecolor='none', color='#a5a5a5')

    def plot_air_temp(self, Tmax_norm, Tavg_norm, Tmin_norm):
        for i, Tnorm in enumerate([Tmax_norm, Tavg_norm, Tmin_norm]):
            T0 = (Tnorm[-1] + Tnorm[0]) / 2
            T = np.hstack((T0, Tnorm, T0))
            self._axe_airtemp.lines[i].set_ydata(T)
        self._axe_airtemp.lines[3].set_ydata(Tavg_norm)

    def update_yearly_avg(self):
        Tavg_norm = self.normals['data']['Tavg'].values
        Ptot_norm = self.normals['data']['Ptot'].values
        ax = self._axe_precip

        # # Update the position of the labels.
        # bbox = ax.texts[0].get_window_extent(self.get_renderer())
        # bbox = bbox.transformed(ax.transAxes.inverted())
        # ax.texts[1].set_position((0, bbox.y0))

        # Update the text of the labels.
        ax.texts[0].set_text(self.fig_labels.Tyrly % np.mean(Tavg_norm))
        ax.texts[1].set_text(self.fig_labels.Pyrly % np.sum(Ptot_norm))


class GridWeatherNormals(QTableWidget):

    def __init__(self, parent=None):
        super(GridWeatherNormals, self).__init__(parent)

        self.initUI()

    def initUI(self):

        self.setFrameStyle(FRAME_SYLE)
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

    def populate_table(self, normals):

        # ---- Air Temperature
        for row, key in enumerate(['Tmax', 'Tmin', 'Tavg']):
            # Months
            for col in range(12):
                value = normals['data'][key].values[col]
                item = QTableWidgetItem('%0.1f' % value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(item.flags() & Qt.AlignCenter)
                self.setItem(row, col, item)

            # Year
            yearVal = np.mean(normals['data'][key])
            item = QTableWidgetItem('%0.1f' % yearVal)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 12, item)

        # ---- Rain
        row = 3
        # Months
        for col in range(12):
            value = normals['data']['Rain'].values[col]
            item = QTableWidgetItem('%0.1f' % value)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)

        # Year
        yearVal = np.sum(normals['data']['Rain'].values)
        item = QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- Snow
        row = 4
        # Months
        for col in range(12):
            value = normals['data']['Snow'].values[col]
            item = QTableWidgetItem('%0.1f' % value)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)

        # Year
        yearVal = np.sum(normals['data']['Snow'].values[col])
        item = QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- Total Precip
        row = 5
        # Months
        for col in range(12):
            value = normals['data']['Ptot'].values[col]
            item = QTableWidgetItem('%0.1f' % value)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)
        # Year
        yearVal = np.sum(normals['data']['Ptot'].values)
        item = QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- ETP
        row = 6
        # Months
        for col in range(12):
            value = normals['data']['PET'].values[col]
            item = QTableWidgetItem('%0.1f' % value)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, col, item)
        # Year
        yearVal = np.sum(normals['data']['PET'].values)
        item = QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 12, item)

    def calcul_height(self):
        h = self.horizontalHeader().height() + 2 * self.frameWidth()
        for i in range(self.rowCount()):
            h += self.rowHeight(i)
        return h


class ExportWeatherButton(ExportDataButton):
    """
    A toolbutton with a popup menu that handles the export of the weather
    dataset in various format.
    """
    MODEL_TYPE = WXDataFrameBase
    TOOLTIP = "Export weather data."

    def __init__(self, model=None, parent=None):
        super(ExportWeatherButton, self).__init__(model, parent)

    def setup_menu(self):
        """Setup the menu of the button tailored to the model."""
        super(ExportWeatherButton, self).setup_menu()
        self.menu().addAction('Export daily time series as...',
                              lambda: self.select_export_file('daily'))
        self.menu().addAction('Export monthly time series as...',
                              lambda: self.select_export_file('monthly'))
        self.menu().addAction('Export yearly time series as...',
                              lambda: self.select_export_file('yearly'))

    # ---- Export Time Series
    @QSlot(str)
    def select_export_file(self, time_frame, savefilename=None):
        """
        Prompt a dialog to select a file and save the weather data time series
        to a file in the specified format and time frame.
        """
        if savefilename is None:
            savefilename = osp.join(
                self.dialog_dir,
                'Weather{}_{}'.format(time_frame.capitalize(),
                                      self.model.metadata['Station Name'])
                )

        savefilename = self.select_savefilename(
            'Export {}'.format(time_frame),
            savefilename,
            '*.xlsx;;*.xls;;*.csv')

        if savefilename:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
            try:
                self.model.export_dataset_to_file(savefilename, time_frame)
            except PermissionError:
                self.show_permission_error()
                self.select_export_file(time_frame, savefilename)
            QApplication.restoreOverrideCursor()


if __name__ == '__main__':
    from gwhat.projet.reader_projet import ProjetReader
    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

    fname = ("C:\\Users\\User\\gwhat\\Projects\\Example\\Example.gwt")
    project = ProjetReader(fname)
    wxdset = project.get_wxdset('Marieville')

    w = WeatherViewer()

    w.set_language('French')
    w.set_weather_dataset(wxdset)
    w.show()

    app.exec_()
