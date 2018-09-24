from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import pyqtgraph.flowchart as pgfc
import pyqtgraph.dockarea as pgda
import my_pyqtgraph.flowchart.library.common as pgfclc


class SubWindow(QtWidgets.QDialog):
    def __init__(self, parent=None, child=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.setModal(False)

        if child is not None:
            layout.addWidget(child)


class ImageViewNode(pgfclc.CtrlNode):
    """Node that displays image data in an ImageView widget"""
    nodeName = 'ImageView'
    uiTemplate = [
        ('view',  'button', {}),
    ]
    def __init__(self, name):
        self.view = pg.ImageView()
        ## Initialize node with only a single input terminal
        pgfclc.CtrlNode.__init__(self, name, terminals={'dataIn': {'io':'in'}})

        self.button = self.ctrls['view']
        self.button.setText('open view')
        self.button.clicked.connect(self.display)

        # Create Docks
        self.dockarea = pgda.DockArea()        
        self.dock = pgda.Dock(self.view.name, size=(300, 400))
        self.dock.addWidget(self.view)
        self.dockarea.addDock(self.dock)

    def display(self):
        subWindow = SubWindow(parent=self.ctrlWidget(), child=self.dockarea)
        subWindow.show()
        
    def getView(self):
        # disable button
        self.button.setEnabled(False)
        self.button.setText('see right window')
        return self.view
        
    def process(self, dataIn, display=True):
        ## if process is called with display=False, then the flowchart is being operated
        ## in batch processing mode, so we should skip displaying to improve performance.
        
        if display and self.view is not None:
            ## the 'data' argument is the value given to the 'data' terminal
            if dataIn is None:
                self.view.setImage(np.zeros((1,1))) # give a blank array to clear the view
            else:
                self.view.setImage(dataIn)


class UnsharpMaskNode(pgfclc.CtrlNode):
    """Return the input data passed through an unsharp mask."""
    nodeName = "UnsharpMask"
    uiTemplate = [
        ('sigma',  'spin', {'value': 1.0, 'step': 1.0, 'bounds': [0.0, None]}),
        ('strength', 'spin', {'value': 1.0, 'dec': True, 'step': 0.5, 'minStep': 0.01, 'bounds': [0.0, None]}),
    ]
    def __init__(self, name):
        ## Define the input / output terminals available on this node
        terminals = {
            'dataIn': dict(io='in'),    # each terminal needs at least a name and
            'dataOut': dict(io='out'),  # to specify whether it is input or output
        }                              # other more advanced options are available
                                       # as well..
        
        pgfclc.CtrlNode.__init__(self, name, terminals=terminals)
        
    def process(self, dataIn, display=True):
        # CtrlNode has created self.ctrls, which is a dict containing {ctrlName: widget}
        sigma = self.ctrls['sigma'].value()
        strength = self.ctrls['strength'].value()
        output = dataIn - (strength * pg.gaussianFilter(dataIn, (sigma,sigma)))
        return {'dataOut': output}


def add_image_process_library(library):
    if isinstance( library, pgfc.NodeLibrary.NodeLibrary ):
        library.addNodeType(ImageViewNode   , [('Image',),])
        library.addNodeType(UnsharpMaskNode , [('Image',), 
                                              ('Submenu_test','submenu2','submenu3')])
    return library