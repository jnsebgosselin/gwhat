# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 00:28:27 2015

@author: jsgosselin
"""

#---- STANDARD LIBRARY IMPORTS ----

import sys

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore

#---- PERSONAL IMPORTS ----

import database as db


class MyQErrorMessageBox(QtGui.QMessageBox):
    
    def __init__(self, parent=None):
        super(MyQErrorMessageBox, self).__init__(parent)
        
        self.setIcon(QtGui.QMessageBox.Warning)
        self.setWindowTitle('Error Message')
        self.setWindowIcon(db.icons().WHAT)

#===============================================================================
class MyQNavigationToolbar(QtGui.QWidget):
#===============================================================================
    
    currentContentChanged = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        super(MyQNavigationToolbar, self).__init__(parent)
        
        self.currentIndex = 0 
        self.contentMemory = []
        self.currentContent = ''
        
        self.initUI()
        
    def initUI(self):
        
        iconDB = db.icons()
        styleDB = db.styleUI()
        
        self.btn_goNext = QtGui.QToolButton()
        self.btn_goNext.setIcon(iconDB.go_next)
        self.btn_goNext.setAutoRaise(True)
        self.btn_goNext.setToolTip('Click to go forward.')
        self.btn_goNext.setIconSize(styleDB.iconSize2)
        self.btn_goNext.setEnabled(False)
        
        self.btn_goPrevious = QtGui.QToolButton()
        self.btn_goPrevious.setIcon(iconDB.go_previous)
        self.btn_goPrevious.setAutoRaise(True)
        self.btn_goPrevious.setToolTip('Click to go back.')
        self.btn_goPrevious.setIconSize(styleDB.iconSize2)
        self.btn_goPrevious.setEnabled(False)
        
        self.btn_goLast = QtGui.QToolButton()
        self.btn_goLast.setIcon(iconDB.go_last)
        self.btn_goLast.setAutoRaise(True)
        self.btn_goLast.setToolTip('Click to go last.')
        self.btn_goLast.setIconSize(styleDB.iconSize2)
        self.btn_goLast.setEnabled(False)
        
        self.btn_goFirst = QtGui.QToolButton()
        self.btn_goFirst.setIcon(iconDB.go_first)
        self.btn_goFirst.setAutoRaise(True)
        self.btn_goFirst.setToolTip('Click to go first.')
        self.btn_goFirst.setIconSize(styleDB.iconSize2)
        self.btn_goFirst.setEnabled(False)
        
        goToolbar_grid = QtGui.QGridLayout()
        goToolbar_widg = QtGui.QFrame()
        
        col = 0
        goToolbar_grid.addWidget(self.btn_goFirst, 0, col)
        col += 1
        goToolbar_grid.addWidget(self.btn_goPrevious, 0, col)
        col += 1
        goToolbar_grid.addWidget(self.btn_goNext, 0, col)
        col += 1
        goToolbar_grid.addWidget(self.btn_goLast, 0, col)
        
        goToolbar_grid.setContentsMargins(0, 0, 0, 0) # [L, T, R, B]
        goToolbar_grid.setSpacing(5)
        
        goToolbar_widg.setLayout(goToolbar_grid)
        
        #----------------------------------------------------------- EVENTS ----
        
        self.btn_goLast.clicked.connect(self.button_isClicked)
        self.btn_goFirst.clicked.connect(self.button_isClicked)
        self.btn_goNext.clicked.connect(self.button_isClicked)
        self.btn_goPrevious.clicked.connect(self.button_isClicked)
        
    def button_isClicked(self):
        
         # http://zetcode.com/gui/pysidetutorial/eventsandsignals/
        
        button = self.sender()
       
        if button == self.btn_goFirst:            
            self.currentIndex = 0
            
        elif button == self.btn_goLast:            
            self.currentIndex = len(self.contentMemory) - 1
            
        elif button == self.btn_goPrevious:            
            self.currentIndex += -1
            
        elif button == self.btn_goNext:            
            self.currentIndex += 1
        
        self.currentContent = self.contentMemory(self.currentIndex)
        
        self.update_current_state()        
        
    def update_current_state(self): #===========================================
        
        if len(self.contentMemory) > 1:
        
            if self.currentIndex == (len(self.contentMemory) - 1):
                self.btn_goLast.setEnabled(False)
                self.btn_goNext.setEnabled(False)
                self.btn_goFirst.setEnabled(True)
                self.btn_goPrevious.setEnabled(True)
            elif self.currentIndex == 0:
                self.btn_goLast.setEnabled(True)
                self.btn_goNext.setEnabled(True)
                self.btn_goFirst.setEnabled(False)
                self.btn_goPrevious.setEnabled(False)
            else:
                self.btn_goLast.setEnabled(True)
                self.btn_goNext.setEnabled(True)
                self.btn_goFirst.setEnabled(True)
                self.btn_goPrevious.setEnabled(True)
                
        else:
            
            self.btn_goLast.setEnabled(False)
            self.btn_goNext.setEnabled(False)
            self.btn_goFirst.setEnabled(False)
            self.btn_goPrevious.setEnabled(False)
            
        self.currentContentChanged.emit(self.currentContent)
            
                
    def addContent(self, content):
        
        self.contentMemory.append(content)
        self.currentIndex = len(self.contentMemory) - 1
        self.currentContent = self.contentMemory(self.currentIndex)
        
        self.update_current_state()        
        
    def clear(self):
        
        self.currentIndex = 0
        self.contentMemory = []
        self.currentContent = ''
            
        self.update_current_state()        
           
           
#===============================================================================
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
#===============================================================================
        
    def __init__(self, parent=None):
        super(MyQToolBox, self).__init__(parent)
        
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
    
    instance1.addItem(QtGui.QLabel('Example Toolbox'), 'Tool #1')
    instance1.addItem(QtGui.QLabel('Example Toolbox'), 'Tool #2')
    
    sys.exit(app.exec_())