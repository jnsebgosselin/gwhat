# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin
email: jnsebgosselin@gmail.com

This file is part of WHAT (Well Hydrograph Analysis Toolbox).

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# STANDARD LIBRARY IMPORTS :

# import csv
from time import sleep  # ctime, strftime, sleep
import os

# THIRD PARTY IMPORTS :

from PySide import QtGui, QtCore
import numpy as np
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT

# PERSONAL IMPORTS :

import meteo
from custom_widgets import MyQToolButton, QToolPanel
import custom_widgets as MyQWidget
import database as db
from gapfill_weather_algorithm2 import GapFillWeather


class GapFillWeatherGUI(QtGui.QWidget):

    ConsoleSignal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(GapFillWeatherGUI, self).__init__(parent)

        self.isFillAll_inProgress = False
        self.FILLPARAM = GapFill_Parameters()

        # Correlation calculation won't be triggered by events when
        # CORRFLAG is 'off'
        self.CORRFLAG = 'on'

        # Setup gap fill worker and thread :
        self.gap_fill_worker = GapFillWeather()
        self.gap_fill_thread = QtCore.QThread()
        self.gap_fill_worker.moveToThread(self.gap_fill_thread)
        self.set_workdir(os.getcwd())

        self.__initUI__()

    def __initUI__(self):

        # ---- Database ----

        #TODO: cleanup the language, tooltips and labels.

        styleDB = db.styleUI()
        iconDB = db.Icons()
        ttipDB = db.Tooltips('English')
        labelDB = db.labels('English')

        # ---- Main Window ----

        self.setWindowIcon(iconDB.WHAT)

        # ---- TOOLBAR ----

        self.btn_fill = QtGui.QPushButton(labelDB.btn_fill_weather)
        self.btn_fill.setIcon(iconDB.fill_data)
        self.btn_fill.setToolTip(ttipDB.btn_fill)
        self.btn_fill.setIconSize(styleDB.iconSize2)

        self.btn_fill_all = QtGui.QPushButton(labelDB.btn_fill_all_weather)
        self.btn_fill_all.setToolTip(ttipDB.btn_fill_all)
        self.btn_fill_all.setIcon(iconDB.fill_all_data)
        self.btn_fill_all.setIconSize(styleDB.iconSize2)

        grid_toolbar = QtGui.QGridLayout()
        widget_toolbar = QtGui.QFrame()

        row = 0
        col = 1
        grid_toolbar.addWidget(self.btn_fill, row, col)
        col += 1
        grid_toolbar.addWidget(self.btn_fill_all, row, col)

        grid_toolbar.setSpacing(5)
        grid_toolbar.setContentsMargins(0, 0, 0, 0)
        grid_toolbar.setColumnStretch(0, 100)
        grid_toolbar.setColumnStretch(col+1, 100)

        widget_toolbar.setLayout(grid_toolbar)

        # ---- LEFT PANEL ----

        # Target Station :

        target_station_label = QtGui.QLabel('<b>%s</b>' % labelDB.fill_station)
        self.target_station = QtGui.QComboBox()
        self.target_station_info = QtGui.QTextEdit()
        self.target_station_info.setReadOnly(True)
        self.target_station_info.setMaximumHeight(110)

        self.btn_refresh_staList = QtGui.QToolButton()
        self.btn_refresh_staList.setIcon(iconDB.refresh)
        self.btn_refresh_staList.setAutoRaise(True)
        self.btn_refresh_staList.setIconSize(styleDB.iconSize2)
        self.btn_refresh_staList.setToolTip(
            'Force the reloading of the weather data files')
        self.btn_refresh_staList.clicked.connect(self.load_data_dir_content)

        self.tarSta_widg = QtGui.QWidget()
        tarSta_grid = QtGui.QGridLayout()

        row = 0
        tarSta_grid.addWidget(target_station_label, row, 0, 1, 2)
        row = 1
        tarSta_grid.addWidget(self.target_station, row, 0)
        tarSta_grid.addWidget(self.btn_refresh_staList, row, 1)
        row = 2
        tarSta_grid.addWidget(self.target_station_info, row, 0, 1, 2)

        tarSta_grid.setSpacing(5)
        tarSta_grid.setColumnStretch(0, 500)
        tarSta_grid.setContentsMargins(0, 0, 0, 10)  # (L,T,R,B)
        self.tarSta_widg.setLayout(tarSta_grid)

        # Gapfill Dates :

        label_From = QtGui.QLabel('From :  ')
        self.date_start_widget = QtGui.QDateEdit()
        self.date_start_widget.setDisplayFormat('dd / MM / yyyy')
        self.date_start_widget.setEnabled(False)
        label_To = QtGui.QLabel('To :  ')
        self.date_end_widget = QtGui.QDateEdit()
        self.date_end_widget.setEnabled(False)
        self.date_end_widget.setDisplayFormat('dd / MM / yyyy')

        self.fillDates_widg = QtGui.QWidget()
        fillDates_grid = QtGui.QGridLayout()

        row = 0
        col = 0
        fillDates_grid.addWidget(label_From, row, col)
        col += 1
        fillDates_grid.addWidget(self.date_start_widget, row, col)
        row += 1
        col = 0
        fillDates_grid.addWidget(label_To, row, col)
        col += 1
        fillDates_grid.addWidget(self.date_end_widget, row, col)

        fillDates_grid.setColumnStretch(row+1, 500)
        fillDates_grid.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        fillDates_grid.setSpacing(10)

        self.fillDates_widg.setLayout(fillDates_grid)

        def station_sel_criteria(self):
            labelDB = db.labels('English')

            # Widgets :

            Nmax_label = QtGui.QLabel(labelDB.NbrSta)
            self.Nmax = QtGui.QSpinBox()
            self.Nmax.setRange(0, 99)
            self.Nmax.setSingleStep(1)
            self.Nmax.setValue(4)
            self.Nmax.setAlignment(QtCore.Qt.AlignCenter)

            distlimit_label = QtGui.QLabel(labelDB.distlimit)
            distlimit_label.setToolTip(ttipDB.distlimit)
            self.distlimit = QtGui.QSpinBox()
            self.distlimit.setRange(-1, 9999)
            self.distlimit.setSingleStep(1)
            self.distlimit.setValue(100)
            self.distlimit.setToolTip(ttipDB.distlimit)
            self.distlimit.setSuffix(' km')
            self.distlimit.setAlignment(QtCore.Qt.AlignCenter)

            altlimit_label = QtGui.QLabel(labelDB.altlimit)
            altlimit_label.setToolTip(ttipDB.altlimit)
            self.altlimit = QtGui.QSpinBox()
            self.altlimit.setRange(-1, 9999)
            self.altlimit.setSingleStep(1)
            self.altlimit.setValue(350)
            self.altlimit.setToolTip(ttipDB.altlimit)
            self.altlimit.setSuffix(' m')
            self.altlimit.setAlignment(QtCore.Qt.AlignCenter)

            # Layout :

            container = QtGui.QFrame()
            grid = QtGui.QGridLayout()

            row = 0
            grid.addWidget(self.Nmax, row, 1)
            grid.addWidget(Nmax_label, row, 0)
            row += 1
            grid.addWidget(distlimit_label, row, 0)
            grid.addWidget(self.distlimit, row, 1)
            row += 1
            grid.addWidget(altlimit_label, row, 0)
            grid.addWidget(self.altlimit, row, 1)

            grid.setContentsMargins(10, 0, 10, 0) # [L, T, R, B]
            grid.setColumnStretch(2, 500)
            grid.setSpacing(10)
            container.setLayout(grid)

            return container

        def regression_model(self):

            # ---- Widgets ----

            self.RMSE_regression = QtGui.QRadioButton('Ordinary Least Squares')
            self.RMSE_regression.setChecked(True)
            self.ABS_regression = QtGui.QRadioButton(
                                      'Least Absolute Deviations')

            # ---- Layout ----

            container = QtGui.QFrame()
            grid = QtGui.QGridLayout()

            row = 0
            grid.addWidget(self.RMSE_regression, row, 0)
            row += 1
            grid.addWidget(self.ABS_regression, row, 0)

            grid.setSpacing(5)
            grid.setContentsMargins(10, 0, 10, 0)  # (L, T, R, B)
            container.setLayout(grid)

            return container

        def advanced_settings(self):

            chckstate = QtCore.Qt.CheckState.Unchecked

            # ---- Row Full Error ----

            self.full_error_analysis = QtGui.QCheckBox('Full Error Analysis')
            self.full_error_analysis.setCheckState(chckstate)

            # ---- Row ETP ----

            self.add_ETP_ckckbox = QtGui.QCheckBox('Add ETP to data file')
            self.add_ETP_ckckbox.setCheckState(chckstate)

            btn_add_ETP = MyQToolButton(db.Icons().openFile,
                                        'Add ETP to data file',
                                        db.styleUI().iconSize2)
            btn_add_ETP.clicked.connect(self.btn_add_ETP_isClicked)

            # ---- Row Layout Assembly ----

            container = QtGui.QFrame()
            grid = QtGui.QGridLayout()

            row = 0
            grid.addWidget(self.full_error_analysis, row, 0)
            row += 1
            grid.addWidget(self.add_ETP_ckckbox, row, 0)
            grid.addWidget(btn_add_ETP, row, 2)

            grid.setSpacing(5)
            grid.setContentsMargins(10, 0, 10, 0)  # [L, T, R, B]
            grid.setRowStretch(row+1, 100)
            grid.setColumnStretch(1, 100)
            container.setLayout(grid)

            return container

        # STACKED WIDGET :

        cutoff_widg = station_sel_criteria(self)
        MLRM_widg = regression_model(self)
        advanced_widg = advanced_settings(self)

        self.stack_widget = QToolPanel()
        self.stack_widget.setIcons(QtGui.QIcon('Icons/triangle_right.png'),
                                   QtGui.QIcon('Icons/triangle_down.png'))
        self.stack_widget.addItem(cutoff_widg, 'Stations Selection Criteria :')
        self.stack_widget.addItem(MLRM_widg, 'Regression Model :')
        self.stack_widget.addItem(advanced_widg, 'Advanced Settings :')

        # SUBGRIDS ASSEMBLY :

        grid_leftPanel = QtGui.QGridLayout()
        self.LEFT_widget = QtGui.QFrame()
        self.LEFT_widget.setFrameStyle(0)  # styleDB.frame

        seprator1 = QtGui.QFrame()
        seprator1.setFrameStyle(styleDB.HLine)
        seprator2 = QtGui.QFrame()
        seprator2.setFrameStyle(styleDB.HLine)
        seprator3 = QtGui.QFrame()
        seprator3.setFrameStyle(styleDB.HLine)

        row = 0
        grid_leftPanel.addWidget(self.tarSta_widg, row, 0)
        row += 1
        grid_leftPanel.addWidget(self.fillDates_widg, row, 0)
        row += 1
        grid_leftPanel.addWidget(seprator1, row, 0)
        row += 1
        grid_leftPanel.addWidget(self.stack_widget, row, 0)
        row += 2
        grid_leftPanel.addWidget(seprator2, row, 0)
        row += 1
        grid_leftPanel.addWidget(widget_toolbar, row, 0)

        grid_leftPanel.setVerticalSpacing(15)
        grid_leftPanel.setRowStretch(row-2, 500)
        grid_leftPanel.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
