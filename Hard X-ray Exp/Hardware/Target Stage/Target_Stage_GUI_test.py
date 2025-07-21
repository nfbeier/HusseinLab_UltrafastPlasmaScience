#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 10:14:56 2025

@author: Christina Strilets
"""
# This is where the main control panel for the hard - xray pannel will be made / tested
# out 
from PyQt5 import QtCore, QtGui, QtWidgets


# First defining and making the user interface
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        # Defining the size of the main window
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(40, 50, 160, 83))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)  
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.InitializeXPSButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.InitializeXPSButton.setObjectName("InitializeXPSButton")
        self.verticalLayout.addWidget(self.InitializeXPSButton)
        
        
        # self.HomeXPSButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        # self.HomeXPSButton.setEnabled(False)
        # self.HomeXPSButton.setObjectName("HomeXPSButton")
        # self.verticalLayout.addWidget(self.HomeXPSButton)
        
        # self.EnableDisableButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        # self.EnableDisableButton.setEnabled(False)
        # self.EnableDisableButton.setDefault(False)
        # self.EnableDisableButton.setObjectName("EnableDisableButton")
        # self.verticalLayout.addWidget(self.EnableDisableButton)
        
        # self.XPSStatus = QtWidgets.QGroupBox(self.centralwidget)
        # self.XPSStatus.setGeometry(QtCore.QRect(40, 150, 120, 80))
        # font = QtGui.QFont()
        # font.setPointSize(10)
        # font.setBold(True)
        # font.setWeight(75)
        # self.XPSStatus.setFont(font)
        # self.XPSStatus.setAutoFillBackground(False)
        # self.XPSStatus.setStyleSheet("")
        # self.XPSStatus.setFlat(False)
        # self.XPSStatus.setCheckable(False)
        # self.XPSStatus.setObjectName("XPSStatus")
        
        # self.XPSStatusLabel = QtWidgets.QLabel(self.XPSStatus)
        # self.XPSStatusLabel.setGeometry(QtCore.QRect(10, 20, 101, 51))
        # font = QtGui.QFont()
        # font.setBold(False)
        # font.setWeight(50)
        # self.XPSStatusLabel.setFont(font)
        # self.XPSStatusLabel.setFocusPolicy(QtCore.Qt.NoFocus)
        # self.XPSStatusLabel.setObjectName("XPSStatusLabel")
        
        # self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.centralwidget)
        # self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(210, 50, 160, 83))
        # self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        # self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        # self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        # self.verticalLayout_2.setObjectName("verticalLayout_2")
        
        # self.MoveForward = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        # self.MoveForward.setEnabled(False)
        # self.MoveForward.setObjectName("MoveForward")
        # self.verticalLayout_2.addWidget(self.MoveForward)
        
        # self.MoveBackward = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        # self.MoveBackward.setEnabled(False)
        # self.MoveBackward.setObjectName("MoveBackward")
        # self.verticalLayout_2.addWidget(self.MoveBackward)
        
        # self.MoveAbsolute = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        # self.MoveAbsolute.setEnabled(False)
        # self.MoveAbsolute.setObjectName("MoveAbsolute")
        # self.verticalLayout_2.addWidget(self.MoveAbsolute)
        
        # self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.centralwidget)
        # self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(210, 140, 160, 131))
        # self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        # self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        # self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        # self.verticalLayout_3.setObjectName("verticalLayout_3")
        # self.label_3 = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        # self.label_3.setObjectName("label_3")
        # self.verticalLayout_3.addWidget(self.label_3)
        
        # self.GroupName = QtWidgets.QComboBox(self.verticalLayoutWidget_3)
        # self.GroupName.setObjectName("GroupName")
        # self.GroupName.addItem("")
        # self.GroupName.addItem("")
        # self.verticalLayout_3.addWidget(self.GroupName)
        
        # self.label = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        # self.label.setObjectName("label")
        # self.verticalLayout_3.addWidget(self.label)
        # self.XPSMovePosition = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        # self.XPSMovePosition.setObjectName("XPSMovePosition")
        # self.verticalLayout_3.addWidget(self.XPSMovePosition)
        # self.label_2 = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        # self.label_2.setObjectName("label_2")
        # self.verticalLayout_3.addWidget(self.label_2)
        # self.XPSPosition = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        # self.XPSPosition.setObjectName("XPSPosition")
        # self.verticalLayout_3.addWidget(self.XPSPosition)
        # self.STOP = QtWidgets.QPushButton(self.centralwidget)
        # self.STOP.setGeometry(QtCore.QRect(40, 240, 161, 31))
        # palette = QtGui.QPalette()
        # brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        # brush.setStyle(QtCore.Qt.SolidPattern)
        # palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        # brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        # brush.setStyle(QtCore.Qt.SolidPattern)
        # palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        # brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        # brush.setStyle(QtCore.Qt.SolidPattern)
        # palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        # self.STOP.setPalette(palette)
        # font = QtGui.QFont()
        # font.setPointSize(14)
        # font.setBold(True)
        # font.setWeight(75)
        # self.STOP.setFont(font)
        # self.STOP.setIconSize(QtCore.QSize(16, 16))
        # self.STOP.setObjectName("STOP")
        # self.verticalLayoutWidget_4 = QtWidgets.QWidget(self.centralwidget)
        # self.verticalLayoutWidget_4.setGeometry(QtCore.QRect(380, 190, 160, 81))
        # self.verticalLayoutWidget_4.setObjectName("verticalLayoutWidget_4")
        # self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_4)
        # self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        # self.verticalLayout_4.setObjectName("verticalLayout_4")
        # self.label_4 = QtWidgets.QLabel(self.verticalLayoutWidget_4)
        # self.label_4.setObjectName("label_4")
        # self.verticalLayout_4.addWidget(self.label_4)
        # self.MinimumTravel = QtWidgets.QLineEdit(self.verticalLayoutWidget_4)
        # self.MinimumTravel.setObjectName("MinimumTravel")
        # self.verticalLayout_4.addWidget(self.MinimumTravel)
        # self.label_5 = QtWidgets.QLabel(self.verticalLayoutWidget_4)
        # self.label_5.setObjectName("label_5")
        # self.verticalLayout_4.addWidget(self.label_5)
        # self.MaximumTravel = QtWidgets.QLineEdit(self.verticalLayoutWidget_4)
        # self.MaximumTravel.setObjectName("MaximumTravel")
        # self.verticalLayout_4.addWidget(self.MaximumTravel)
        # MainWindow.setCentralWidget(self.centralwidget)
        # self.menubar = QtWidgets.QMenuBar(MainWindow)
        # self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        # self.menubar.setObjectName("menubar")
        # self.menuXPS_Control_Panel = QtWidgets.QMenu(self.menubar)
        # self.menuXPS_Control_Panel.setObjectName("menuXPS_Control_Panel")
        # MainWindow.setMenuBar(self.menubar)
        # self.statusbar = QtWidgets.QStatusBar(MainWindow)
        # self.statusbar.setObjectName("statusbar")
        # MainWindow.setStatusBar(self.statusbar)
        # self.menubar.addAction(self.menuXPS_Control_Panel.menuAction())

        # self.retranslateUi(MainWindow)
        # QtCore.QMetaObject.connectSlotsByName(MainWindow)

    # def retranslateUi(self, MainWindow):
    #     _translate = QtCore.QCoreApplication.translate
    #     MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
    #     self.InitializeXPSButton.setText(_translate("MainWindow", "Initialize XPS"))
        # self.HomeXPSButton.setText(_translate("MainWindow", "Home XPS"))
        # self.EnableDisableButton.setText(_translate("MainWindow", "Enable/Disable Motion"))
        # self.XPSStatus.setTitle(_translate("MainWindow", "XPS Status"))
        # self.XPSStatusLabel.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:10pt; color:#ff0000;\">Not Initialized</span></p></body></html>"))
        # self.MoveForward.setText(_translate("MainWindow", "Move Forward"))
        # self.MoveBackward.setText(_translate("MainWindow", "Move Backward"))
        # self.MoveAbsolute.setText(_translate("MainWindow", "Move Absolute"))
        # self.label_3.setText(_translate("MainWindow", "Group Name"))
        # self.GroupName.setItemText(0, _translate("MainWindow", "Group1"))
        # self.GroupName.setItemText(1, _translate("MainWindow", "DelayStage"))
        # self.label.setText(_translate("MainWindow", "XPS Move (mm)"))
        # self.XPSMovePosition.setText(_translate("MainWindow", "0"))
        # self.label_2.setText(_translate("MainWindow", "XPS Position (mm)"))
        # self.XPSPosition.setText(_translate("MainWindow", "0"))
        # self.STOP.setText(_translate("MainWindow", "STOP"))
        # self.label_4.setText(_translate("MainWindow", "Minimum Travel (mm)"))
        # self.MinimumTravel.setText(_translate("MainWindow", "0"))
        # self.label_5.setText(_translate("MainWindow", "Maximum Travel (mm)"))
        # self.MaximumTravel.setText(_translate("MainWindow", "50"))
        # self.menuXPS_Control_Panel.setTitle(_translate("MainWindow", "XPS Control Panel"))









if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
    
    
    
    