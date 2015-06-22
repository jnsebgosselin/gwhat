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
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
        
#---- STANDARD LIBRARY IMPORTS ----

from sys import argv
from time import clock
import csv
from os import path

#---- THIRD PARTY IMPORTS ----

import numpy as np
from PySide import QtGui, QtCore

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
import matplotlib.pyplot as plt

#---- PERSONAL IMPORTS ----

import database as db


class Tooltips():
    
    def __init__(self, language): #------------------------------- ENGLISH -----
        
        self.undo = 'Undo'
        self.clearall = 'Clear all extremum from the graph'
        self.home = 'Reset original view.'
        self.editPeak = ('Toggle edit mode to manually add extremums ' +
                         'to the graph')
        self.delPeak = ('Toggle edit mode to manually remove extremums ' +
                        'from the graph')
        self.pan = 'Pan axes with left mouse, zoom with right'
        self.MRCalc = ('Calculate the Master Recession Curve (MRC) for the ' +
                       'selected time pertiods')
        self.find_peak = 'Automated search for local extremum (EXPERIMENTAL FEATURE)'
        
        self.toggle_layout_mode = ('Toggle between layout and computation ' +
                                   'mode (EXPERIMENTAL FEATURE)')
                                   
        self.btn_Waterlvl_lineStyle = ('Show water lvl data as dots instead ' +
                                       'of a continuous line')
                                       
        self.btn_strati = ('Toggle on and off the display of the soil' +
                           ' stratigraphic layers')
                           
        self.mrc2rechg = ('Compute recharge from the water level time series' +
                          ' using the MRC calculated and the water-table' +
                          ' fluctuation principle')
        
        if language == 'French': #--------------------------------- FRENCH -----
            
            pass
        
class WLCalc(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(WLCalc, self).__init__(parent)

        self.initUI()
        self.fig_MRC_widget.mpl_connect('button_press_event', self.onclick)
        self.fig_MRC_widget.mpl_connect('motion_notify_event',
                                        self.mouse_vguide)
              
    def initUI(self):
        
        #--------------------------------------------------- INIT VARIABLES ----
        
        iconDB = db.icons()
        StyleDB = db.styleUI()
        ttipDB = Tooltips('English')
        
        self.isGraphExists = False
        self.peak_indx = np.array([]).astype(int)
        self.peak_memory = [np.array([]).astype(int)]
        self.time = []
        self.water_lvl = []
        
        self.soilFilename = []
        
        self.A = []
        self.B = []
        
        #---- load soil column info ----
        
        self.SOILPROFIL = SoilProfil()
        
        #---------------------------------------------------- FIGURE CANVAS ----
        
        self.setWindowTitle('Master Recession Curve Estimation')
        
        self.fig_MRC = plt.figure()        
        self.fig_MRC.set_size_inches(8.5, 5)        
        self.fig_MRC.patch.set_facecolor('white')
        self.fig_MRC_widget = FigureCanvasQTAgg(self.fig_MRC)
        
        # Put figure canvas in a QFrame widget.
        
        fig_frame_grid = QtGui.QGridLayout()
        self.fig_frame_widget = QtGui.QFrame()
        
        fig_frame_grid.addWidget(self.fig_MRC_widget, 0, 0)
        
        self.fig_frame_widget.setLayout(fig_frame_grid)
        fig_frame_grid.setContentsMargins(0, 0, 0, 0) # Left, Top, Right, Bottom
        
        self.fig_frame_widget.setFrameStyle(StyleDB.frame)
        self.fig_frame_widget.setLineWidth(2)
        self.fig_frame_widget.setMidLineWidth(1)
        
        #---------------------------------------------------------- TOOLBAR ----
        
        self.toolbar = NavigationToolbar2QT(self.fig_MRC_widget, self)
        self.toolbar.hide()
        
        self.btn_layout_mode = QtGui.QToolButton()
        self.btn_layout_mode.setAutoRaise(False)
        self.btn_layout_mode.setIcon(iconDB.toggleMode)
        self.btn_layout_mode.setToolTip(ttipDB.toggle_layout_mode)
        self.btn_layout_mode.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_layout_mode.setIconSize(StyleDB.iconSize)
        
        self.btn_undo = QtGui.QToolButton()
        self.btn_undo.setAutoRaise(True)
        self.btn_undo.setIcon(iconDB.undo)
        self.btn_undo.setToolTip(ttipDB.undo)
        self.btn_undo.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_undo.setEnabled(False)
        self.btn_undo.setIconSize(StyleDB.iconSize)
        
        self.btn_clearPeak = QtGui.QToolButton()
        self.btn_clearPeak.setAutoRaise(True)
        self.btn_clearPeak.setIcon(iconDB.clear_search)
        self.btn_clearPeak.setToolTip(ttipDB.clearall)
        self.btn_clearPeak.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_clearPeak.setIconSize(StyleDB.iconSize)
        
        self.btn_home = QtGui.QToolButton()
        self.btn_home.setAutoRaise(True)
        self.btn_home.setIcon(iconDB.home)
        self.btn_home.setToolTip(ttipDB.home)
        self.btn_home.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_home.setIconSize(StyleDB.iconSize)
        
        self.btn_findPeak = QtGui.QToolButton()
        self.btn_findPeak.setAutoRaise(True)
        self.btn_findPeak.setIcon(iconDB.findPeak2)
        self.btn_findPeak.setToolTip(ttipDB.find_peak)
        self.btn_findPeak.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_findPeak.setIconSize(StyleDB.iconSize)
        
        self.btn_editPeak = QtGui.QToolButton()
        self.btn_editPeak.setAutoRaise(True)
        self.btn_editPeak.setIcon(iconDB.add_point)
        self.btn_editPeak.setToolTip(ttipDB.editPeak)
        self.btn_editPeak.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_editPeak.setIconSize(StyleDB.iconSize)
        
        self.btn_delPeak = QtGui.QToolButton()
        self.btn_delPeak.setAutoRaise(True)
        self.btn_delPeak.setIcon(iconDB.erase)
        self.btn_delPeak.setToolTip(ttipDB.delPeak)
        self.btn_delPeak.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_delPeak.setIconSize(StyleDB.iconSize)
        
        self.btn_pan = QtGui.QToolButton()
        self.btn_pan.setAutoRaise(True)
        self.btn_pan.setIcon(iconDB.pan)
        self.btn_pan.setToolTip(ttipDB.pan)
        self.btn_pan.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_pan.setIconSize(StyleDB.iconSize)
        
        self.btn_MRCalc = QtGui.QToolButton()
        self.btn_MRCalc.setAutoRaise(True)
        self.btn_MRCalc.setIcon(iconDB.MRCalc2)
        self.btn_MRCalc.setToolTip(ttipDB.MRCalc)
        self.btn_MRCalc.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_MRCalc.setIconSize(StyleDB.iconSize)
        
        self.btn_mrc2rechg = QtGui.QToolButton()
        self.btn_mrc2rechg.setAutoRaise(True)
        self.btn_mrc2rechg.setIcon(iconDB.mrc2rechg)
        self.btn_mrc2rechg.setToolTip(ttipDB.mrc2rechg)
        self.btn_mrc2rechg.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_mrc2rechg.setIconSize(StyleDB.iconSize)
        
        self.btn_Waterlvl_lineStyle = QtGui.QToolButton()
        self.btn_Waterlvl_lineStyle.setAutoRaise(True)
        self.btn_Waterlvl_lineStyle.setIcon(iconDB.showDataDots)
        self.btn_Waterlvl_lineStyle.setToolTip(ttipDB.btn_Waterlvl_lineStyle)
        self.btn_Waterlvl_lineStyle.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_Waterlvl_lineStyle.setIconSize(StyleDB.iconSize)
        
        self.btn_strati = QtGui.QToolButton()
        self.btn_strati.setAutoRaise(True)
        self.btn_strati.setIcon(iconDB.stratigraphy)
        self.btn_strati.setToolTip(ttipDB.btn_strati)
        self.btn_strati.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_strati.setIconSize(StyleDB.iconSize)
                        
        separator1 = QtGui.QFrame()
        separator1.setFrameStyle(StyleDB.VLine)
        separator2 = QtGui.QFrame()
        separator2.setFrameStyle(StyleDB.VLine)
        separator3 = QtGui.QFrame()
        separator3.setFrameStyle(StyleDB.VLine)
        separator4 = QtGui.QFrame()
        separator4.setFrameStyle(StyleDB.VLine)
        
        subgrid_toolbar = QtGui.QGridLayout()
        toolbar_widget = QtGui.QWidget()
        
        row = 0
        col = 0
        subgrid_toolbar.addWidget(self.btn_layout_mode, row, col)
        col += 1
        subgrid_toolbar.addWidget(separator3, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_undo, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_clearPeak, row, col)                
        col += 1        
        subgrid_toolbar.addWidget(self.btn_findPeak, row, col)
        col += 1 
        subgrid_toolbar.addWidget(self.btn_editPeak, row, col)
        col += 1        
        subgrid_toolbar.addWidget(self.btn_delPeak, row, col)
        col += 1        
        subgrid_toolbar.addWidget(separator1, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_home, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_pan, row, col)
        col += 1        
        subgrid_toolbar.addWidget(separator2, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_MRCalc, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_mrc2rechg, row, col)
        col += 1        
        subgrid_toolbar.addWidget(separator4, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_Waterlvl_lineStyle, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.btn_strati, row, col)
                
        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)
        subgrid_toolbar.setColumnStretch(col+1, 500)
                        
        toolbar_widget.setLayout(subgrid_toolbar)
        
        #--------------------------------------------------- MRC PARAMETERS ----
        
        MRCtype_label = QtGui.QLabel('MRC Type :')
        
        self.MRC_type = QtGui.QComboBox()
        self.MRC_type.addItems(['Linear', 'Exponential'])
        self.MRC_type.setCurrentIndex(1)
        
        self.MRC_ObjFnType = QtGui.QComboBox()
        self.MRC_ObjFnType.addItems(['RMSE', 'MAE'])
        self.MRC_ObjFnType.setCurrentIndex(0)
        
        self.MRC_results = QtGui.QTextEdit()
        self.MRC_results.setReadOnly(True)
        self.MRC_results.setFixedHeight(100)
        
        grid_MRCparam = QtGui.QGridLayout()
        self.widget_MRCparam = QtGui.QFrame()
        self.widget_MRCparam.setFrameStyle(StyleDB.frame)
        
        row = 0
        col = 0
        grid_MRCparam.addWidget(MRCtype_label, row, col)
        col += 1
        grid_MRCparam.addWidget(self.MRC_type, row, col)
        row += 1