#        grid_leftPanel.setColumnMinimumWidth(0, styleDB.sideBarWidth)

        self.LEFT_widget.setLayout(grid_leftPanel)

        # ---- Right Panel ----

        self.FillTextBox = QtGui.QTextEdit()
        self.FillTextBox.setReadOnly(True)
#        self.FillTextBox.setFrameStyle(styleDB.frame)
        self.FillTextBox.setMinimumWidth(700)
#        self.FillTextBox.setStyleSheet(
#                                  "QTextEdit {background-color:transparent;}")
        self.FillTextBox.setFrameStyle(0)
        self.FillTextBox.document().setDocumentMargin(10)

        self.sta_display_summary = QtGui.QTextEdit()
        self.sta_display_summary.setReadOnly(True)
#        self.sta_display_summary.setStyleSheet(
#                                  "QTextEdit {background-color:transparent;}")
        self.sta_display_summary.setFrameStyle(0)
        self.sta_display_summary.document().setDocumentMargin(10)

        self.gafill_display_table = GapFillDisplayTable()

#        grid_rightPanel = QtGui.QGridLayout()
#        new_table = QtGui.QFrame()
#        new_table.setFrameStyle(0)

#        row = 0
#        grid_rightPanel.addWidget(self.gafill_display_table2 , row, 0)
#        row += 1
#        grid_rightPanel.addWidget(self.gafill_display_table , row, 0)
#
#        grid_rightPanel.setRowStretch(row, 500)
##        grid_rightPanel.setColumnStretch(0, 500)
#        grid_rightPanel.setSpacing(0)
#        grid_rightPanel.setContentsMargins(0, 0, 0, 0) #(L, T, R, B)
#
#        new_table.setLayout(grid_rightPanel)

        RIGHT_widget = QtGui.QTabWidget()
        RIGHT_widget.addTab(self.FillTextBox, 'Correlation Coefficients')
        RIGHT_widget.addTab(self.sta_display_summary, 'Missing Data Overview')
