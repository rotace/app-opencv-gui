import copy
import threading

import cv2

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import pyqtgraph.flowchart as pgfc
# extension of pyqtgraph ( = exchange library )
import my_pyqtgraph.flowchart.library.common as pgfclc
# customize of pyqtgraph ( = addition library )
import my_pyqtgraph as mypg


class AbstractCalcNode(pgfclc.CtrlNode):
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

    @staticmethod
    def is_gray(data_in):
        if   len(data_in['image'].shape)==2:
            return True
        else:
            assert data_in['image'].shape[2] == 3
            return False


class CannyNode(AbstractCalcNode):
    nodeName = "Canny"
    uiTemplate = [
        ('min', 'spin', {'value': 100, 'step': 1, 'bounds': [0, None], 'int':True }),
        ('max', 'spin', {'value': 200, 'step': 1, 'bounds': [0, None], 'int':True }),
    ]
    def process(self, data_in, display=True):
        # should shallow copy soon because "data_in" will change maybe
        data_in  = copy.copy(data_in)
        data_out = data_in

        min = self.ctrls['min'].value()
        max = self.ctrls['max'].value()

        data_out['image'] = cv2.Canny(data_in['image'], min, max)
        return {'data_out': data_out}


class CvtColorNode(AbstractCalcNode):
    color_names = ['BGR', 'RGB', 'HSV', 'HLS', 'GRAY']
    cv2_cvt_codes = \
        [[None, cv2.COLOR_BGR2RGB, cv2.COLOR_BGR2HSV, cv2.COLOR_BGR2HLS, cv2.COLOR_BGR2GRAY],
         [cv2.COLOR_RGB2BGR, None, cv2.COLOR_RGB2HSV, cv2.COLOR_RGB2HLS, cv2.COLOR_RGB2GRAY],
         [cv2.COLOR_HSV2BGR, cv2.COLOR_HSV2RGB, None, None, None],
         [cv2.COLOR_HLS2BGR, cv2.COLOR_HLS2RGB, None, None, None],
         [cv2.COLOR_GRAY2BGR, cv2.COLOR_GRAY2RGB, None, None, None]]

    nodeName = "CvtColor"
    uiTemplate = [
        ('type_in',  'combo', {'value': 'BGR', 'values': color_names}),
        ('type_out', 'combo', {'value': 'RGB', 'values': color_names}),
    ]
    
    def process(self, data_in, display=True):
        # should shallow copy soon because "data_in" will change maybe
        data_in  = copy.copy(data_in)
        data_out = data_in

        idx_in  = self.ctrls['type_in' ].currentIndex()
        idx_out = self.ctrls['type_out'].currentIndex()

        if self.is_gray(data_in):
            idx_in = self.color_names.index('GRAY')
        else:
            if idx_in == self.color_names.index('GRAY'):
                idx_in = self.color_names.index('BGR')
        self.ctrls['type_in'].setCurrentIndex(idx_in)

        cv2_cvt_code = self.cv2_cvt_codes[idx_in][idx_out]

        if cv2_cvt_code is not None:
            data_out['image'] = cv2.cvtColor(data_in['image'], cv2_cvt_code)
        else:
            data_out['image'] = data_in['image']
        return {'data_out':data_out}


class ThreshNode(AbstractCalcNode):
    thresh_names = \
        ['BINARY', 'BINARY_INV', 'TRUNC', 'TOZERO', 'TOZERO_INV']
    cv2_thresh_types = \
        [cv2.THRESH_BINARY, cv2.THRESH_BINARY_INV, cv2.THRESH_TRUNC,
         cv2.THRESH_TOZERO, cv2.THRESH_TOZERO_INV]

    nodeName = 'Threshold'
    uiTemplate = [
        ('type',  'combo', {'value': 'BINARY', 'values': thresh_names}),
        ('threshold', 'spin', {'value': 150, 'step': 1, 'bounds': [0, None], 'int':True }),
        ('max_value', 'spin', {'value': 200, 'step': 1, 'bounds': [0, None], 'int':True }),
        ('otsu', 'check', {'checkd': False}),
    ]
    def process(self, data_in, display=True):
        # should shallow copy soon because "data_in" will change maybe
        data_in = copy.copy(data_in)
        data_out = data_in

        thresh_idx = self.ctrls['type' ].currentIndex()
        threshold = self.ctrls['threshold'].value()
        max_value = self.ctrls['max_value'].value()
        has_otsu = self.ctrls['otsu'].isChecked()
        cv2_thresh_type = self.cv2_thresh_types[thresh_idx]

        if has_otsu:
            if self.is_gray(data_in):
                threshold = 0
                cv2_thresh_type = cv2_thresh_type + cv2.THRESH_OTSU
            else:
                return {'data_out':data_out}
        
        _, data_out['image'] = cv2.threshold(data_in['image'], threshold, max_value, cv2_thresh_type)
        return {'data_out':data_out}


class AdaptThreshNode(AbstractCalcNode):
    thresh_names = \
        ['BINARY', 'BINARY_INV', 'TRUNC', 'TOZERO', 'TOZERO_INV']
    cv2_thresh_types = \
        [cv2.THRESH_BINARY, cv2.THRESH_BINARY_INV, cv2.THRESH_TRUNC,
         cv2.THRESH_TOZERO, cv2.THRESH_TOZERO_INV]
    adapt_method_names = \
        ['MEAN_C', 'GAUSSIAN_C']
    cv2_adapt_methods = \
        [cv2.ADAPTIVE_THRESH_MEAN_C, cv2.ADAPTIVE_THRESH_GAUSSIAN_C]

    nodeName = 'AdaptiveThreshold'
    uiTemplate = [
        ('type',  'combo', {'value': 'BINARY', 'values': thresh_names}),
        ('method',  'combo', {'value': 'BINARY', 'values': adapt_method_names}),
        ('max_value', 'spin', {'value': 255, 'step': 1, 'bounds': [0, None], 'int':True }),
        ('block_size', 'spin', {'value': 11, 'step': 1, 'bounds': [0, None], 'int':True }),
        ('parameter', 'spin', {'value': 2, 'step': 1, 'bounds': [None, None] }),
    ]
    def process(self, data_in, display=True):
        # should shallow copy soon because "data_in" will change maybe
        data_in = copy.copy(data_in)
        data_out = data_in

        if not self.is_gray(data_in):
            return {'data_out':data_out}

        thresh_idx = self.ctrls['type' ].currentIndex()
        method_idx = self.ctrls['method'].currentIndex()
        mv = self.ctrls['max_value'].value()
        bs = self.ctrls['block_size'].value()
        p1 = self.ctrls['parameter'].value()
        cv2_tt = self.cv2_thresh_types[thresh_idx]
        cv2_am = self.cv2_adapt_methods[method_idx]
        data_out['image'] = cv2.adaptiveThreshold(data_in['image'], mv, cv2_am, cv2_tt, bs, p1)

        return {'data_out':data_out}


class UnsharpMaskNode(AbstractCalcNode):
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
        library.addNodeType(ThreshNode , [('Process',),])
        library.addNodeType(AdaptThreshNode , [('Process',),])
        library.addNodeType(UnsharpMaskNode , [('Image',), 
                                              ('Submenu_test','submenu2','submenu3')])
    return library