#        grid_MRCparam.addWidget(self.MRC_ObjFnType, row, col)
        row += 1
        col = 0
        grid_MRCparam.addWidget(self.MRC_results, row, col, 1, 2)
        
        grid_MRCparam.setSpacing(5)
        grid_MRCparam.setContentsMargins(5, 5, 5, 5) # (L, T, R, B)
        grid_MRCparam.setColumnStretch(1, 500)        
        
        self.widget_MRCparam.setLayout(grid_MRCparam)
                
        #-------------------------------------------------------- MAIN GRID ----
        
        mainGrid = QtGui.QGridLayout()
        
        row = 0 
        mainGrid.addWidget(toolbar_widget, row, 0)
        row += 1
        mainGrid.addWidget(self.fig_frame_widget, row, 0)        
              
        self.setLayout(mainGrid)
        mainGrid.setContentsMargins(0, 0, 0, 0) # Left, Top, Right, Bottom 
#        mainGrid.setSpacing(15)
        mainGrid.setRowStretch(1, 500)
        
        #---------------------------------------------------- MESSAGE BOXES ----
                                          
        self.msgError = QtGui.QMessageBox()
        self.msgError.setIcon(QtGui.QMessageBox.Warning)
        self.msgError.setWindowTitle('Error Message')
                
        #----------------------------------------------------------- EVENTS ----
        
        #----- Toolbox -----
        
        self.btn_undo.clicked.connect(self.undo)
        self.btn_clearPeak.clicked.connect(self.clear_all_peaks)        
        self.btn_home.clicked.connect(self.home)
        self.btn_findPeak.clicked.connect(self.find_peak)
        self.btn_editPeak.clicked.connect(self.edit_peak)
        self.btn_delPeak.clicked.connect(self.delete_peak)
        self.btn_pan.clicked.connect(self.pan_graph)
        self.btn_MRCalc.clicked.connect(self.btn_MRCalc_isClicked)
        self.btn_Waterlvl_lineStyle.clicked.connect(
                                                 self.change_waterlvl_lineStyle)
        self.btn_strati.clicked.connect(self.btn_strati_isClicked)
        self.btn_mrc2rechg.clicked.connect(self.btn_mrc2rechg_isClicked)
        
        
    def emit_error_message(self, error_text):
        
        self.msgError.setText(error_text)
        self.msgError.exec_()
    
    def btn_MRCalc_isClicked(self):
        
        if self.isGraphExists == False:
            print 'Graph is empty'
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            return
            
        if len(self.peak_indx) == 0:
             print 'No extremum selected'
             return
        
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        A, B, hp, obj = mrc_calc(self.time, self.water_lvl, self.peak_indx, 
                                 self.MRC_type.currentIndex())
        
        #---- display result ----
        
        txt = u'∂h/∂t (mm/d) = -%0.2f h + %0.2f' % (A*1000, B*1000)
        self.MRC_results.setText(txt)        
        txt = '\n%s = %f' % (self.MRC_ObjFnType.currentText(), obj)                          
        self.MRC_results.append(txt)
        
        #---- plot result ----
        
        self.h3_ax0.set_xdata(self.time)
        self.h3_ax0.set_ydata(hp)        
        self.fig_MRC_widget.draw()
                
        #---- store result in class var ----
        
        self.A = A
        self.B = B
        
        #---- Compute Recharge ----
        
        if path.exists(self.soilFilename):

            self.SOILPROFIL.load_info(self.soilFilename) 
            
            rechg = mrc2rechg(self.time, self.water_lvl, self.A, self.B,
                              self.SOILPROFIL.zlayer, self.SOILPROFIL.Sy,
                              self.peak_indx)
                              
            rechg_tot = np.sum(rechg) * 1000
                  
            txt = '\nRecharge = %0.0f mm' % (rechg_tot) 
            self.MRC_results.append(txt)
            
        QtGui.QApplication.restoreOverrideCursor()
        
    def btn_mrc2rechg_isClicked(self):
        
        if not self.A and not self.B:
            print('Need to calculate MRC equation first.')
            return
            
        if not path.exists(self.soilFilename):
            print('A ".sol" file is needed for the calculation of' +
                  ' groundwater recharge from the MRC')
            return
            
        self.SOILPROFIL.load_info(self.soilFilename)        
        
        mrc2rechg(self.time, self.water_lvl, self.A, self.B,
                  self.SOILPROFIL.zlayer, self.SOILPROFIL.Sy,
                  self.peak_indx)
            
    def plot_peak(self):
                
        if len(self.peak_memory) == 1:
            self.btn_undo.setEnabled(False)
        else:
            self.btn_undo.setEnabled(True)
            
        if self.isGraphExists == True:
            
            self.h2_ax0.set_xdata(self.time[self.peak_indx])
            self.h2_ax0.set_ydata(self.water_lvl[self.peak_indx])
                                   
            self.fig_MRC_widget.draw()
    
    def find_peak(self):
        
        if self.isGraphExists == False:
            print 'Graph is empty'
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            return
        
        n_j, n_add = local_extrema(self.water_lvl, 4 * 5)
        
        # Removing first and last point if necessary to always start with a
        # maximum and end with a minimum.
        
        # WARNING: y axis is inverted. Consequently, the logic needs to be 
        #          inverted also
        
        if n_j[0] > 0:
            n_j = np.delete(n_j, 0)
            
        if n_j[-1] < 0:
            n_j = np.delete(n_j, -1)
        
        self.peak_indx = np.abs(n_j).astype(int)
        self.peak_memory.append(self.peak_indx)
        
        self.plot_peak()
        
    def edit_peak(self):

        if self.isGraphExists == False:
            print 'Graph is empty'
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            return
            
        if self.btn_editPeak.autoRaise(): 
            
            # Activate <edit_peak>
            self.btn_editPeak.setAutoRaise(False)            
            
            # Deactivate <pan_graph>
            # http://stackoverflow.com/questions/17711099
            self.btn_pan.setAutoRaise(True)
            if self.toolbar._active == "PAN":
                self.toolbar.pan()
                
            # Deactivate <delete_peak>
            self.btn_delPeak.setAutoRaise(True)
            
        else:

            # Deactivate <edit_peak> and hide guide line
            self.btn_editPeak.setAutoRaise(True)
            self.ly.set_xdata(-1)
            self.fig_MRC_widget.draw()
            
    def delete_peak(self):
        
        if self.isGraphExists == False:
            print 'Graph is empty'
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            return
        
        if self.btn_delPeak.autoRaise():
            
            # Activate <delete_peak>
            self.btn_delPeak.setAutoRaise(False)
            
            # Deactivate <pan_graph>
            # http://stackoverflow.com/questions/17711099
            self.btn_pan.setAutoRaise(True)
            if self.toolbar._active == "PAN":
                self.toolbar.pan()
                
            # Deactivate <edit_peak> and hide guide line
            self.btn_editPeak.setAutoRaise(True)
            self.ly.set_xdata(-1)
            self.fig_MRC_widget.draw()
            
        else:

            # Deactivate <delete_peak>
            self.btn_delPeak.setAutoRaise(True)
        
    def pan_graph(self):
        
        if self.isGraphExists == False:
            print 'Graph is empty'
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            return
                
        if self.btn_pan.autoRaise():

            # Deactivate <edit_peak> and hide guide line
            self.btn_editPeak.setAutoRaise(True)
            self.ly.set_xdata(-1)
            self.fig_MRC_widget.draw()
            
            # Deactivate <delete_peak>
            self.btn_delPeak.setAutoRaise(True)
            
            # Activate <pan_graph>
            self.btn_pan.setAutoRaise(False)
            self.toolbar.pan()
            
        else:
            self.btn_pan.setAutoRaise(True)
            self.toolbar.pan()
            
    def home(self):
        
        if self.isGraphExists == False:
            print 'Graph is empty'
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            return
            
        self.toolbar.home()

    def undo(self):
        
        if self.isGraphExists == False:
            print 'Graph is empty'
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            return
        
        if len(self.peak_memory) > 1:
            self.peak_indx = self.peak_memory[-2]
            del self.peak_memory[-1]
        
            self.plot_peak()
        
            print 'undo'
        else:
            pass
            
    def clear_all_peaks(self):
        
        if self.isGraphExists == False:
            print 'Graph is empty'
            self.emit_error_message(
            '''<b>Please select a valid Water Level Data File first.</b>''')
            return
                            
        self.peak_indx = np.array([]).astype(int)
        self.peak_memory.append(self.peak_indx)
    
        self.plot_peak()
                
    def plot_water_levels(self):
        
        t = self.time
        x = self.water_lvl
        fig = self.fig_MRC
        fig.clf()
        
        fheight = fig.get_figheight()
        fwidth = fig.get_figwidth()
        
        #------------------------------------------------------------ RESET ----
        
        self.peak_indx = np.array([]).astype(int)
        self.peak_memory = [np.array([]).astype(int)]
        self.btn_undo.setEnabled(False)
    
        #---------------------------------------------------------- MARGINS ----
        
        left_margin  = 0.85
        right_margin = 0.25
        bottom_margin = 0.85
        top_margin = 0.25
           
        x0 = left_margin / fwidth
        y0 = bottom_margin / fheight
        w = 1 - (left_margin + right_margin) / fwidth
        h = 1 - (bottom_margin + top_margin) / fheight
                        
        #---------------------------------------------------- AXES CREATION ----        
        
        #---- Water Level (Host) ----
        
        self.ax0  = fig.add_axes([x0, y0, w, h], zorder=0)
        self.ax0.patch.set_visible(False)
       
        #----------------------------------------------------------- XTICKS ---- 
        
        self.ax0.xaxis.set_ticks_position('bottom')
        self.ax0.tick_params(axis='x',direction='out', gridOn=True)

        #----------------------------------------------------------- YTICKS ----
        
        self.ax0.yaxis.set_ticks_position('left')
        self.ax0.tick_params(axis='y',direction='out', gridOn=True)
                
        #--------------------------------------------------- SET AXIS RANGE ---- 
       
        delta = 0.05
        Xmin0 = np.min(t) - (np.max(t) - np.min(t)) * delta
        Xmax0 = np.max(t) + (np.max(t) - np.min(t)) * delta
        
        indx = np.where(~np.isnan(x))
        Ymin0 = np.min(x[indx]) - (np.max(x[indx]) - np.min(x[indx])) * delta
        Ymax0 = np.max(x[indx]) + (np.max(x[indx]) - np.min(x[indx])) * delta
    
        self.ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])
        self.ax0.invert_yaxis()
        
        #----------------------------------------------------------- LABELS ----
    
        self.ax0.set_ylabel('Water level (mbgs)', fontsize=14, labelpad=25,
                            verticalalignment='top', color='black')
        self.ax0.set_xlabel('Time (days)', fontsize=14, labelpad=25,
                            verticalalignment='bottom', color='black')

        #--------------------------------------------------------- PLOTTING ----
    
        #---- Water Levels ----
    
        self.h1_ax0, = self.ax0.plot(t, x, color='blue', clip_on=True, zorder=10,
                                     marker='None', linestyle='-')
        
        #---- Peaks ----
                 
        self.h2_ax0, = self.ax0.plot([], [], color='red', clip_on=True, 
                                     zorder=30, marker='o', linestyle='None')
                                     
        #---- Vertical guide line under cursor ----
                                     
        self.ly = self.ax0.axvline(x=.5, ymin=0, ymax=1, color='red', zorder=40)
        
        #---- Cross Remove Peaks ----
        
        self.xcross, = self.ax0.plot(-1, 0, color='red', clip_on=True, 
                                     zorder=20, marker='x', linestyle='None',
                                     markersize = 15, markeredgewidth = 3)
                                     
        #---- Recession ----
                                     
        self.h3_ax0, = self.ax0.plot([], [], color='red', clip_on=True,
                                     zorder=15, marker='None', linestyle='--')                          
        
        #---- Strati ----
        
        if not self.btn_strati.autoRaise():
            self.display_soil_layer()
            
        #---------------------------------------------------- UPDATE WIDGET ----

        self.fig_MRC_widget.draw()
        
        self.isGraphExists = True
    
    def btn_strati_isClicked(self):
        
        #---- Checks ----
        
        if self.isGraphExists == False:
            print('Graph is empty.')
            self.btn_strati.setAutoRaise(True)
            return
        
        #---- Attribute Action ----
        
        if self.btn_strati.autoRaise():
            self.btn_strati.setAutoRaise(False)
            self.display_soil_layer()
        else:
            self.btn_strati.setAutoRaise(True)
            self.hide_soil_layer()        
        
    def hide_soil_layer(self):
        
        for i in range(len(self.zlayer)):
            self.layers[i].remove()
            self.stratLines[i].remove()
        self.stratLines[i+1].remove()    
        
        self.fig_MRC_widget.draw()
        
    def display_soil_layer(self):
        
        #---- Check ----
        
        if not path.exists(self.soilFilename):
            print('No ".sol" file found for this well.')
            self.btn_strati.setAutoRaise(True)
            return
            
        #---- load soil column info ----
    
        reader = open(self.soilFilename,'rb')
        reader = csv.reader(reader, delimiter="\t")
        reader = list(reader)
   
        NLayer = len(reader)
                           
        self.zlayer = np.empty(NLayer).astype(float)
        self.soilName = np.empty(NLayer).astype(str)
        self.Sy = np.empty(NLayer).astype(float)
        self.soilColor = np.empty(NLayer).astype(str)
        
        for i in range(NLayer):
            self.zlayer[i] = reader[i][0]
            self.soilName[i] = reader[i][1]
            self.Sy[i] = reader[i][2]
            try:
                self.soilColor[i] = reader[i][3]
                print reader[i][3]
            except:
                self.soilColor[i] = '#FFFFFF'                
                
        print self.soilColor

        #---- plot layers and lines ----

        self.layers = [0] * len(self.zlayer)
        self.stratLines = [0] * (len(self.zlayer)+1)

        up = 0
        self.stratLines[0], = self.ax0.plot([0, 99999], [up, up],
                                            color="black",
                                            linewidth=1)
        for i in range(len(self.zlayer)):
                        
            down = self.zlayer[i]
                                                   
            self.stratLines[i+1], = self.ax0.plot([0, 99999], [down, down],
                                                  color="black",
                                                  linewidth=1)
            try:                                                  
                self.layers[i] = self.ax0.fill_between(
                    [0, 99999], up, down, color=self.soilColor[i], zorder=0)
            except:
                self.layers[i] = self.ax0.fill_between(
                    [0, 99999], up, down, color='#FFFFFF', zorder=0)

            up = down
            
        self.fig_MRC_widget.draw()
                
        
    def change_waterlvl_lineStyle(self):
        
        if self.isGraphExists == False:
            print 'Graph is empty'            
            return
            
        if self.btn_Waterlvl_lineStyle.autoRaise():
            
            self.btn_Waterlvl_lineStyle.setAutoRaise(False)
            
            plt.setp(self.h1_ax0, markerfacecolor='blue', markersize = 5,
                     markeredgecolor='blue', markeredgewidth=1.5,
                     linestyle='none', marker='.')
            
        else:
            
            self.btn_Waterlvl_lineStyle.setAutoRaise(True)
            
            plt.setp(self.h1_ax0, marker='None', linestyle='-')
            
        self.fig_MRC_widget.draw()
            
    def mouse_vguide(self, event):

        # http://matplotlib.org/examples/pylab_examples/cursor_demo.html
        if not self.btn_editPeak.autoRaise():
           
           # Trace a red vertical guide (line) that folows the mouse marker.
           
            x = event.xdata
            
            # update the line positions
            self.ly.set_xdata(x)
            
            self.fig_MRC_widget.draw()
            
        elif not self.btn_delPeak.autoRaise() and len(self.peak_indx) > 0:
            
            # For deleting peak in the graph. Will put a cross on top of the
            # peak to delete if some proximity conditions are met.
            
            x = event.x
            y = event.y
            
            xt = np.empty(len(self.peak_indx))
            yt = np.empty(len(self.peak_indx))
            xpeak = self.time[self.peak_indx]
            ypeak = self.water_lvl[self.peak_indx]
            
            for i in range(len(self.peak_indx)):                
                xt[i], yt[i] = self.ax0.transData.transform((xpeak[i],ypeak[i]))
           
            r = ((xt - x)**2 + (yt - y)**2)**0.5
            
            if np.min(r) < 15 :

                indx = np.where(r == np.min(r))[0][0]
                                
                self.xcross.set_xdata(xpeak[indx])
                self.xcross.set_ydata(ypeak[indx])
                
                self.fig_MRC_widget.draw()
            else:
                self.xcross.set_xdata(-1)
                
                self.fig_MRC_widget.draw()            
        else:
            pass
            
    def onclick(self, event):
        
        x = event.x
        y = event.y
 
        #---------------------------------------------------- DELETE A PEAK ---- 
        
        # www.github.com/eliben/code-for-blog/blob/master/2009/qt_mpl_bars.py

        if x != None and y != None and not self.btn_delPeak.autoRaise():
            
            if len(self.peak_indx) == 0: return
                
            xt = np.empty(len(self.peak_indx))
            yt = np.empty(len(self.peak_indx))
            xpeak = self.time[self.peak_indx]
            ypeak = self.water_lvl[self.peak_indx]
        
            for i in range(len(self.peak_indx)):                
                xt[i], yt[i] = self.ax0.transData.transform((xpeak[i],ypeak[i]))
       
            r = ((xt - x)**2 + (yt - y)**2)**0.5
        
            if np.min(r) < 15 :

                indx = np.where(r == np.min(r))[0][0]
                            
                self.xcross.set_xdata(xpeak[indx])
                self.xcross.set_ydata(ypeak[indx])
                
                self.peak_indx = np.delete(self.peak_indx, indx)
                self.peak_memory.append(self.peak_indx)
                
                xpeak = np.delete(xpeak, indx)
                ypeak = np.delete(ypeak, indx)
                
                
                self.xcross.set_xdata(-1)            
                self.plot_peak()
            else:
                pass
            
        #------------------------------------------------------- ADD A PEAK ----        

        elif x != None and y != None and not self.btn_editPeak.autoRaise():
        # print(event.xdata, event.ydata)
            
            xclic = event.xdata
        
            # http://matplotlib.org/examples/pylab_examples/cursor_demo.html
            
            x = self.time
            y = self.water_lvl
            
            indxmin = np.where(x < xclic)[0]
            indxmax = np.where(x > xclic)[0]
            if len(indxmax) == 0:
                
                # Marker is outside the water level time series, to the right.
                # The last data point is added to "peak_indx". 
                
                self.peak_indx = np.append(self.peak_indx, len(x)-1)
                self.peak_memory.append(self.peak_indx)
                
            elif len(indxmin) == 0:
                
                # Marker is outside the water level time series, to the left.
                # The first data point is added to "peak_indx".
                
                self.peak_indx = np.append(self.peak_indx, 0)
                self.peak_memory.append(self.peak_indx)
                
            else:
                
                # Marker is between two data point. The closest data point to
                # the marker is then selected.
                
                indxmin = indxmin[-1]
                indxmax = indxmax[0]
                
                dleft = xclic - x[indxmin]
                dright = x[indxmax] - xclic
                
                if dleft < dright:
                    
                    self.peak_indx = np.append(self.peak_indx, indxmin)
                    self.peak_memory.append(self.peak_indx)
                                        
                else:
                    
                    self.peak_indx = np.append(self.peak_indx, indxmax)
                    self.peak_memory.append(self.peak_indx)
           
            self.plot_peak()    
   