#        RIGHT_widget.addTab(self.gafill_display_table,
#                            'New Table (Work-in-Progress)')

        # ---- Main grid ----

        grid_MAIN = QtGui.QGridLayout()

        row = 0
        grid_MAIN.addWidget(self.LEFT_widget, row, 0)
        grid_MAIN.addWidget(RIGHT_widget, row, 1)

        grid_MAIN.setColumnStretch(1, 500)
        grid_MAIN.setRowStretch(0, 500)
        grid_MAIN.setSpacing(15)
        grid_MAIN.setContentsMargins(15, 15, 15, 15)  # L, T, R, B

        self.setLayout(grid_MAIN)

        # ---- Progress Bar ----

        self.pbar = QtGui.QProgressBar()
        self.pbar.setValue(0)
        self.pbar.hide()

        # ---- Events ----

        # CORRELATION :

        self.target_station.currentIndexChanged.connect(self.correlation_UI)
        self.distlimit.valueChanged.connect(self.correlation_table_display)
        self.altlimit.valueChanged.connect(self.correlation_table_display)
        self.date_start_widget.dateChanged.connect(
                                                self.correlation_table_display)
        self.date_end_widget.dateChanged.connect(
                                                self.correlation_table_display)

        # GAPFILL :

        self.gap_fill_worker.ProgBarSignal.connect(self.pbar.setValue)
        self.gap_fill_worker.GapFillFinished.connect(
                                                   self.gap_fill_worker_return)
        self.gap_fill_worker.ConsoleSignal.connect(self.ConsoleSignal.emit)

        self.btn_fill.clicked.connect(self.gap_fill_btn_clicked)
        self.btn_fill_all.clicked.connect(self.gap_fill_btn_clicked)

        # ---------------------------------------------------- MESSAGE BOX ----

        self.msgBox = MyQWidget.MyQErrorMessageBox()

    # =========================================================================

    @property
    def workdir(self):
        return self.__workdir

    def set_workdir(self, dirname):
        self.__workdir = dirname
        self.gap_fill_worker.inputDir = os.path.join(dirname, 'Meteo', 'Input')
        self.gap_fill_worker.outputDir = os.path.join(
                                             dirname, 'Meteo', 'Output')

    # =========================================================================

    def load_data_dir_content(self):
        '''
        Initiate the loading of Weater Data Files contained in the
        */Meteo/Input* folder and display the resulting station list in the
        *Target station* combo box widget.
        '''

        # Reset UI :

        self.FillTextBox.setText('')
        self.target_station_info.setText('')
        self.target_station.clear()
        QtGui.QApplication.processEvents()

        # Load data and fill UI with info :

        self.CORRFLAG = 'off'
        # Correlation calculation won't be triggered when this is off

        if self.sender() == self.btn_refresh_staList:
            stanames = self.gap_fill_worker.reload_data()
        else:
            stanames = self.gap_fill_worker.load_data()
        self.target_station.addItems(stanames)
        self.target_station.setCurrentIndex(-1)
        self.sta_display_summary.setHtml(self.gap_fill_worker.read_summary())

        if len(stanames) > 0:
            self.set_fill_and_save_dates()

        self.CORRFLAG = 'on'

    def set_fill_and_save_dates(self):  # =====================================
        """
        Set first and last dates of the data serie in the boxes of the
        *Fill and Save* area.
        """

        if len(self.gap_fill_worker.WEATHER.DATE) > 0:

            self.date_start_widget.setEnabled(True)
            self.date_end_widget.setEnabled(True)

            DATE = self.gap_fill_worker.WEATHER.DATE

            DateMin = QtCore.QDate(DATE[0, 0], DATE[0, 1], DATE[0, 2])
            DateMax = QtCore.QDate(DATE[-1, 0], DATE[-1, 1], DATE[-1, 2])

            self.date_start_widget.setDate(DateMin)
            self.date_start_widget.setMinimumDate(DateMin)
            self.date_start_widget.setMaximumDate(DateMax)

            self.date_end_widget.setDate(DateMax)
            self.date_end_widget.setMinimumDate(DateMin)
            self.date_end_widget.setMaximumDate(DateMax)

    def correlation_table_display(self):  # ===================================

        """
        This method plot the table in the display area. It is separated from
        the method <Correlation_UI> because red numbers and statistics
        regarding missing data for the selected time period can be updated in
        the table when the user changes the values without having to
        recalculate the correlation coefficient each time.
        """

        if self.CORRFLAG == 'on' and self.target_station.currentIndex() != -1:

            self.FILLPARAM.limitDist = self.distlimit.value()
            self.FILLPARAM.limitAlt = self.altlimit.value()

            y = self.date_start_widget.date().year()
            m = self.date_start_widget.date().month()
            d = self.date_start_widget.date().day()
            self.FILLPARAM.time_start = xldate_from_date_tuple((y, m, d), 0)

            y = self.date_end_widget.date().year()
            m = self.date_end_widget.date().month()
            d = self.date_end_widget.date().day()
            self.FILLPARAM.time_end = xldate_from_date_tuple((y, m, d), 0)

            self.gafill_display_table.populate_table(
                self.gap_fill_worker.TARGET,
                self.gap_fill_worker.WEATHER,
                self.FILLPARAM)

            table, target_info = correlation_table_generation(
                self.gap_fill_worker.TARGET,
                self.gap_fill_worker.WEATHER,
                self.FILLPARAM)

            self.FillTextBox.setText(table)
            self.target_station_info.setText(target_info)


    def correlation_UI(self): #================================================

        """
        Calculate automatically the correlation coefficients when a target
        station is selected by the user in the drop-down menu or if a new
        station is selected programmatically.
        """

        if self.CORRFLAG == 'on' and self.target_station.currentIndex() != -1:

            index = self.target_station.currentIndex()
            self.gap_fill_worker.set_target_station(index)

            msg = ('Correlation coefficients calculation for ' +
                   'station %s completed') % self.gap_fill_worker.TARGET.name
            self.ConsoleSignal.emit('<font color=black>%s</font>' % msg )
            print(msg)

            self.correlation_table_display()


    def restoreUI(self): #=====================================================

        iconDB = db.Icons()

        self.btn_fill.setIcon(iconDB.fill_data)
        self.btn_fill.setEnabled(True)

        self.btn_fill_all.setIcon(iconDB.fill_all_data)
        self.btn_fill_all.setEnabled(True)

        self.tarSta_widg.setEnabled(True)
        self.fillDates_widg.setEnabled(True)
        self.stack_widget.setEnabled(True)

        self.pbar.setValue(0)

        QtGui.QApplication.processEvents()

        self.pbar.hide()

    def get_time_from_qdatedit(self, obj):

        y = obj.date().year()
        m = obj.date().month()
        d = obj.date().day()

        return xldate_from_date_tuple((y, m, d), 0)


    def gap_fill_btn_clicked(self): #=============== Gap-Fill Button Clicked ==

        #-------------------------------------------- Stop Thread if Running --

        if self.gap_fill_thread.isRunning():

            print('!Stopping the gap-filling routine!')

            #-- Pass a flag to the worker to tell him to stop --

            self.gap_fill_worker.STOP = True
            self.isFillAll_inProgress = False
            # UI will be restored in *gap_fill_worker_return* method

            return

        #----------------------------------------------------- Data is Empty --

        #-- Check if Station List is Empty --

        nSTA = len(self.gap_fill_worker.WEATHER.STANAME)
        if nSTA == 0:
            self.msgBox.setText('There is no data to fill.')
            self.msgBox.exec_()
            print('There is no data to fill.')

            return

        #-------------------------------------------- CHECK FOR DATES ERRORS --

        time_start = self.get_time_from_qdatedit(self.date_start_widget)
        time_end = self.get_time_from_qdatedit(self.date_end_widget)

        if time_start > time_end:

            print('The time period is invalid.')
            self.msgBox.setText('<b>Gap Fill Data Record</b> start date is ' +
                                'set to a later time than the end date.')
            self.msgBox.exec_()

            return

        #------------------------------------------------ Check Which Button --

        button = self.sender()
        if button == self.btn_fill: #---------------------- Fill One Station --

            #-- Check if Station is Selected --

            if self.target_station.currentIndex() == -1:
                self.msgBox.setText('No <b>weather station</b> is currently ' +
                                    'selected.')
                self.msgBox.exec_()
                print('No weather station is currently selected.')

                return

            self.btn_fill_all.setEnabled(False)
            self.isFillAll_inProgress = False
            sta_indx2fill = self.target_station.currentIndex()

        elif button == self.btn_fill_all: #--------------- Fill All Stations --

            self.btn_fill.setEnabled(False)
            self.isFillAll_inProgress = True
            sta_indx2fill = 0

        # -- Disable UI and continue the process normally --

        button.setIcon(db.Icons().stop)
        self.fillDates_widg.setEnabled(False)
        self.tarSta_widg.setEnabled(False)
        self.stack_widget.setEnabled(False)
        self.pbar.show()

        QtGui.QApplication.processEvents()

        self.gap_fill_start(sta_indx2fill)


    def gap_fill_worker_return(self, event): #============== Gap-Fill Return ==

        # Method initiated from an automatic return from the gapfilling
        # process in batch mode. Iterate over the station list and continue
        # process normally.

        self.gap_fill_thread.quit()

        nSTA = len(self.gap_fill_worker.WEATHER.STANAME)
        if event == True:
            sta_indx2fill = self.target_station.currentIndex() + 1
            if self.isFillAll_inProgress == False or sta_indx2fill == nSTA:

                # Single fill process completed sucessfully for the current
                # selected weather station OR Fill All process completed
                # sucessfully for all the weather stations in the list.

                self.restoreUI()
            else:
                self.gap_fill_start(sta_indx2fill)

        elif event == False:
            print('Gap-filling routine stopped... restoring UI.')
            self.gap_fill_worker.STOP = False
            self.isFillAll_inProgress = False
            self.restoreUI()


    def gap_fill_start(self, sta_indx2fill): #=============== Gap-Fill Start ==

        #----- Wait for the QThread to finish -----

        # Protection in case the QTread did not had time to close completely
        # before starting the downloading process for the next station.

        waittime = 0
        while self.gap_fill_thread.isRunning():
            print('Waiting for the fill weather data thread to close ' +
                  'before processing with the next station.')
            sleep(1)
            waittime += 1
            if waittime > 15:
                msg = ('This function is not working as intended.' +
                       ' Please report a bug.')
                print(msg)
                self.ConsoleSignal.emit('<font color=red>%s</font>' % msg)
                return

        # -------------------------------------------------------- UPDATE UI --

        self.CORRFLAG = 'off'
        self.target_station.setCurrentIndex(sta_indx2fill)
