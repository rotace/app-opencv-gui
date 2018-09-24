import cv2
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import pyqtgraph.flowchart as pgfc
# extension of pyqtgraph ( = exchange library )
import my_pyqtgraph.flowchart.library.common as pgfclc
# customize of pyqtgraph ( = addition library )
import my_pyqtgraph as mypg


class AbstractImageProcessNode(pgfclc.CtrlNode):
    """
    Abstract ImageProcess Node
    """
    nodeName = None
    uiTemplate = None
    def __init__(self, name):
        ## Define the input / output terminals available on this node
        terminals = {
            'dataIn': dict(io='in'),    # each terminal needs at least a name and
            'dataOut': dict(io='out'),  # to specify whether it is input or output
        }                              # other more advanced options are available
                                       # as well..
        pgfclc.CtrlNode.__init__(self, name, terminals=terminals)


class CannyNode(AbstractImageProcessNode):
    """
    opencv Canny
    """
    nodeName = "Canny"
    uiTemplate = [
        ('min', 'spin', {'value': 1, 'step': 1, 'bounds': [0, None], 'int':True }),
        ('max', 'spin', {'value': 1, 'step': 1, 'bounds': [0, None], 'int':True }),
    ]
    def process(self, dataIn, display=True):
        # CtrlNode has created self.ctrls, which is a dict containing {ctrlName: widget}
        min = self.ctrls['min'].value()
        max = self.ctrls['max'].value()
        dataOut = cv2.Canny(dataIn, min, max)
        return {'dataOut': dataOut}





class UnsharpMaskNode(AbstractImageProcessNode):
    """Return the input data passed through an unsharp mask."""
    nodeName = "UnsharpMask"
    uiTemplate = [
        ('sigma',  'spin', {'value': 1.0, 'step': 1.0, 'bounds': [0.0, None]}),
        ('strength', 'spin', {'value': 1.0, 'dec': True, 'step': 0.5, 'minStep': 0.01, 'bounds': [0.0, None]}),
    ]
    def process(self, dataIn, display=True):
        # CtrlNode has created self.ctrls, which is a dict containing {ctrlName: widget}
        sigma = self.ctrls['sigma'].value()
        strength = self.ctrls['strength'].value()
        output = dataIn - (strength * pg.gaussianFilter(dataIn, (sigma,sigma)))
        return {'dataOut': output}




def add_image_process_library(library):
    if isinstance( library, pgfc.NodeLibrary.NodeLibrary ):
        library.addNodeType(CannyNode , [('Process',),])
        library.addNodeType(UnsharpMaskNode , [('Image',), 
                                              ('Submenu_test','submenu2','submenu3')])
    return library