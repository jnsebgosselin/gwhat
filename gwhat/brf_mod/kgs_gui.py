# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox)..

GWHAT is free software: you can redistribute it and/or modify
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

from PyQt5.QtCore import pyqtProperty
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QLabel, QDateTimeEdit, QCheckBox, QPushButton,
                             QApplication, QDialog, QSpinBox, QAbstractSpinBox,
                             QGridLayout, QDoubleSpinBox, QFrame, QWidget)

from xlrd import xldate_as_tuple
from xlrd.xldate import xldate_from_date_tuple
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

import gwhat.common.widgets as myqt
from gwhat.brf_mod.kgs_plot import BRFFigure
from gwhat.common import IconDB, StyleDB, QToolButtonNormal, QToolButtonSmall
from gwhat import brf_mod as bm

mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Arial']})


class BRFManager(myqt.QFrameLayout):
    def __init__(self, wldset=None, parent=None):
        super(BRFManager, self).__init__(parent)

        self.viewer = BRFViewer(wldset, parent)
        self.__initGUI__()

    def __initGUI__(self):
        self.setContentsMargins(10, 10, 10, 10)

        self._bplag = {}
        self._bplag['label'] = QLabel('BP Lags Nbr:')
        self._bplag['widget'] = myqt.QDoubleSpinBox(100, 0)
        self._bplag['widget'].setRange(1, 9999)
        self._bplag['widget'].setValue(300)
        self._bplag['widget'].setKeyboardTracking(True)

        self._etlag = {}
        self._etlag['label'] = QLabel('ET Lags Nbr:')
        self._etlag['widget'] = myqt.QDoubleSpinBox(300, 0)
        self._etlag['widget'].setRange(-1, 9999)
        self._etlag['widget'].setValue(300)
        self._etlag['widget'].setKeyboardTracking(True)

        # ---- BRF Data Range ----

        self._datastart = QDateTimeEdit()
        self._datastart.setCalendarPopup(True)
        self._datastart.setDisplayFormat('dd/MM/yyyy')

        self._dataend = QDateTimeEdit()
        self._dataend.setCalendarPopup(True)
        self._dataend.setDisplayFormat('dd/MM/yyyy')

        self.btn_seldata = QToolButtonSmall(IconDB().select_range)
        self.btn_seldata.clicked.connect(self.get_datarange)

        # ---- Detrend and Correct Options ----

        self._detrend = QCheckBox('Detrend')
        self._detrend.setCheckState(Qt.Checked)

        self._correct = QCheckBox('Correct WL')
        self._correct.setEnabled(False)

        # -------------------------------------------------------- Toolbar ----

        btn_comp = QPushButton('Compute BRF')
        btn_comp.clicked.connect(self.calc_brf)
        btn_comp.setFocusPolicy(Qt.NoFocus)

        btn_show = QToolButtonSmall(IconDB().search)
        btn_show.clicked.connect(self.viewer.show)

        # ---- Layout ----

        tbar = myqt.QFrameLayout()
        tbar.addWidget(btn_comp, 0, 0)
        tbar.addWidget(btn_show, 0, 1)
        tbar.setColumnStretch(0, 100)

        # ---------------------------------------------------- Main Layout ----

        # ---- Layout ----

        row = 0
        self.addWidget(self._bplag['label'], row, 0)
        self.addWidget(self._bplag['widget'], row, 1)
        row += 1
        self.addWidget(self._etlag['label'], row, 0)
        self.addWidget(self._etlag['widget'], row, 1)
        row += 1
        self.setRowMinimumHeight(row, 15)
        row += 1
        self.addWidget(QLabel('BRF Start :'), row, 0)
        self.addWidget(self._datastart, row, 1)
        self.addWidget(self.btn_seldata, row, 2)
        row += 1
        self.addWidget(QLabel('BRF End :'), row, 0)
        self.addWidget(self._dataend, row, 1)
        row += 1
        self.setRowMinimumHeight(row, 15)
        row += 1
        self.addWidget(self._detrend, row, 0, 1, 2)
        row += 1
        self.addWidget(self._correct, row, 0, 1, 2)
        row += 1
        self.setRowMinimumHeight(row, 5)
        self.setRowStretch(row, 100)
        row += 1
        self.addWidget(tbar, row, 0, 1, 3)

        self.setColumnStretch(self.columnCount(), 100)

    # =========================================================================

    @property
    def lagBP(self):
        return self._bplag['widget'].value()

    @property
    def lagET(self):
        return self._etlag['widget'].value()

    @property
    def detrend(self):
        if self._detrend.checkState():
            return 'Yes'
        else:
            return 'No'

    @property
    def correct_WL(self):
        return 'No'

    @property
    def brfperiod(self):
        y, m, d = self._datastart.date().getDate()
        dstart = xldate_from_date_tuple((y, m, d), 0)

        y, m, d = self._dataend.date().getDate()
        dend = xldate_from_date_tuple((y, m, d), 0)

        return (dstart, dend)

    # =========================================================================

    def set_wldset(self, wldset):
        self.wldset = wldset
        self.viewer.set_wldset(wldset)
        if wldset is None:
            self.setEnabled(False)
        else:
            self.setEnabled(True)

            date_start, date_end = self.set_datarange(
                    self.wldset['Time'][[0, -1]])
            self._datastart.setMinimumDate(date_start)
            self._dataend.setMaximumDate(date_end)

    # =========================================================================

    def get_datarange(self):
        child = self
        while True:
            try:
                child.parent().raise_()
            except:
                break
            else:
                child = child.parent()

    def set_datarange(self, times):
        date_start = xldate_as_tuple(times[0], 0)
        date_start = QDate(date_start[0], date_start[1], date_start[2])
        self._datastart.setDate(date_start)

        date_end = xldate_as_tuple(times[1], 0)
        date_end = QDate(date_end[0], date_end[1], date_end[2])
        self._dataend.setDate(date_end)

        return date_start, date_end

    # =========================================================================

    def calc_brf(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        print('calculating BRF')
        well = self.wldset['Well']

        t1 = min(self.brfperiod)
        i1 = np.where(self.wldset['Time'] >= t1)[0][0]

        t2 = max(self.brfperiod)
        i2 = np.where(self.wldset['Time'] <= t2)[0][-1]

        time = np.copy(self.wldset['Time'][i1:i2+1])
        wl = np.copy(self.wldset['WL'][i1:i2+1])
        bp = np.copy(self.wldset['BP'][i1:i2+1])
        et = np.copy(self.wldset['ET'][i1:i2+1])
        if len(et) == 0:
            et = np.zeros(len(wl))

        lagBP = self.lagBP
        lagET = self.lagET
        detrend = self.detrend
        correct = self.correct_WL

        dt = np.min(np.diff(time))
        tc = np.arange(t1, t2+dt/2, dt)
        if len(tc) != len(time):
            print('Filling gaps in data with linear interpolation.')
            indx = np.where(~np.isnan(wl))[0]
            wl = np.interp(tc, time[indx], wl[indx])

            indx = np.where(~np.isnan(bp))[0]
            bp = np.interp(tc, time[indx], bp[indx])

            indx = np.where(~np.isnan(et))[0]
            et = np.interp(tc, time[indx], et[indx])

            time = tc

        bm.produce_BRFInputtxt(well, time, wl, bp, et)
        msg = 'Not enough data. Try enlarging the selected period'
        msg += ' or reduce the number of BP and ET lags.'
        if lagBP >= len(time) or lagET >= len(time):
            QApplication.restoreOverrideCursor()
            self.emit_warning(msg)
            return

        bm.produce_par_file(lagBP, lagET, detrend, correct)
        bm.run_kgsbrf()

        # ---- Save BRF results ----

        try:
            lag, A, err = bm.read_BRFOutput()
            date_start = self._datastart.date().getDate()
            date_end = self._dataend.date().getDate()
            self.wldset.save_brf(lag, A, err, date_start, date_end)
            self.viewer.new_brf_added()
            self.viewer.show()

            QApplication.restoreOverrideCursor()
        except:
            QApplication.restoreOverrideCursor()
            self.emit_warning(msg)
            return


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class BRFViewer(QWidget):

    def __init__(self, wldset=None, parent=None):
        super(BRFViewer, self).__init__(parent)

        self.setWindowTitle('BRF Viewer')
        self.setWindowIcon(IconDB().master)
        self.setWindowFlags(Qt.Window |
                            Qt.WindowCloseButtonHint)

        self.__initGUI__()
        self.set_wldset(wldset)

    def __initGUI__(self):

        # -------------------------------------------------------- Toolbar ----

        self.btn_del = QToolButtonNormal(IconDB().clear_search)
        self.btn_del.setToolTip('Delete current BRF results')
        self.btn_del.clicked.connect(self.del_brf)

        btn_save = QToolButtonNormal(IconDB().save)
        btn_save.setToolTip('Save current BRF graph...')

        self.btn_setp = QToolButtonNormal(IconDB().page_setup)
        self.btn_setp.setToolTip('Show graph layout parameters...')
        self.btn_setp.clicked.connect(self.toggle_graphpannel)

        # ---- Navigator ----

        self.btn_prev = QToolButtonNormal(IconDB().go_previous)
        self.btn_prev.clicked.connect(self.navigate_brf)

        self.btn_next = QToolButtonNormal(IconDB().go_next)
        self.btn_next.clicked.connect(self.navigate_brf)

        self.current_brf = QSpinBox()
        self.current_brf.setRange(0, 99)
        self.current_brf.setAlignment(Qt.AlignCenter)
        self.current_brf.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.current_brf.setCorrectionMode(
                QAbstractSpinBox.CorrectToNearestValue)
        self.current_brf.valueChanged.connect(self.navigate_brf)
        self.current_brf.setValue(0)

        self.total_brf = QLabel('/ 0')

        # ---- Layout ----

        self.tbar = myqt.QFrameLayout()

        buttons = [btn_save, self.btn_del,
                   self.btn_prev, self.current_brf, self.total_brf,
                   self.btn_next, self.btn_setp]

        for btn in buttons:
            self.tbar.addWidget(btn, 1, self.tbar.columnCount())

        row = self.tbar.columnCount()
        self.tbar.addWidget(myqt.HSep(), 0, 0, 1, row+1)
        self.tbar.setColumnStretch(row, 100)
        self.tbar.setContentsMargins(10, 0, 10, 10)  # (l, t, r, b)

        # -------------------------------------------------- Graph Options ----

        self._errorbar = QCheckBox('Show error bars')
        self._errorbar.setCheckState(Qt.Checked)
        self._errorbar.stateChanged.connect(self.plot_brf)

        self._drawline = QCheckBox('Draw line')
        self._drawline.setCheckState(Qt.Unchecked)
        self._drawline.stateChanged.connect(self.plot_brf)

        self._markersize = {}
        self._markersize['label'] = QLabel('Marker size :')
        self._markersize['widget'] = QSpinBox()
        self._markersize['widget'].setValue(5)
        self._markersize['widget'].setRange(0, 25)
        self._markersize['widget'].valueChanged.connect(self.plot_brf)

        # ---- axis limits ----

        axlayout = QGridLayout()
        axlayout.addWidget(QLabel('y-axis limits:'), 0, 0, 1, 2)
        axlayout.addWidget(QLabel('   Minimum :'), 1, 0)
        axlayout.addWidget(QLabel('   Maximum :'), 2, 0)
        axlayout.addWidget(QLabel('   Auto :'), 3, 0)

        self._ylim = {}
        self._ylim['min'] = QDoubleSpinBox()
        self._ylim['min'].setValue(0)
        self._ylim['min'].setDecimals(1)
        self._ylim['min'].setSingleStep(0.1)
        self._ylim['min'].setRange(-10, 10)
        self._ylim['min'].setEnabled(True)
        self._ylim['min'].valueChanged.connect(self.plot_brf)

        self._ylim['max'] = QDoubleSpinBox()
        self._ylim['max'].setValue(1)
        self._ylim['max'].setDecimals(1)
        self._ylim['max'].setSingleStep(0.1)
        self._ylim['max'].setRange(-10, 10)
        self._ylim['max'].setEnabled(True)
        self._ylim['max'].valueChanged.connect(self.plot_brf)

        self._ylim['auto'] = QCheckBox('')
        self._ylim['auto'].setCheckState(Qt.Unchecked)
        self._ylim['auto'].stateChanged.connect(self.xlimModeChanged)

        axlayout.addWidget(self._ylim['min'], 1, 1)
        axlayout.addWidget(self._ylim['max'], 2, 1)
        axlayout.addWidget(self._ylim['auto'], 3, 1)

        axlayout.setColumnStretch(3, 100)
        axlayout.setContentsMargins(0, 0, 0, 0)  # (left, top, right, bottom)

        # ---- Layout ----

        self.graph_pan = myqt.QFrameLayout()
        self.graph_pan.setContentsMargins(10, 0, 10, 0)  # (l, t, r, b)
        self.graph_pan.setVisible(False)

        row = 0
        self.graph_pan.addWidget(self._errorbar, row, 1, 1, 2)
        row += 1
        self.graph_pan.addWidget(self._drawline, row, 1, 1, 2)
        row += 1
        self.graph_pan.addWidget(self._markersize['label'], row, 1)
        self.graph_pan.addWidget(self._markersize['widget'], row, 2)
        row += 1
        self.graph_pan.addWidget(myqt.HSep(), row, 1, 1, 2)
        row += 1
        self.graph_pan.addLayout(axlayout, row, 1, 1, 2)
        row += 1
        self.graph_pan.setRowMinimumHeight(row, 15)
        self.graph_pan.setRowStretch(row, 100)

        # ---------------------------------------------------------- Graph ----

        self.fig_frame = QFrame()
        self.fig_frame.setFrameStyle(StyleDB().frame)
        self.fig_frame.setObjectName("figframe")
        self.fig_frame.setStyleSheet("#figframe {background-color:white;}")

        self.brf_canvas = FigureCanvasQTAgg(BRFFigure())

        fflay = QGridLayout(self.fig_frame)
        fflay.setContentsMargins(0, 0, 0, 0)   # (left, top, right, bottom)
        fflay.addWidget(self.tbar, 1, 0)
        fflay.addWidget(self.brf_canvas, 0, 0)

        # ---------------------------------------------------- Main Layout ----

        ml = QGridLayout(self)

        ml.addWidget(self.fig_frame, 0, 2)
        ml.addWidget(self.graph_pan, 0, 3)

        ml.setColumnStretch(1, 100)

    # =========================================================================

    def set_wldset(self, wldset):
        self.wldset = wldset
        if wldset is None:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            self.update_brfnavigate_state()

    # ======================================================= Graph Panel  ====

    def toggle_graphpannel(self):
        if self.graph_pan.isVisible() is True:                     # Hide panel
            self.graph_pan.setVisible(False)
            self.btn_setp.setAutoRaise(True)
            self.btn_setp.setToolTip('Show graph layout parameters...')

            w = self.size().width() - self.graph_pan.size().width()
            self.setFixedWidth(w)
        else:                                                      # Show panel
            self.graph_pan.setVisible(True)
            self.btn_setp.setAutoRaise(False)
            self.btn_setp.setToolTip('Hide graph layout parameters...')

            w = self.size().width() + self.graph_pan.size().width()
            self.setFixedWidth(w)

    # =========================================================================

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
        index = self.current_brf.value()-1
        name = self.wldset.get_brfAt(index)
        self.wldset.del_brf(name)
        self.update_brfnavigate_state()

    def new_brf_added(self):
        self.current_brf.setMaximum(self.wldset.brf_count())
        self.current_brf.setValue(self.wldset.brf_count())
        self.update_brfnavigate_state()

    def update_brfnavigate_state(self):
        count = self.wldset.brf_count()
        self.total_brf.setText('/ %d' % count)

        self.current_brf.setMinimum(min(count, 1))
        self.current_brf.setMaximum(count)
        curnt = self.current_brf.value()

        self.tbar.setEnabled(count > 0)
        self.btn_prev.setEnabled(curnt > 1)
        self.btn_next.setEnabled(curnt < count)
        self.btn_del.setEnabled(count > 0)

        self.plot_brf()

    # =========================================================================

    def xlimModeChanged(self, state):
        if state == 2:
            self._ylim['min'].setEnabled(False)
            self._ylim['max'].setEnabled(False)
        else:
            self._ylim['min'].setEnabled(True)
            self._ylim['max'].setEnabled(True)
        self.plot_brf()

    # =========================================================================

    @property
    def ymin(self):
        if self._ylim['auto'].checkState() == Qt.Checked:
            return None
        else:
            return self._ylim['min'].value()

    @property
    def ymax(self):
        if self._ylim['auto'].checkState() == Qt.Checked:
            return None
        else:
            return self._ylim['max'].value()

    @property
    def show_ebar(self):
        if self._errorbar.checkState() == Qt.Checked:
            return True
        else:
            return False

    @property
    def draw_line(self):
        if self._drawline.checkState() == Qt.Checked:
            return True
        else:
            return False

    @property
    def markersize(self):
        return self._markersize['widget'].value()

    # -------------------------------------------------------------------------

    def plot_brf(self):
        if self.wldset.brf_count() == 0:
            self.brf_canvas.figure.empty_BRF()
        else:
            name = self.wldset.get_brfAt(self.current_brf.value()-1)
            lag, A, err, date_start, date_end = self.wldset.get_brf(name)
            well = self.wldset['Well']

            if self.show_ebar is False:
                err = []
            msize = self.markersize
            draw_line = self.draw_line

            ymin = self.ymin
            ymax = self.ymax

            date0 = '%02d/%02d/%04d' % (date_start[2],
                                        date_start[1],
                                        date_start[0])

            date1 = '%02d/%02d/%04d' % (date_end[2],
                                        date_end[1],
                                        date_end[0])

            self.brf_canvas.figure.plot_BRF(lag, A, err, date0, date1, well,
                                            msize, draw_line, [ymin, ymax])

        self.brf_canvas.draw()

    # =========================================================================

    def show(self):
        super(BRFViewer, self).show()
        self.fig_frame.setFixedSize(self.fig_frame.size())
        self.setFixedSize(self.size())

        self.raise_()
        if self.windowState() == Qt.WindowMinimized:
            # Window is minimised. Restore it.
            self.setWindowState(Qt.WindowNoState)


# ---- if __name__ == "__main__":

if __name__ == "__main__":
    import gwhat.projet.reader_projet as prd
    import sys
    projet = prd.ProjetReader('C:/Users/jsgosselin/OneDrive/Research/'
                              'PostDoc - MDDELCC/Outils/BRF MontEst/'
                              'BRF MontEst.what')
    wldset = projet.get_wldset(projet.wldsets[1])

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setPointSize(11)
    ft.setFamily('Segoe UI')
    app.setFont(ft)

    brfwin = BRFManager(None)
    brfwin.show()
    brfwin.set_wldset(wldset)

    sys.exit(app.exec_())

#    plt.close('all')
    # produce_par_file()
    # run_kgsbrf()
    # load_BRFOutput(show_ebar=True, msize=5, draw_line=False)
#    plt.show()