#        self.TARGET.index = self.target_station.currentIndex()
#        self.TARGET.name = \
#            self.gap_fill_worker.WEATHER.STANAME[self.TARGET.index]
        self.CORRFLAG = 'on'

        # Calculate correlation coefficient for the next station.
        self.correlation_UI()

        # ----------------------------------------------------- START THREAD --

        # -- Pass information to the worker --

        self.gap_fill_worker.outputDir = self.workdir + '/Meteo/Output'

        time_start = self.get_time_from_qdatedit(self.date_start_widget)
        time_end = self.get_time_from_qdatedit(self.date_end_widget)
        self.gap_fill_worker.time_start = time_start
        self.gap_fill_worker.time_end = time_end

        self.gap_fill_worker.NSTAmax = self.Nmax.value()
        self.gap_fill_worker.limitDist = self.distlimit.value()
        self.gap_fill_worker.limitAlt = self.altlimit.value()

#        self.gap_fill_worker.TARGET = self.TARGET

        self.gap_fill_worker.regression_mode = self.RMSE_regression.isChecked()

        self.gap_fill_worker.full_error_analysis = \
            self.full_error_analysis.isChecked()
        self.gap_fill_worker.add_ETP = self.add_ETP_ckckbox.isChecked()

        # ---- Start the Thread ----

        self.gap_fill_thread.start()
        self.gap_fill_worker.FillDataSignal.emit(True)

    def btn_add_ETP_isClicked(self):  # =======================================

        dirname = self.workdir + '/Meteo/Output'
        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                  self, 'Select a valid water level data file',
                                  dirname, '*.out')

        if filename:
            meteo.add_ETP_to_weather_data_file(filename)


