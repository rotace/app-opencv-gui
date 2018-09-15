# -*- coding: utf-8 -*-
"""
This example demonstrates writing a custom Node subclass for use with flowcharts.

We implement a couple of simple image processing nodes.
"""

import sys

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph.pyqtgraph as pg
import pyqtgraph.pyqtgraph.dockarea as pgda
import pyqtgraph.pyqtgraph.flowchart as pgfc

import imageprocess


class ImageViewNode(pgfc.Node):
    """Node that displays image data in an ImageView widget"""
    nodeName = 'ImageView'
    
    def __init__(self, name):
        self.view = None
        ## Initialize node with only a single input terminal
        pgfc.Node.__init__(self, name, terminals={'dataIn': {'io':'in'}}, allowRemove=False)
        
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
LIBRARY.addNodeType(ImageViewNode, [])


class MainForm(QtWidgets.QMainWindow):
    """
    Main Window
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle('pyqtgraph example: FlowchartCustomNode')
        da = pgda.DockArea()
        self.setCentralWidget(da)
        self.resize(1000, 500)

        # Create Docks
        d1 = pgda.Dock("FlowChart", size=(300, 200))
        d2 = pgda.Dock("ImageView", size=(300, 400))

        da.addDock(d1, "left")
        da.addDock(d2, "right")


        ## Create an empty flowchart with a single input and output
        fc = pgfc.Flowchart(terminals={
            'import_data': {'io': 'in' },
            'export_data': {'io': 'out'}
        })
        fc.setLibrary(LIBRARY)
        d1.addWidget(fc.widget())

        iv = pg.ImageView()
        d2.addWidget(iv)
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
