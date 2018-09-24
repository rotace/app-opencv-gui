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
import pyqtgraph.flowchart.library.common as pgfclc

import imageprocess


class ImageViewNode(pgfclc.CtrlNode):
    """Node that displays image data in an ImageView widget"""
    nodeName = 'ImageView'
    uiTemplate = [
        ('sigma',  'spin', {'value': 1.0, 'step': 1.0, 'bounds': [0.0, None]}),
        ('strength', 'spin', {'value': 1.0, 'dec': True, 'step': 0.5, 'minStep': 0.01, 'bounds': [0.0, None]}),
    ]
    def __init__(self, name):
        self.view = None
        ## Initialize node with only a single input terminal
        pgfclc.CtrlNode.__init__(self, name, terminals={'dataIn': {'io':'in'}})
        
    def setView(self, view):  ## setView must be called by the program
        self.view = view
        
    def process(self, dataIn, display=True):
        ## if process is called with display=False, then the flowchart is being operated
        ## in batch processing mode, so we should skip displaying to improve performance.
        
        if display and self.view is not None:
            ## the 'data' argument is the value given to the 'data' terminal
            if dataIn is None:
                self.view.setImage(np.zeros((1,1))) # give a blank array to clear the view
            else:
                self.view.setImage(dataIn)


# LIBRARY = pgfc.library.LIBRARY.copy() # start with the default node set
LIBRARY = pgfc.NodeLibrary.NodeLibrary() # start with empty node set
LIBRARY = imageprocess.add_image_process_library(LIBRARY)
LIBRARY.addNodeType(ImageViewNode, []) # unvisible from context menu for not enabling to add


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

        ## Create an empty flowchart with a single input and output
        fc = pgfc.Flowchart(terminals={
            'import_data': {'io': 'in' },
            'export_data': {'io': 'out'}
        })
        fc.setLibrary(LIBRARY)
        layout.addWidget(fc.widget(), 0,0)

        # Create Docks
        # da = pgda.DockArea()
        # layout.addWidget(da, 0,1)

        # d1 = pgda.Dock("FlowChart", size=(300, 200))
        # d2 = pgda.Dock("ImageView", size=(300, 400))
        # d1.hideTitleBar()

        # da.addDock(d1, "left")
        # da.addDock(d2, "right")

        iv = pg.ImageView()
        # d2.addWidget(iv)
        layout.addWidget(iv, 0,1)
        ivNode = fc.createNode('ImageView', pos=(0, -150))
        ivNode.setView(iv)

        fc.connectTerminals(fc['import_data'], ivNode['dataIn'])
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
