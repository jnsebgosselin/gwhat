# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 00:28:27 2015

@author: jsgosselin
"""

#---- STANDARD LIBRARY IMPORTS ----

import sys

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui

#---- PERSONAL IMPORTS ----

import database as db

class MyQToolBox(QtGui.QWidget):
    
    """
    This custom widget mimick the behavior of QToolBox, but with some variants:
    
    (1) The background of the scrollarea and of its content is automatically
        set to "transparent" with a stylesheet.
    (2) Header consist of QPushButton that have their content left-align
        with a stylesheet.
    (3) Only one tool can be displayed at a time. Unlike the stock QToolBox
        widget however, it is possible to hide all the tools.  It is possible 
        to hide the current displayed tool by clicking on its header.
    (4) The tools that are hidden are marked by right-arrow icon, while the 
        tool that is currently displayed is mark with a down-arrow icon.
        
    It is possible to access any element of this container widget from the
    layout, wich consist in a QGridLayout with only 1 column, like that:
    
        my_tool_box_widget.layout().itemAtPosition(row, 0).widget()
        
    where even rows contains the headers (QPushButton) and the odd rows 
    contains the items that were added with the method "addItem". The last row
    is empty and is used to eat the remaining vertical blank space when
    drawing the widget.
    """
        
    def __init__(self, parent=None):
        super(MyQToolBox, self).__init__(parent)
        
        self.installEventFilter(self)
        
        self.maingrid = QtGui.QGridLayout()
        self.maingrid.setContentsMargins(0, 0, 0, 0)
        
        self.iconDB = db.icons()
        self.currentIndex = -1
        
        self.initUI()
        
    def initUI(self):
         
         self.setLayout(self.maingrid)
       
    def addItem(self, obj, text):
        
        N = self.maingrid.rowCount()
        
        #---- Header ----
        
        button = QtGui.QPushButton()
        button.setText(text)
        button.setIcon(self.iconDB.triangle_right)
        button.clicked.connect(self.header_isClicked)
        button.setStyleSheet("QPushButton {text-align:left;}")
                
        self.maingrid.addWidget(button, N-1, 0)
        
        #---- Item ----
        
        scrollarea = QtGui.QScrollArea()        
        scrollarea.setFrameStyle(0)
        scrollarea.hide()
        scrollarea.setStyleSheet("QScrollArea {background-color:transparent;}")
        scrollarea.setWidgetResizable(True)
        
        obj.setObjectName("myViewport")
        obj.setStyleSheet("#myViewport {background-color:transparent;}") 
        scrollarea.setWidget(obj)
        
        self.maingrid.addWidget(scrollarea, N, 0)        
        self.maingrid.setRowStretch(N+1, 100)
    
    def header_isClicked(self):

        sender = self.sender()
       
        N = self.maingrid.rowCount ()
        for row in range(0, N-1, 2):
            button = self.maingrid.itemAtPosition(row, 0).widget()
            item = self.maingrid.itemAtPosition(row+1, 0).widget()

            if button == sender:
                
                if self.currentIndex == row / 2:
                    button.setIcon(self.iconDB.triangle_right)
                    item.hide()
                    self.currentIndex = -1
                else:
                    button.setIcon(self.iconDB.triangle_down)
                    item.show()
                    self.currentIndex = row / 2
                    
            else:
                button.setIcon(self.iconDB.triangle_right) 
                item.hide()
            
        
if __name__ == '__main__':    
    
    app = QtGui.QApplication(sys.argv) 
    
    instance1 = MyQToolBox()   

    #---- SHOW ----
              
    instance1.show()
    
    qr = instance1.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    instance1.move(qr.topLeft())
        
    sys.exit(app.exec_())