# =============================================================================


class StaLocManager(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(StaLocManager, self).__init__(*args, **kwargs)

        self.figure = mpl.figure.Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(toolbar, 0, 0)
        layout.addWidget(self.canvas, 1, 0)

        self.__init_plot__()

    def __init_plot__(self):
        self.figure.set_facecolor('white')
        self.figure.add_subplot(111)

    def plot_stations(self, lat, lon, name):
        ax = self.figure.axes[0]
        ax.plot(lon, lat, 'o')
        for i in range(len(name)):
            ax.annotate(name[i], xy=(lon[i], lat[i]), textcoords='data')

    def plot_obswells(self, lat, lon, name):
        ax = self.figure.axes[0]
        ax.plot(lon, lat, 'o', color='red')
        ax.annotate(name, xy=(lon, lat), textcoords='data')


# =============================================================================


def correlation_table_generation(TARGET, WEATHER, FILLPARAM):
    """
    This fucntion generate an HTML output to be displayed in the
    <Fill Data> tab display area after a target station has been
    selected by the user.
    """

    styleDB = db.styleUI()

    STANAME = WEATHER.STANAME

    nSTA = len(STANAME)
    nVAR = len(WEATHER.VARNAME)
    Ndata_limit = int(365 / 2.)

    limitDist = FILLPARAM.limitDist
    limitAlt = FILLPARAM.limitAlt

    # -------------------------------------------- TARGET STATION INFO TABLE --

    date_start = xldate_as_tuple(FILLPARAM.time_start, 0)
    date_start = '%02d/%02d/%04d' % (WEATHER.DATE_START[TARGET.index, 2],
                                     WEATHER.DATE_START[TARGET.index, 1],
                                     WEATHER.DATE_START[TARGET.index, 0])

    date_end = xldate_as_tuple(FILLPARAM.time_end, 0)
    date_end = '%02d/%02d/%04d' % (WEATHER.DATE_END[TARGET.index, 2],
                                   WEATHER.DATE_END[TARGET.index, 1],
                                   WEATHER.DATE_END[TARGET.index, 0])

    FIELDS = ['Latitude', 'Longitude', 'Altitude', 'Data date start',
              'Data date end']

    HEADER = [WEATHER.LAT[TARGET.index],
              WEATHER.LON[TARGET.index],
              WEATHER.ALT[TARGET.index],
              date_start,
              date_end]

    target_info = '''<table border="0" cellpadding="1" cellspacing="0"
                     align="left">'''

    for i in range(len(HEADER)):
        target_info += '<tr>' # + <td width=10></td>'
        target_info +=   '<td align="left">%s</td>' % FIELDS[i]
        target_info +=   '<td align="left">&nbsp;:&nbsp;</td>'
        target_info +=   '<td align="left">%s</td>' % HEADER[i]
        target_info += '</tr>'

    target_info += '</table>'

    # -------------------------------------------------------- SORT STATIONS --

    # Stations best correlated with the target station are displayed toward
    # the top of the table while neighboring stations poorly correlated are
    # displayed toward the bottom.

    # Define a criteria for sorting the correlation quality of the stations.
    CORCOEF = TARGET.CORCOEF
    DATA = WEATHER.DATA
    TIME = WEATHER.TIME

    SUM_CORCOEF = np.sum(CORCOEF, axis=0) * -1  # Sort in descending order.
    index_sort = np.argsort(SUM_CORCOEF)

    # Reorganize the data.
    CORCOEF = CORCOEF[:, index_sort]
    DATA = DATA[:, index_sort, :]
    STANAME = STANAME[index_sort]

    HORDIST = TARGET.HORDIST[index_sort]
    ALTDIFF = TARGET.ALTDIFF[index_sort]
    target_station_index = np.where(TARGET.name == STANAME)[0]

    index_start = np.where(TIME == FILLPARAM.time_start)[0][0]
    index_end = np.where(TIME == FILLPARAM.time_end)[0][0]

    # ---------------------------------------------- Determine filling dates --

    fill_date_start = xldate_as_tuple(FILLPARAM.time_start, 0)
    fill_date_start = '%02d/%02d/%04d' % (fill_date_start[2],
                                          fill_date_start[1],
                                          fill_date_start[0])

    fill_date_end = xldate_as_tuple(FILLPARAM.time_end, 0)
    fill_date_end = '%02d/%02d/%04d' % (fill_date_end[2],
                                        fill_date_end[1],
                                        fill_date_end[0])

    # --------------------------------------------------- missing data table --

    table1 = '''
             <p align=justify>
               Table 1 : Number of days with missing data from
               <b>%s</b> to <b>%s</b> for station <b>%s</b>:
             </p>
             ''' % (fill_date_start, fill_date_end, TARGET.name)
    table1 += '''
              <table border="0" cellpadding="3" cellspacing="0"
                     align="center">
                <tr>
                  <td colspan="5"><hr></td>
                </tr>
                <tr>
              '''

    table1 +=  '''
               <td width=135 align="left">Weather Variable</td>
               <td align="center">T<sub>max</sub></td>
               <td align="center">T<sub>min</sub></sub></td>
               <td align="center">T<sub>mean</sub></td>
               <td align="center">P<sub>tot</sub></td>
               '''


    table1 +=  '''
               </tr>
               <tr>
                 <td colspan="5"><hr></td>
               </tr>
               <tr>
                 <td width=135 align="left">Days with<br>missing data</td>
               '''

    total_nbr_data = index_end - index_start + 1
    for var in range(nVAR):
        nbr_nan = np.isnan(
                       DATA[index_start:index_end+1, target_station_index, var])
        nbr_nan = float(np.sum(nbr_nan))

        nan_percent = round(nbr_nan / total_nbr_data * 100, 1)

        table1 += '''<td align="center">
                      %d<br>(%0.1f %%)
                     </td>''' % (nbr_nan, nan_percent)

    table1 +=  '''
                 </tr>
                 <tr>
                   <td colspan="5"><hr></td>
                 </tr>
               </table>
               <br><br>'''

    #---------------------------------------------------- corr. coeff. table --
    table2 = table1
    table2 += '''
              <p align="justify">
                <font size="3">
                  Table 2 : Altitude difference, horizontal distance and
                  correlation coefficients for each meteorological variables,
                  calculated between station <b>%s</b> and its neighboring
                  stations :
                <\font>
              </p>
              ''' % TARGET.name

    #---- HEADER ----

    table2 += '''
              <table border="0" cellpadding="3" cellspacing="0"
                     align="center" width="100%%">
                <tr>
                  <td colspan="9"><hr></td>
                </tr>
                <tr>
                  <td align="center" valign="bottom" width=30 rowspan="3">
                    #
                  </td>
                  <td align="left" valign="bottom" width=200 rowspan="3">
                    Neighboring Stations
                  </td>
                  <td width=60 align="center" valign="bottom" rowspan="3">
                    &#916;Alt.<br>(m)
                  </td>
                  <td width=60 align="center" valign="bottom" rowspan="3">
                    Dist.<br>(km)
                  </td>
                  <td align="center" valign="middle" colspan="4">
                    Correlation Coefficients
                  </td>
                </tr>
                <tr>
                  <td colspan="4"><hr></td>
                </tr>
                <tr>
                  <td width=60 align="center" valign="middle">
                    T<sub>max</sub>
                  </td>
                  <td width=60 align="center" valign="middle">
                    T<sub>min</sub>
                  </td>
                  <td width=60 align="center" valign="middle">
                    T<sub>mean</sub>
                  </td>
                  <td width=60 align="center" valign="middle">
                    P<sub>tot</sub>
                  </td>
                </tr>
                <tr>
                  <td colspan="9"><hr></td>
                </tr>
              '''

    color = ['transparent', styleDB.lightgray]
    index = list(range(nSTA))
    index.remove(target_station_index)
    counter = 0
    for i in index:

        #---- Counter and Neighboring station names ----

        table2 += '''
                   <tr bgcolor="%s">
                     <td align="center" valign="top">%02d</td>
                     <td valign="top">
                       %s
                     </td>
                  ''' % (color[counter%2], counter+1, STANAME[i])

        #---- Altitude diff. ----

        if abs(ALTDIFF[i]) >= limitAlt and limitAlt >= 0:
            fontcolor = styleDB.red
        else:
            fontcolor = ''

        table2 += '''
                     <td align="center" valign="top">
                       <font color="%s">%0.1f</font>
                     </td>
                  ''' % (fontcolor, ALTDIFF[i])

        #---- Horiz. distance ----

        if HORDIST[i] >= limitDist and limitDist >= 0:
            fontcolor = styleDB.red
        else :
            fontcolor = ''

        table2 += '''
                     <td align="center" valign="top">
                       <font color="%s">%0.1f</font>
                     </td>
                  ''' % (fontcolor, HORDIST[i])

        #---- correlation coefficients ----

        for value in CORCOEF[:, i]:
            if value > 0.7:
                fontcolor = ''
            else:
                fontcolor = styleDB.red

            table2 += '''
                      <td align="center" valign="top">
                        <font color="%s">%0.3f</font>
                      </td>
                      ''' % (fontcolor, value)
        table2 += '</tr>'
        counter += 1

    table2 += '''  <tr>
                     <td colspan="8"><hr></td>
                   </tr>
                   <tr>
                     <td align="justify" colspan="8">
                     <font size="2">
                       * Correlation coefficients are set to
                       <font color="#C83737">NaN</font> for a given
                       variable if there is less than
                       <font color="#C83737">%d</font> pairs of data
                       between the target and the neighboring station.
                       </font>
                     </td>
                   </tr>
                 </table>
                 ''' % (Ndata_limit)

    return table2, target_info


# =============================================================================


class GapFill_Parameters():
    # Class that contains all the relevant parameters for the gapfilling
    # procedure. Main instance of this class in the code is <FILLPARAM>.

   def __init__(self):

        self.time_start = 0  # Fill and Save start date.
        self.time_end = 0    # Fill and Save end date.
        self.index_start = 0 # Time index for start date
        self.index_end = 0   # Time index for end date

        self.regression_mode = True

        self.NSTAmax = 0 # Max number of neighboring station to use in the
                         # regression model.
        self.limitDist = 0 # Cutoff limit for the horizontal distance between
                           # the target and the neighboring stations.
        self.limitAlt = 0 # Cutoff limit for the altitude difference between
                          # the target and the neighboring stations.


# =============================================================================


class GapFillDisplayTable(QtGui.QTableWidget):
    """
    Widget for displaying usefull information for the gapfilling of daily
    datasets.
    """

    def __init__(self, parent=None):
        super(GapFillDisplayTable, self).__init__(parent)

        self.initUI()

    def initUI(self):

        styleDB = db.styleUI()
#        ttipDB  = Tooltips('English')

        # ------------------------------------------------------------ Style --

        self.setFrameStyle(styleDB.frame)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setMinimumWidth(650)

        #------------------------------------------------------------ Header --

#        HEADER = ['Weather Stations', '&#916;Alt.<br>(m)', 'Dist.\n(km)']
        HEADER = ['Neighboring Stations', '&#916;Alt.<br>(m)', 'Dist.<br>(km)',
                  'T<sub>max</sub>', 'T<sub>min</sub>', 'T<sub>mean</sub>',
                  'P<sub>tot</sub>' ]

        myHeader = MyHorizHeader(self)
        self.setHorizontalHeader(myHeader)

        self.setColumnCount(len(HEADER))
        self.setHorizontalHeaderLabels(HEADER)
        self.verticalHeader().hide()

        #------------------------------------------------ Column Size Policy --

        w1 = 65
        w2 = 50
        self.setColumnWidth(1, w1)
        self.setColumnWidth(2, w1)
#        self.setColumnHidden(2, True)
        self.setColumnWidth(3, w2)
        self.setColumnWidth(4, w2)
        self.setColumnWidth(5, w2)
        self.setColumnWidth(6, w2)


        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)

        #------------------------------------------------------------ Events --

    class NumTableWidgetItem(QtGui.QTableWidgetItem): #========================

        # To be able to sort numerical float item within a given column.

        # http://stackoverflow.com/questions/12673598/
        # python-numerical-sorting-in-qtablewidget

        def __init__(self, text, sortKey):
            QtGui.QTableWidgetItem.__init__(self, text,
                                            QtGui.QTableWidgetItem.UserType)
            self.sortKey = sortKey

        # Qt uses a simple < check for sorting items, override this to use
        # the sortKey

        def __lt__(self, other):

            if np.isnan(self.sortKey):
                return True
            else:
                return abs(self.sortKey) < abs(other.sortKey)


    def populate_table(self, TARGET, WEATHER, FILLPARAM): #====================

        #----------------------------------------------------- Organize Info --

        styleDB = db.styleUI()

        #----------------------------------------------------- Organize Info --

        STANAME = WEATHER.STANAME
        CLIMATEID = WEATHER.ClimateID

        HORDIST = TARGET.HORDIST
        ALTDIFF = TARGET.ALTDIFF

        CORCOEF = TARGET.CORCOEF

        limitDist = FILLPARAM.limitDist
        limitAlt = FILLPARAM.limitAlt

        nVAR = len(WEATHER.VARNAME)

        #-------------------------------------------------------- Fill Table --

        nSTA = len(STANAME)
        self.setRowCount(nSTA - 1)

        indxs = list(range(nSTA))
        indxs.remove(TARGET.index)
        row = 0
        self.setSortingEnabled(False)
        for indx in indxs:

            #-- Weather Station --

            col = 0

            item = QtGui.QTableWidgetItem(STANAME[indx])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setToolTip('%s (%s)' % (STANAME[indx], CLIMATEID[indx]))
            self.setItem(row, col, item)

            #-- Alt. Diff. --

            col += 1

            item = self.NumTableWidgetItem('%0.1f' % ALTDIFF[indx],
                                           ALTDIFF[indx])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            if abs(ALTDIFF[indx]) >= limitAlt and limitAlt >= 0:
                item.setForeground(QtGui.QBrush(QtGui.QColor(styleDB.red)))
            self.setItem(row, col, item)

            #-- Horiz. Dist. --

            col += 1

            item = self.NumTableWidgetItem('%0.1f' % HORDIST[indx],
                                           HORDIST[indx])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            if HORDIST[indx] >= limitDist and limitDist >= 0:
                item.setForeground(QtGui.QBrush(QtGui.QColor(styleDB.red)))
            self.setItem(row, col, item)

            #-- Correlation Coefficients. --

            for var in range(nVAR):

                col += 1

                item = self.NumTableWidgetItem('%0.3f' % CORCOEF[var, indx],
                                               CORCOEF[var, indx])
                item.setFlags(~QtCore.Qt.ItemIsEditable)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                if CORCOEF[var, indx] < 0.7 or np.isnan(CORCOEF[var, indx]):
                    item.setForeground(QtGui.QBrush(QtGui.QColor(styleDB.red)))
                self.setItem(row, col, item)

            row += 1

        self.setSortingEnabled(True)