#===============================================================================
def local_extrema(x, Deltan):
    """
    Code adapted from a MATLAB script at 
    www.ictp.acad.ro/vamos/trend/local_extrema.htm
    
    LOCAL_EXTREMA Determines the local extrema of a given temporal scale.
    
    ---- OUTPUT ----
    
    n_j = The positions of the local extrema of a partition of scale Deltan
          as defined at p. 82 in the book [ATE] C. Vamos and M. Craciun,
          Automatic Trend Estimation, Springer 2012.
          The positions of the maxima are positive and those of the minima
          are negative.
          
    kadd = n_j(kadd) are the local extrema with time scale smaller than Deltan
           which are added to the partition such that an alternation of maxima
           and minima is obtained.    
    """
#===============================================================================

    N = len(x)
    
    ni = 0
    nf = N - 1
    
    #-------------------------------------------------------------- PLATEAU ----
    
    # Recognize the plateaus of the time series x defined in [ATE] p. 85
    # [n1[n], n2[n]] is the interval with the constant value equal with x[n]
    # if x[n] is not contained in a plateau, then n1[n] = n2[n] = n
    #
    # Example with a plateau between indices 5 and 8:
    #  x = [1, 2, 3, 4, 5, 6, 6, 6, 6, 7, 8,  9, 10, 11, 12]
    # n1 = [0, 1, 2, 3, 4, 5, 5, 5, 5, 9, 10, 11, 12, 13, 14]
    # n2 = [0, 1, 2, 3, 4, 8, 8, 8, 8, 9, 10, 11, 12, 13, 14]
   
    n1 = np.arange(N)
    n2 = np.arange(N)
                
    dx = np.diff(x)
    if np.any(dx == 0):
        print 'At least 1 plateau has been detected in the data'
        for i in range(N-1):            
            if x[i+1] == x[i]:                
                n1[i+1] = n1[i]
                n2[n1[i+1]:i+1] = i+1

    #-------------------------------------------------------- MAIN FUNCTION ----
    
    # the iterative algorithm presented in Appendix E of [ATE]
    
    nc = 0    # the time step up to which the time series has been
              # analyzed ([ATE] p. 127)
    Jest = 0  # number of local extrema of the partition of scale DeltaN 
    iadd = 0  # number of additional local extrema
    flagante = 0
    kadd = [] # order number of the additional local extrema between all the
              # local extrema
    n_j = []  # positions of the local extrema of a partition of scale Deltan
    
    while nc < nf:

        # the next extremum is searched within the interval [nc, nlim]
        
        nlim = min(nc + Deltan, nf)   
    
        #--------------------------------------------------- SEARCH FOR MIN ----
    
        xmin = np.min(x[nc:nlim+1])
        nmin = np.where(x[nc:nlim+1] == xmin)[0][0] + nc
       
        nlim1 = max(n1[nmin] - Deltan, ni)
        nlim2 = min(n2[nmin] + Deltan, nf)
        
        xminn = np.min(x[nlim1:nlim2+1])
        nminn = np.where(x[nlim1:nlim2+1] == xminn)[0][0] + nlim1
        
        # if flagmin = 1 then the minimum at nmin satisfies condition (6.1)
        if nminn == nmin:
            flagmin = 1
        else:
            flagmin = 0
            
        #--------------------------------------------------- SEARCH FOR MAX ----
            
        xmax = np.max(x[nc:nlim+1])
        nmax = np.where(x[nc:nlim+1] == xmax)[0][0] + nc   

        nlim1 = max(n1[nmax] - Deltan, ni)        
        nlim2 = min(n2[nmax] + Deltan, nf)
        
        xmaxx = np.max(x[nlim1:nlim2+1])
        nmaxx = np.where(x[nlim1:nlim2+1] == xmaxx)[0][0] + nlim1 
        
        # If flagmax = 1 then the maximum at nmax satisfies condition (6.1)
        if nmaxx == nmax: 
            flagmax = 1
        else: 
            flagmax=0
       
        #------------------------------------------------------- MIN or MAX ----

        # The extremum closest to nc is kept for analysis
        if flagmin == 1 and flagmax == 1:
            if nmin < nmax:
                flagmax = 0
            else:
                flagmin = 0

        #------------------------------------------------ ANTERIOR EXTREMUM ----
                
        if flagante == 0: # No ANTERIOR extremum
            
            if flagmax == 1:  # CURRENT extremum is a MAXIMUM

                nc = n1[nmax] + 1
                flagante = 1
                n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))
                Jest += 1 
                
            elif flagmin == 1:  # CURRENT extremum is a MINIMUM

                nc = n1[nmin] + 1
                flagante = -1
                n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                Jest += 1

            else: # No extremum

                nc = nc + Deltan
                
        elif flagante == -1: # ANTERIOR extremum is an MINIMUM
            
            tminante = np.abs(n_j[-1])
            xminante = x[tminante]
            
            if flagmax == 1: # CURRENT extremum is a MAXIMUM                

                if xminante < xmax:

                    nc = n1[nmax] + 1
                    flagante = 1
                    n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))
                    Jest += 1
                    
                else: 
                    
                    # CURRENT MAXIMUM is smaller than the ANTERIOR MINIMUM
                    # an additional maximum is added ([ATE] p. 82 and 83)
                    
                    xmaxx = np.max(x[tminante:nmax+1])
                    nmaxx = np.where(x[tminante:nmax+1] == xmaxx)[0][0]               
                    nmaxx += tminante
                    
                    nc = n1[nmaxx] + 1
                    flagante = 1
                    n_j = np.append(n_j, np.floor((n1[nmaxx] + n2[nmaxx]) / 2.))
                    Jest += 1
                    
                    kadd = np.append(kadd, Jest-1)
                    iadd += 1
                
            elif flagmin == 1: # CURRENT extremum is also a MINIMUM
                               # an additional maximum is added ([ATE] p. 82)

                nc = n1[nmin]
                flagante = 1
                
                xmax = np.max(x[tminante:nc+1])
                nmax = np.where(x[tminante:nc+1] == xmax)[0][0] + tminante                
                
                n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))                               
                Jest += 1
                
                kadd = np.append(kadd, Jest-1)
                iadd += 1
                
            else:
                nc = nc + Deltan
                
        else: # ANTERIOR extremum is a MAXIMUM
            
            tmaxante = np.abs(n_j[-1])
            xmaxante = x[tmaxante]
            
            if flagmin == 1: # CURRENT extremum is a MINIMUM
                
                if xmaxante > xmin:
                    
                    nc = n1[nmin] + 1
                    flagante = -1
                    
                    n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                    Jest += 1
                    
                else: # CURRENT MINIMUM is larger than the ANTERIOR MAXIMUM:
                      # an additional minimum is added ([ATE] p. 82 and 83)
                    
                    xminn = np.min(x[tmaxante:nmin+1])  
                    nminn = np.where(x[tmaxante:nmin+1] == xminn)[0][0]
                    nminn += tmaxante
                    
                    nc = n1[nminn] + 1
                    flagante = -1
                    
                    n_j = np.append(n_j, -np.floor((n1[nminn] + n2[nminn]) / 2.))                
                    Jest = Jest + 1

                    kadd = np.append(kadd, Jest-1)                
                    iadd += 1
                    
            elif flagmax == 1: # CURRENT extremum is also an MAXIMUM:
                               # an additional minimum is added ([ATE] p. 82)
                nc = n1[nmax]
                flagante = -1
                
                xmin = np.min(x[tmaxante:nc+1])
                nmin = np.where(x[tmaxante:nc+1] == xmin)[0]            
                nmin += tmaxante
                
                n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                Jest += 1
                
                kadd = np.append(kadd, Jest-1)
                iadd += 1
                
            else:
                nc = nc + Deltan
            
