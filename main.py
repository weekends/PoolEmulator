#!/usr/bin/env python3
# This Python file uses the following encoding: utf-8

import sys
from PyQt5.QtWidgets import (QWidget, QToolTip, QPushButton, QApplication, QDesktopWidget)
from PyQt5.QtGui import QFont
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from functools import partial
import SerialPort


class Example(QWidget):
    _receive_signal = QtCore.pyqtSignal(int, str)

    def __init__(self, max_tables=16):
        super().__init__()
        self.max_tables = max_tables
        self.initUI()

    def initUI(self):
        QToolTip.setFont(QFont('SansSerif', 10))

        self.setToolTip('This is a <b>QWidget</b> widget')
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('PoolClub emulate hardware')
        self.center()

        layout = QtWidgets.QGridLayout()
        layout.setColumnStretch(3, 0)

        self.btns = []
        for i in range(self.max_tables):
            b = QPushButton('Table '+str(i), self)
            self.btns.append([b, False])
            b.clicked.connect(partial(self.send_signal, i))
            layout.addWidget(b)

        self.setLayout(layout)

        btn = QPushButton('Quit', self)
#        btn.setToolTip('This is a <b>QPushButton</b> widget')
        btn.resize(btn.sizeHint())
#        btn.move(50, 50)
        btn.clicked.connect(QtCore.QCoreApplication.instance().quit)
        layout.addWidget(btn, 4, 0, 1, 0)

        self.show()
        self._receive_signal.connect(self.ShowData)

        self.dev = SerialPort.SerialPort('/tmp/dev/serial_port_0')
        self.dev.registerReceivedCallback(self.ShowData)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def send_signal(self, num):
        self._receive_signal.emit(num, "invert")

    def ShowData(self, num, data):
        print('Signsl: ', num, data)
        if (data == 'invert'):
           if (num >= 0 and num <self.max_tables):
               if (self.btns[num][1] is False):
                   self.btns[num][0].setStyleSheet("background-color : yellow")
                   self.btns[num][1] = True
               else:
                   self.btns[num][0].setStyleSheet("background-color : None")
                   self.btns[num][1] = False
        else:
            self.btns[num][0].setStyleSheet(data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
