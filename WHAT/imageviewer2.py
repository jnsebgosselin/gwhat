# -*- coding: utf-8 -*-
"""
Copyright 2015 Jean-Sebastien Gosselin
email: jnsebgosselin@gmail.com

---- NOTICE ----

This file is part of WHAT (Well Hydrograph Analysis Toolbox). This code was
forked from a code provided in the example classes of the Qt Tookit by
Trolltech AS. Original license is provided below. I removed from the original
code most of the UI elements, added a zooming capability with the mouse wheel, 
and I added the capability to display matplotlib figures.

---- LICENSE ----

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

------------------------------------------------------------------------------

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

from PySide import QtGui, QtCore, QtSvg
import io

#============================================================================     
class MplViewer(QtGui.QFrame):
    def __init__(self, parent=None):
        super(MplViewer, self).__init__(parent)
        
        self.setFrameStyle(QtGui.QFrame.Panel|QtGui.QFrame.Raised)
        self.setLineWidth(2)
        self.setMidLineWidth(1)
        self.setStyleSheet("background-color: white")
        
        self.df = 'png' # display format is png or svg. Default is png.
        
    def load_image(self, mplfig, df='png'): #=================================

        #---------------------------------------------------- figure size ----
        
        bbox = mplfig.get_window_extent()
        self.fwidth  = bbox.width
        self.fheight = bbox.height
        
        #------------------------------------------ save figure to buffer ----
        
        # http://stackoverflow.com/questions/8598673/
        # how-to-save-a-pylab-figure-into-in-memory-file-which-can-be-read
        # -into-pil-image/8598881#8598881
        
        # http://stackoverflow.com/questions/1300908/
        # load-blob-image-data-into-qpixmap
        
        if df == 'svg':
            self.df = 'svg'
            
            fbuffer = io.BytesIO()
            mplfig.savefig(fbuffer, format='svg')
            fbuffer.seek(0)
            img_dta = fbuffer.getvalue()
            
            xmlsr = QtCore.QXmlStreamReader(img_dta)
            self.img = QtSvg.QSvgRenderer(xmlsr)
            
        else:
            self.df = 'png'
            
            base_dpi = mplfig.get_dpi()
            mplfig.dpi = 150
            
            buf, size = mplfig.canvas.print_to_buffer()
            self.img = QtGui.QImage(buf, size[0], size[1],
                                    QtGui.QImage.Format_ARGB32)
            self.img = QtGui.QImage.rgbSwapped(self.img)
            self.img = QtGui.QPixmap(self.img)
            
            mplfig.dpi = base_dpi
            
            # for the io.BytesIO file buffer approach, use the same 
            # code as for svg to get "img_dta", then do:
            # ----
            # img = QtGui.QImage.fromData(img_dta)
            # self.img = QtGui.QPixmap(img)
        
        #-------------------------------------------------------- repaint ----
        
        self.repaint()        
                        
    def paintEvent(self, event):
        super(MplViewer, self).paintEvent(event)
        
        qp = QtGui.QPainter()
        qp.begin(self)
                
        if self.df == 'png':            
            
            # QtGui.QPainter.Antialiasing
            # QtGui.QPainter.TextAntialiasing
            # QtGui.QPainter.SmoothPixmapTransform
            # QtGui.QPainter.HighQualityAntialiasing
            # QtGui.QPainter.NonCosmeticDefaultPen 
            
            qp.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
            
            fw = 4 # frame width
            rect = QtCore.QRect(0 + fw, 0 + fw, self.size().width() - 2*fw,
                                self.size().height() - 2*fw)

            qp.drawPixmap(rect, self.img) 

        elif self.df == 'svg':    
            self.img.render(qp)
        
        qp.end()
        
        
#=============================================================================
class ImageViewer(QtGui.QScrollArea):
    
    """
    This is a PySide widget class to display a matplotlib figure image in a 
    QScrollArea with zooming and panning capability with CTRL + Mouse_wheel
    and Left-click event.
    """

    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        
        self.setWindowTitle('Image Viewer')
        self.setAlignment(QtCore.Qt.AlignCenter)
        
        #---- init. variable ----        
        
        self.scaleFactor = 0
        self.scaleStep = 1.2
        self.pan = False
        
        #---- image container Set Up ----
        
        self.imageCanvas = MplViewer()
                
        self.imageCanvas.installEventFilter(self)
        self.setWidget(self.imageCanvas)
             
    def eventFilter(self, widget, event): #=================================== 
        
        # http://stackoverflow.com/questions/17525608/
        # event-filter-cannot-intercept-wheel-event-from-qscrollarea
        
        # http://stackoverflow.com/questions/20420072/
        # pyside-keypressevent-catching-enter-or-return
        
        # http://stackoverflow.com/questions/19113532/
        # qgraphicsview-zooming-in-and-out-under-mouse-position
        # -using-mouse-wheel

        #----------------------------------------------------------- ZOOM ----
        
        if event.type() == QtCore.QEvent.Type.Wheel:
                               
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
        
        #------------------------------------------------------------ PAN ----
        
        #---- Set ClosedHandCursor ----
        
        elif event.type() == QtCore.QEvent.Type.MouseButtonPress:
                  
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                
                QtGui.QApplication.setOverrideCursor(
                                                    QtCore.Qt.ClosedHandCursor)
                self.pan = True
                self.xclick = event.globalX()
                self.yclick = event.globalY()
        
        #---- Reset Cursor ----

        elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            
            QtGui.QApplication.restoreOverrideCursor()
            self.pan = False
        
        #---- Move  ScrollBar----
        
        elif event.type() == QtCore.QEvent.Type.MouseMove:
            
            if self.pan == True:
                
                dx = self.xclick - event.globalX()
                self.xclick = event.globalX()
                
                dy = self.yclick - event.globalY()
                self.yclick = event.globalY()
                
                scrollBarH = self.horizontalScrollBar()
                scrollBarH.setValue(scrollBarH.value() + dx)
    
                scrollBarV = self.verticalScrollBar()
                scrollBarV.setValue(scrollBarV.value() + dy)

        return QtGui.QWidget.eventFilter(self, widget, event)

    def zoomIn(self):
        if self.scaleFactor < 5:
            self.scaleFactor += 1
            self.scale_image()
            self.adjust_scrollbar(self.scaleStep)

    def zoomOut(self):
        if self.scaleFactor > -3:
            self.scaleFactor -= 1
            self.scale_image()
            self.adjust_scrollbar(1/self.scaleStep)
                
    def scale_image(self):
        
        new_width = int(self.imageCanvas.fwidth * 
                        self.scaleStep ** self.scaleFactor)
        new_height = int(self.imageCanvas.fheight * 
                         self.scaleStep ** self.scaleFactor)

        self.imageCanvas.setFixedSize(new_width, new_height)
       
    def load_image(self, mplfig, df='png'):
        self.imageCanvas.load_image(mplfig, df)
        self.scale_image()
        
    def reset_original_image(self):
        self.scaleFactor = 0
        self.scale_image()

    def adjust_scrollbar(self, f):
        
        #---- Adjust HScrollBar ----
        
        hb = self.horizontalScrollBar()
        hb.setValue(int(f * hb.value() + ((f - 1) * hb.pageStep()/2)))
                                
        #---- Adjust VScrollBar ----
                                
        vb = self.verticalScrollBar()                        
        vb.setValue(int(f * vb.value() + ((f - 1) * vb.pageStep()/2)))
                                
                                
if __name__ == '__main__':

    import sys
    import matplotlib.pyplot as plt
    import numpy as np

    app = QtGui.QApplication(sys.argv)
    
    #---------------------------------------------- generate a mpl figure ----
    
    #---- generate data ----
    
    N = 50
    x = np.random.rand(N)
    y = np.random.rand(N)
    colors = np.random.rand(N)
    area = np.pi * (15 * np.random.rand(N)) ** 2
    
    #---- setup figure and plot data ----
    
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('white')
    
    ax.scatter(x, y, s=area, c=colors, alpha=0.5)
    plt.tight_layout()
    
    #------------------------------------------------------- image viewer ----
    
    imageViewer = ImageViewer()
    imageViewer.show()
    
    bbox = fig.get_window_extent()  
    imageViewer.resize(bbox.width*1.2, bbox.height*1.2)
    
    imageViewer.load_image(fig, 'png')
      
    sys.exit(app.exec_())