#    # x(ni) is not included in the partition of scale Deltan 
#    nj1 = np.abs(n_j[0])
#    if nj1 > ni:
#        if n1[nj1] > ni: # the boundary ni is not included in the plateau
#                         # containing the first local extremum at n_j[1] and it
#                         # is added as an additional local extremum ([ATE] p. 83)
#            n_j = np.hstack((-np.sign(n_j[0]) * ni, n_j))
#            Jest += 1
#            
#            kadd = np.hstack((0, kadd + 1))
#            iadd += 1
#
#        else: # the boundary ni is included in the plateau containing
#              # the first local extremum at n_j(1) and then the first local
#              # extremum is moved at the boundary of the plateau
#            n_j[0] = np.sign(n_j[0]) * ni
   
   
#    # the same situation as before but for the other boundary nf
#    njJ = np.abs(n_j[Jest])
#    if njJ < nf:
#        if n2[njJ] < nf:
#            n_j = np.append(n_j, -np.sign(n_j[Jest]) * nf)
#            Jest += 1
#
#            kadd = np.append(kadd, Jest)
#            iadd += 1
#        else:
#            n_j[Jest] = np.sign(n_j[Jest]) * nf
   
    return n_j, kadd
    

#===============================================================================
def mrc_calc(t, h, ipeak, MRCTYPE=1):
    """
    Calculate the equation parameters of the Master Recession Curve (MRC) of
    the aquifer from the water level time series.
    
    ---- INPUT ----
    h : water level time series in mbgs
    t : time in days
    ipeak: indices where the maxima and minima are located in h
    
    MRCTYPE: MRC equation type    
    
             MODE = 0 -> linear (dh/dt = b)
             MODE = 1 -> exponential (dh/dt = -a*h + b)
    
    """
