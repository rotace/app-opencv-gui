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
            'data_in' : dict(io='in'),   # each terminal needs at least a name and
            'data_out': dict(io='out'),  # to specify whether it is input or output
        }                              # other more advanced options are available
                                       # as well..
        pgfclc.CtrlNode.__init__(self, name, terminals=terminals)


class CannyNode(AbstractImageProcessNode):
    nodeName = "Canny"
    uiTemplate = [
        ('min', 'spin', {'value': 100, 'step': 1, 'bounds': [0, None], 'int':True }),
        ('max', 'spin', {'value': 200, 'step': 1, 'bounds': [0, None], 'int':True }),
    ]
    def process(self, data_in, display=True):
        min = self.ctrls['min'].value()
        max = self.ctrls['max'].value()
        data_out = data_in
        data_out['image'] = cv2.Canny(data_in['image'], min, max)
        return {'data_out': data_out}


class CvtColorNode(AbstractImageProcessNode):
    code_names = ['BGR', 'RGB', 'HSV', 'HLS', 'GRAY']
    nodeName = "CvtColor"
    uiTemplate = [
        (
            'type_in', 'combo',
            {
                'value': 'BGR',
                'values': code_names
            }
        ),(
            'type_out', 'combo',
            {
                'value': 'RGB',
                'values': code_names
            }
        )
    ]
    cv2_cvt_codes = \
        [[None, cv2.COLOR_BGR2RGB, cv2.COLOR_BGR2HSV, cv2.COLOR_BGR2HLS, cv2.COLOR_BGR2GRAY],
         [cv2.COLOR_RGB2BGR, None, cv2.COLOR_RGB2HSV, cv2.COLOR_RGB2HLS, cv2.COLOR_RGB2GRAY],
         [cv2.COLOR_HSV2BGR, cv2.COLOR_HSV2RGB, None, None, None],
         [cv2.COLOR_HLS2BGR, cv2.COLOR_HLS2RGB, None, None, None],
         [cv2.COLOR_GRAY2BGR, cv2.COLOR_GRAY2RGB, None, None, None]]
    
    def process(self, data_in, display=True):
        idx_in  = self.ctrls['type_in' ].currentIndex()
        idx_out = self.ctrls['type_out'].currentIndex()
        data_out = data_in
        idx_in  = self.correct_index(idx_in, len(data_in['image'].shape)==2)
        cv2_cvt_code = self.cv2_cvt_codes[idx_in][idx_out]
        if cv2_cvt_code is not None:
            data_out['image'] = cv2.cvtColor(data_in['image'], cv2_cvt_code)
        return {'data_out':data_out}
    
    @classmethod
    def correct_index(cls, idx, is_gray=True):
        if is_gray:
            idx = len(cls.code_names)-1
        elif idx == len(cls.code_names)-1:
            idx = 0
        return idx



class UnsharpMaskNode(AbstractImageProcessNode):
    """Return the input data passed through an unsharp mask."""
    nodeName = "UnsharpMask"
    uiTemplate = [
        ('sigma',  'spin', {'value': 1.0, 'step': 1.0, 'bounds': [0.0, None]}),
        ('strength', 'spin', {'value': 1.0, 'dec': True, 'step': 0.5, 'minStep': 0.01, 'bounds': [0.0, None]}),
    ]
    def process(self, data_in, display=True):
        # CtrlNode has created self.ctrls, which is a dict containing {ctrlName: widget}
        sigma = self.ctrls['sigma'].value()
        strength = self.ctrls['strength'].value()
        data_out = data_in - (strength * pg.gaussianFilter(data_in, (sigma,sigma)))
        return {'data_out': data_out}




def add_library(library):
    if isinstance( library, pgfc.NodeLibrary.NodeLibrary ):
        library.addNodeType(CannyNode , [('Process',),])
        library.addNodeType(CvtColorNode , [('Process',),])
        library.addNodeType(UnsharpMaskNode , [('Image',), 
                                              ('Submenu_test','submenu2','submenu3')])
    return library