class MyHorizHeader(QtGui.QHeaderView):
    # https://forum.qt.io/topic/30598/
    # solved-how-to-display-subscript-text-in-header-of-qtableview/5

    # http://stackoverflow.com/questions/1956542/
    # how-to-make-item-view-render-rich-html-text-in-qt

    # http://stackoverflow.com/questions/2336079/
    # can-i-have-more-than-one-line-in-a-table-header-in-qt

    def __init__(self, parent=None):
        super(MyHorizHeader, self).__init__(QtCore.Qt.Horizontal, parent)

        self.parent = parent

        # http://stackoverflow.com/questions/18777554/
        # why-wont-my-custom-qheaderview-allow-sorting/18777555#18777555

        self.setClickable(True)

        self.setHighlightSections(True)
        self.showMouseOverLabel = True

        self.showSectionSep = False
        self.showMouseOverSection = False

        self.multirow = True

        self.setSortIndicatorShown(False)
        self.heightHint = 20


    def paintEvent(self, event): #=============================================

        qp = QtGui.QPainter()
        qp.begin(self.viewport())

#        print self.sender()
        print(event.region)

        if self.showSectionSep:
            QtGui.QHeaderView.paintEvent(self, event)
        else:
            qp.save()
            self.paintHeader(qp)
            qp.restore()

        qp.save()
        self.paintLabels(qp)
        qp.restore()

        qp.end()


    def paintHeader(self, qp): #===============================================

        # Paint the header box for the entire width of the table.
        # This eliminates the separators between each individual section.

        opt = QtGui.QStyleOptionHeader()
        opt.rect = QtCore.QRect(0, 0, self.size().width(), self.size().height())

        self.style().drawControl(QtGui.QStyle.CE_Header, opt, qp, self)


    def paintSection(self, painter, rect, logicalIndex):

        # http://qt4-x11.sourcearchive.com/documentation/4.4.3/
        # classQHeaderView_fd6972445e0a4a0085538a3f620b03d1.
        # html#fd6972445e0a4a0085538a3f620b03d1

        if not rect.isValid():
            return

        #---------------------------------------------  draw header sections --

        opt = QtGui.QStyleOptionHeader()
        self.initStyleOption(opt) #