#===============================================================================
   
    #-------------------------------------------------------- Quality Check ----

    ipeak = np.sort(ipeak)
    
    maxpeak = ipeak[:-1:2]
    minpeak = ipeak[1::2]
    
    dpeak = (h[maxpeak] - h[minpeak]) * -1 # WARNING: Don't forget it is mbgs
    if np.any(dpeak < 0):
        print 'There is a problem with the pair-ditribution of min-max'
        return
    if len(ipeak) == 0:
        print 'No extremum selected'
        return
    
    print; print '---- MRC calculation started ----'; print
    print 'MRCTYPE =', ['Linear', 'Exponential'][MRCTYPE]
    print
    
    # nsegmnt = len(minpeak)
        
    #--------------------------------------------------------- Optimization ----

    tstart = clock()
    
    # If MRCTYPE is 0, then the parameter A is kept to a value of 0 throughout
    # the entire optimization process and only paramter B is optimized.
    
    dt = np.diff(t)
    tolmax = 0.001
    
    A = 0.
    B = np.mean((h[maxpeak] - h[minpeak]) / (t[maxpeak] - t[minpeak]))
    
    hp = calc_synth_hydrograph(A, B, h, dt, ipeak)
    tindx = np.where(~np.isnan(hp))
    
    RMSE = (np.mean((h[tindx] - hp[tindx])**2))**0.5
    print('A = %0.3f ; B= %0.3f; RMSE = %f' % (A, B, RMSE))
    
    # NP: number of parameters
    if MRCTYPE == 0:
        NP = 1 
    elif MRCTYPE ==1:
        NP = 2
    
    while 1:
                    
        #---- Calculating Jacobian Numerically ---- 
        
        hdB = calc_synth_hydrograph(A, B + tolmax, h, dt, ipeak)
        XB = (hdB[tindx] - hp[tindx]) / tolmax
        
        if MRCTYPE == 1:
            hdA = calc_synth_hydrograph(A + tolmax, B, h, dt, ipeak)
            XA = (hdA[tindx] - hp[tindx]) / tolmax
            
            Xt  = np.vstack((XA, XB))
        elif MRCTYPE == 0:
            Xt = XB        
        
        X = Xt.transpose()
                          
        #---- Solving Linear System ----
            
        dh = h[tindx] - hp[tindx]
        XtX = np.dot(Xt, X)                
        Xtdh = np.dot(Xt, dh)

        #---- Scaling ----
        
        C = np.dot(Xt, X) * np.identity(NP)
        for j in range(NP):
            C[j, j] = C[j, j] ** -0.5
        
        Ct = C.transpose()
        Cinv = np.linalg.inv(C)
        
        #---- Constructing right hand side ----

        CtXtdh = np.dot(Ct, Xtdh)
        
        #---- Constructing left hand side ----
        
        CtXtX = np.dot(Ct, XtX)
        CtXtXC = np.dot(CtXtX, C)
        
        m = 0
        while 1: # loop for the Marquardt parameter (m)
            
            #---- Constructing left hand side (continued) ----
            
            CtXtXCImr = CtXtXC + np.identity(NP) * m
            CtXtXCImrCinv = np.dot(CtXtXCImr, Cinv)
                        
            #---- Calculating parameter change vector ----
    
            dr = np.linalg.tensorsolve(CtXtXCImrCinv, CtXtdh, axes=None)
    
            #---- Checking Marquardt condition ----
            
            NUM = np.dot(dr.transpose(), CtXtdh)
            DEN1 = np.dot(dr.transpose(), dr)
            DEN2 = np.dot(CtXtdh.transpose(), CtXtdh)
            
            cos = NUM / (DEN1 * DEN2)**0.5
            if np.abs(cos) < 0.08:
                m = 1.5 * m + 0.001                
            else:
                break
        
