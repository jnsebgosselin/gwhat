#!/usr/bin/env python
"""
Copyright 2015 Jean-Sebastien Gosselin

email: jnsebgosselin@gmail.com

This file is part of WHAT (Well Hydrograph Analysis Toolbox). This code was
forked from a code provided in the example classes of the Qt Tookit by
Trolltech AS. Original license is provided below. I removed from the original
code most of the UI elements, added a zooming capability with the mouse wheel, 
and I added the capability to display matplotlib figures.

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

--------------------------------------------------------------------------------

Copyright (C) 2005-2005 Trolltech AS. All rights reserved.

This file is part of the example classes of the Qt Toolkit.
This file may be used under the terms of the GNU General Public
License version 2.0 as published by the Free Software Foundation
and appearing in the file LICENSE.GPL included in the packaging of
this file.  Please review the following information to ensure GNU
General Public Licensing requirements will be met:
http://www.trolltech.com/products/qt/opensource.html

If you are unsure which license is appropriate for your use, please
review the following information:
http://www.trolltech.com/products/qt/licensing.html or contact the
sales department at sales@trolltech.com.

This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
"""

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

#-------------------------------------------------------------------------------
class ImageViewer(QtGui.QWidget):
    """
    This is a PySide widget class to display a bitmap image in a 
    QScrollArea with zooming capability with CTRL + Mouse_wheel.  
    """
#-------------------------------------------------------------------------------

    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
                       
        self.printer = QtGui.QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = QtGui.QLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                      QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.installEventFilter(self)
        
        #---- Scroll Area Set Up ----
        
        self.scrollArea = QtGui.QScrollArea(self)
#        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)
                
        #---- Grid Set Up ----
                
        grid = QtGui.QGridLayout()
               
        grid.addWidget(self.scrollArea, 0, 0)
                
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0) # (Left,Top, Right, Bottom)
        
        self.setLayout(grid)
        self.setWindowTitle("Image Viewer")
        
        #---- Create Initial Image ----
        
        self.figure = plt.figure()
        plt.plot([1, 2, 3, 4], [1, 2, 3, 4], '-b')

        self.figure_widget = FigureCanvasQTAgg(self.figure)
        self.figure_widget.draw()
        
        # http://stackoverflow.com/questions/17676373/
        # python-matplotlib-pyqt-copy-image-to-clipboard
        size = self.figure_widget.size()
        width, height = size.width(), size.height()
        
        imgbuffer = self.figure_widget.buffer_rgba()
        image = QtGui.QImage(imgbuffer, width, height, QtGui.QImage.Format_ARGB32)
            
        self.load_image(image)
        
    def eventFilter(self, widget, event):
        if (event.type() == QtCore.QEvent.Type.Wheel and widget is self.imageLabel):
                               
            # http://stackoverflow.com/questions/8772595/
            # how-to-check-if-a-key-modifier-is-pressed-shift-ctrl-alt
            modifiers = QtGui.QApplication.keyboardModifiers()

            if modifiers == QtCore.Qt.ControlModifier:                
                if event.delta() > 0:
                    self.zoomIn()
                else:
                    self.zoomOut()
                return True
            else:
                return False

        return QtGui.QWidget.eventFilter(self, widget, event)

    def load_image(self, image):        
               
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))
        self.scaleFactor = 1.0
        
        self.imageLabel.adjustSize()

    def zoomIn(self):
        if self.scaleFactor < 3.0:        
            self.scaleImage(1.25)

    def zoomOut(self):
        if self.scaleFactor > 0.333:        
            self.scaleImage(0.8)
                
    def scaleImage(self, factor):
        
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))
                                
#    def normalSize(self):
#        self.imageLabel.adjustSize()
#        self.scaleFactor = 1.0
#
#    def fitToWindow(self):
#        fitToWindow = self.fitToWindowAct.isChecked()
#        self.scrollArea.setWidgetResizable(fitToWindow)
#        if not fitToWindow:
#            self.normalSize()
#
#        self.updateActions()
                                
if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