#        opt.initFrom(self) #
#
#        print(self.model().headerData(logicalIndex, self.orientation()))
#
        opt.rect = rect
        opt.section = logicalIndex
        opt.text = ""
#        print dir(opt)
#        print opt.SO_TabWidgetFrame

#        print int(QtGui.QStyle.State_MouseOver)

        #-------------------------------------------------- section position --

#        visual = self.visualIndex(logicalIndex)
#        if self.count() == 1:
#            opt.position = QtGui.QStyleOptionHeader.OnlyOneSection
#        elif visual == 0:
#            opt.position = QtGui.QStyleOptionHeader.Beginning
#        elif visual == self.count() - 1:
#            opt.position = QtGui.QStyleOptionHeader.End
#        else:
#            opt.position = QtGui.QStyleOptionHeader.Middle
#
#        sortIndicatorSection = self.sortIndicatorSection()
#        if sortIndicatorSection==logicalIndex:
#            opt.state = int(opt.state) + int(QtGui.QStyle.State_Sunken)

        #---------------------------------------------- mouse over highlight --

        if self.showMouseOverSection:
            mouse_pos = self.mapFromGlobal(QtGui.QCursor.pos())
            if rect.contains(mouse_pos):
                opt.state = int(opt.state) + 8192
            else:
                pass
        else:
            pass

        #----------------------------------------------------- paint section --

        self.style().drawControl(QtGui.QStyle.CE_Header, opt, painter, self)


    def paintLabels(self, qp): #=============================== Paint Labels ==

        fontfamily = db.styleUI().fontfamily

        if self.multirow:
            headerTable  = '''
                           <table border="0" cellpadding="0" cellspacing="0"
                                  align="center" width="100%%">
                             <tr>
                               <td colspan="3"></td>
                               <td colspan="4" align=center
                                   style="padding-top:8px;
                                          font-size:14px;
                                          font-family: "%s";">
                                 Correlation Coefficients
                               </td>
                             </tr>
                             <tr>
                               <td colspan="3"></td>
                               <td colspan="4"><hr width=100%%></td>
                             </tr>
                             <tr>
                           ''' % fontfamily
        else:
            headerTable =  '''
                           <table border="0" cellpadding="0" cellspacing="0"
                                  align="center" width="100%%">
                             <tr>
                           '''