#        print(dr)
#        print(CtXtdh)
#        print(CtXtXCImrCinv)
        
        #---- Storing old parameter values ----
        
        Aold = np.copy(A)
        Bold = np.copy(B)
        RMSEold = np.copy(RMSE)
       
        while 1: # Loop for Damping (to prevent overshoot)
            
            #---- Calculating new paramter values ----
            
            if MRCTYPE == 1:
                A = Aold + dr[0]
                B = Bold + dr[1]
            if MRCTYPE == 0:
                B = Bold + dr[0]
        
            #---- Applying parameter bound-constraints ----
            
            A = np.max((A, 0)) # lower bound
        
            #---- Solving for new parameter values ----
        
            hp = calc_synth_hydrograph(A, B, h, dt, ipeak)
            RMSE = (np.mean((h[tindx] - hp[tindx])**2))**0.5
            
            #---- Checking overshoot ----
            
            if (RMSE - RMSEold) > 0.001:
                dr = dr * 0.5
            else:
                break

        print(u'A = %0.3f ; B= %0.3f; RMSE = %f ; Cosθ = %0.3f' 
              % (A, B, RMSE, cos))
    
        #---- Checking tolerance ----
    
        tolA = np.abs(A - Aold)
        tolB = np.abs(B - Bold)
        
        tol = np.max((tolA, tolB))
        
        if tol < tolmax:
            break
    
    tend = clock()
    print
    print('TIME = %0.3f sec'%(tend-tstart))
    print
    print '---- FIN ----'
    print
         
    return A, B, hp, RMSE

