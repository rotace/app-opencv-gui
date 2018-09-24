# -*- coding: utf-8 -*-
"""
This example demonstrates writing a custom Node subclass for use with flowcharts.

We implement a couple of simple image processing nodes.
"""

import sys

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import pyqtgraph.dockarea as pgda
import pyqtgraph.flowchart as pgfc
import imageprocess as ip

# LIBRARY = pgfc.library.LIBRARY.copy() # start with the default node set
LIBRARY = pgfc.NodeLibrary.NodeLibrary() # start with empty node set
LIBRARY = ip.add_image_process_library(LIBRARY)

class MainForm(QtWidgets.QMainWindow):
    """
    Main Window
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle('pyqtgraph example: FlowchartCustomNode')
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        self.resize(1000, 500)
        layout = QtWidgets.QGridLayout()
        cw.setLayout(layout)

        ## Create FlowChart
        fc = pgfc.Flowchart(terminals={
            'import_data': {'io': 'in' },
            'export_data': {'io': 'out'}
        })
        fc.setLibrary(LIBRARY)
        layout.addWidget(fc.widget(), 0,0)

        ## Create DockArea
        dockarea = pgda.DockArea()
        layout.addWidget(dockarea, 0,1)

        ## initial flowchart setting
        dock1 = pgda.Dock("ImageView", size=(300, 400))
        dockarea.addDock(dock1)
        node1 = fc.createNode('ImageView', pos=(0, -150))
        view1 = node1.getView()
        dock1.addWidget(view1)
        fc.connectTerminals(fc['import_data'], node1['dataIn'])
        fc.connectTerminals(fc['import_data'], fc['export_data'])

        self.fc = fc
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.set_data)
        self.timer.start(1000)

    def set_data(self):
        ## generate random input data
        data = np.random.normal(size=(100,100))
        data = 25 * pg.gaussianFilter(data, (5,5))
        data += np.random.normal(size=(100,100))
        data[40:60, 40:60] += 15.0
        data[30:50, 30:50] += 15.0

        ## Set the raw data as the input value to the flowchart
        self.fc.setInput(import_data=data)


def main():
    """
    Main Function
    """
    app = QtWidgets.QApplication(sys.argv)
    form = MainForm()
    form.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        main()