#        shownSectionCount = self.count() - self.hiddenSectionCount ()

        #----------------------------------- prepare a list of logical index --

        LogicalIndex_shown_and_ordered = []
        for visualIndex in range(self.count()):
            logicalIndex = self.logicalIndex(visualIndex)
            if self.isSectionHidden(logicalIndex):
                pass
            else:
                LogicalIndex_shown_and_ordered.append(logicalIndex)

        x0 = 0
        for logicalIndex in LogicalIndex_shown_and_ordered:

            #----------------------------------------------- Grab label text --

            label = str(self.model().headerData(logicalIndex,
                                                self.orientation()))

            # ------------------------------------------ Put Labels in Table --

            # -- Highlights labels when item is selected in column --

            if self.highlightSections():
                selectedIndx = self.selectionModel().selectedIndexes()
                for index in selectedIndx:
                    if (logicalIndex == index.column()) is True:
                        label = '<b>%s<b>' % label
                        break
                    else:
                        pass

                                     # OR

            #-- Highlights labels when mouse it over section --

            sectionHeight = self.size().height()
            sectionWidth = self.sectionSize(logicalIndex)
            rect = QtCore.QRect(x0, 0, sectionWidth, sectionHeight)
            x0 += sectionWidth

            if self.showMouseOverLabel:
                mouse_pos = self.mapFromGlobal(QtGui.QCursor.pos())
                if rect.contains(mouse_pos):
                    label = '<b>%s<b>' % label
                else:
                    pass
            else:
                pass

            headerTable += '''
                           <td valign=middle align=center width=%d
                            style="padding-top:0px; padding-bottom:0px;
                                   font-size:14px;
                                   font-family:"%s";">
                             %s
                           </td>
                           ''' % (sectionWidth, fontfamily, label)

        # ---------------------------------------------------- Add Sort Icon --

        headerTable += '</tr><tr>'

        sortIndicatorSection = self.sortIndicatorSection()

        if self.sortIndicatorOrder() == QtCore.Qt.SortOrder.DescendingOrder:
            filename = 'Icons/triangle_up_center.png'
        else:
            filename = 'Icons/triangle_down_center.png'

        for logicalIndex in LogicalIndex_shown_and_ordered:

            sectionWidth = self.sectionSize(logicalIndex)
            if logicalIndex == sortIndicatorSection:
                txt = '<img src="%s">' % filename
            else:
                txt = ''
            headerTable += '''
                           <td valign=middle align=center width=%d
                            style="padding-top:0px; padding-bottom:0px;">
                             %s
                           </td>
                           ''' % (sectionWidth, txt)

        # ---- Prepare html ----

        headerTable += '''
                         </tr>
                       </table>
                       '''

        TextDoc = QtGui.QTextDocument()
        TextDoc.setTextWidth(self.size().width())
        TextDoc.setDocumentMargin(0)
        TextDoc.setHtml(headerTable)

        self.setFixedHeight(TextDoc.size().height())
        self.heightHint = TextDoc.size().height()

        # ---- Draw html ----

        rec = QtCore.QRect(0, 0, self.size().width(), self.size().height())
        TextDoc.drawContents(qp, rec)

    def sizeHint(self):

        baseSize = QtGui.QHeaderView.sizeHint(self)
        baseSize.setHeight(self.heightHint)

        self.parent.repaint()

        return baseSize


if __name__ == '__main__':

    import platform
    import sys

    app = QtGui.QApplication(sys.argv)

    if platform.system() == 'Windows':
        app.setFont(QtGui.QFont('Segoe UI', 11))
    elif platform.system() == 'Linux':
        app.setFont(QtGui.QFont('Ubuntu', 11))

    w = GapFillWeatherGUI()
    w.set_workdir('C:\\Users\\jnsebgosselin\\OneDrive\\Research\\Collaborations\\R. Martel - Suffield\\Suffield')
    w.load_data_dir_content()

    lat = w.gap_fill_worker.WEATHER.LAT
    lon = w.gap_fill_worker.WEATHER.LON
    name = w.gap_fill_worker.WEATHER.STANAME
    alt = w.gap_fill_worker.WEATHER.ALT

    # ---- Show Map ----

    GWSU16 = [50.525687, -110.64174514]
    GWSU24 = [50.368081, -111.14447737]
    GWSU34 = [50.446457, -111.0195349]

#    stamap = StaLocManager()
#    stamap.plot_stations(lat, lon, name)
#    stamap.plot_obswells(GWSU16[0], GWSU16[1], 'GW-SU-16')
#    stamap.plot_obswells(GWSU24[0], GWSU24[1], 'GW-SU-24')
#    stamap.plot_obswells(GWSU34[0], GWSU34[1], 'GW-SU-34')
#    stamap.show()
#
#    print()
#    from hydrograph3 import LatLong2Dist
#    for x, y, n, a in zip(lat, lon, name, alt):
#        print(n, LatLong2Dist(x, y, GWSU16[0], GWSU16[1]))


    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()

    i1 = 9
    i2 = 22

    n1 = w.gap_fill_worker.WEATHER.STANAME[i1]
    n2 = w.gap_fill_worker.WEATHER.STANAME[i2]

    set1 = w.gap_fill_worker.WEATHER.DATA[:, i1, 3]
    set2 = w.gap_fill_worker.WEATHER.DATA[:, i2, 3]

    plt.close('all')
    ax.plot(set1, set2, 'o')
    ax.set_xlabel(n1)
    ax.set_ylabel(n2)
    fig.show()

    for i, name in enumerate(w.gap_fill_worker.WEATHER.STANAME):
        print(name, w.gap_fill_worker.WEATHER.ALT[i])

    # ---- Show and Move Center ----

    w.show()

    qr = w.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    w.move(qr.topLeft())

    sys.exit(app.exec_())