#===============================================================================    
def calc_synth_hydrograph(A, B, h, dt, ipeak):
    """
    Compute synthetic hydrograph with a time-forward implicit numerical scheme
    during period where the water level recedes identified by the "ipeak"
    pointers.
    """    
    
#===============================================================================
    
    maxpeak = ipeak[:-1:2] # Time indexes delimiting period where water level
    minpeak = ipeak[1::2]  # recedes.
    
    nsegmnt = len(minpeak) # Number of segments of the time series that were
                           # identified as period where the water level
                           # recedes.
    
    hp = np.ones(len(h)) * np.nan
    
    for i in range(nsegmnt):
        # numerical scheme development in logbook#10 p.79
        
        hp[maxpeak[i]] = h[maxpeak[i]]
        
        for j in range(minpeak[i] - maxpeak[i]):
            
            imax = maxpeak[i]
            
            LUMP1 = (1 - A * dt[imax+j] / 2)
            LUMP2 = B * dt[imax+j]
            LUMP3 = (1 + A * dt[imax+j] / 2) ** -1                    
                
            hp[imax+j+1] = (LUMP1 * hp[imax+j] + LUMP2) * LUMP3
    
    return hp

#===============================================================================    
class SoilProfil():
    """
    zlayer = Position of the layer boundaries in mbgs where 0 is the ground
             surface. There is one more element in zlayer than the total number
             of layer.
    soilName = Soil texture description.
    Sy = Soil specific yield.
    """
#===============================================================================
    
    def __init__(self):
        
        self.zlayer = []
        self.soilName = []
        self.Sy = []
        self.color = []
        
    def load_info(self, filename):    
        
        #---- load soil column info ----
    
        reader = open(filename,'rb')
        reader = csv.reader(reader, delimiter="\t")
        reader = list(reader)
   
        NLayer = len(reader)
        
        self.zlayer = np.empty(NLayer+1).astype(float)
        self.soilName = np.empty(NLayer).astype(str)
        self.Sy = np.empty(NLayer).astype(float)
        self.color = np.empty(NLayer).astype(str)
        
        self.zlayer[0] = 0
        for i in range(NLayer):
            self.zlayer[i+1] = reader[i][0]
            self.soilName[i] = reader[i][1]
            self.Sy[i] = reader[i][2]
            try:
                self.color[i] = reader[i][3]
            except:
                self.color[i] = '#FFFFFF'                
                
        print self.color  
        print self.zlayer


#===============================================================================    
def mrc2rechg(t, ho, A, B, z, Sy, indx):
    """Calculate groundwater recharge from the Master Recession Curve 
       Equation, the water level time series and the soil column description
       in m, using the water-level fluctuation principle."""
#===============================================================================
    
    #---- Check ----
    
    if np.min(ho) < 0:
        print('Water level rise above ground surface. Please check your data.')
        return

#    indx = np.sort(indx)
#    
#    print indx
#    
#    lindx = indx[:-1:2]
#    rindx = indx[1::2]
#    Sy = 0.09
    dz = np.diff(z)
    print dz
    
    dt = np.diff(t)
    rechg = np.zeros(len(dt))
    
#    # for validation only
#    Sy2 = np.mean(Sy)
#    rechg2 = np.zeros(len(dt))
    
    # !!! Do not forget it is mbgs !!!
    
    for i in range(len(dt)):
        
        #--- Calculate projected water level at i+1 ----
        
        LUMP1 = (1 - A * dt[i] / 2)
        LUMP2 = B * dt[i]
        LUMP3 = (1 + A * dt[i] / 2) ** -1
        
        hp = (LUMP1 * ho[i] + LUMP2) * LUMP3
        
        #---- Calculate resulting recharge over dt (See logbook #11, p.23) ----
                
        hup = min(hp, ho[i+1])
        hlo = max(hp, ho[i+1])
                
        iup = np.where(hup >= z)[0][-1]
        ilo = np.where(hlo >= z)[0][-1]
        
        rechg[i] = np.sum(dz[iup:ilo+1] * Sy[iup:ilo+1])        
        rechg[i] -= (z[ilo+1] - hlo) * Sy[ilo]
        rechg[i] -= (hup - z[iup]) * Sy[iup]
        
        rechg[i] *= np.sign(hp - ho[i+1]) # Will be positif in most cases. In
        # theory, it should always be positive, but error in the MRC and noise
        # in the data can cause hp to be above ho in some cases.
                       
#        rechg2[i] = -(ho[i+1] - hp) * Sy2 # Do not forget it is mbgs
    
    print("Recharge = %0.2f m" % np.sum(rechg))
#    print("Recharge2 = %0.2f m" % np.sum(rechg2))
           
    return rechg
    

##===============================================================================    
#class NewFig(QtGui.QWidget):
##===============================================================================
#            
#    def __init__(self, A, B, parent=None):
#        super(NewFig, self).__init__(parent)
#            
#        self.fig = plt.figure()        
#        self.fig_MRC_widget = FigureCanvasQTAgg(self.fig)
#        self.toolbar = NavigationToolbar2QT(self.fig_MRC_widget, self)
#        
#        plt.plot(A, A, '.')
#        
#        grid = QtGui.QGridLayout()
#       
#        row = 0
#        col = 0
#        grid.addWidget(self.fig_MRC_widget, row, col)
#        row += 1
#        grid.addWidget(self.toolbar, row, col)
#        
#        self.setLayout(grid)
#        
#        self.fig_MRC_widget.draw() 
        
                
if __name__ == '__main__':
    
    from hydroprint import WaterlvlData
    from meteo import MeteoObj
    
    app = QtGui.QApplication(argv)   
    instance_1 = WLCalc()
    instance_1.show()
    instance_1.widget_MRCparam.show()
    
    fwaterlvl = 'Files4testing/PO01.xls'
    
    waterLvlObj = WaterlvlData()
    waterLvlObj.load(fwaterlvl)

    water_lvl = waterLvlObj.lvl
    water_lvl = water_lvl[400:1000]

    time = waterLvlObj.time
    time = time[400:1000]
    
    #---- Push info to WLcalc instance ----
    
    instance_1.water_lvl = water_lvl
    instance_1.time = time
    instance_1.soilFilename = waterLvlObj.soilFilename
    
    instance_1.plot_water_levels()
       
    app.exec_() 
