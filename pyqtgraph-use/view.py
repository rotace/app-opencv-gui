from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import pyqtgraph.flowchart as pgfc
import pyqtgraph.dockarea as pgda
# extension of pyqtgraph ( = exchange library )
import my_pyqtgraph.flowchart.library.common as pgfclc
# customize of pyqtgraph ( = addition library )
import my_pyqtgraph as mypg


class SubWindow(QtWidgets.QDialog):
    def __init__(self, parent=None, child=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.setModal(False)

        if child is not None:
            layout.addWidget(child)


class AbstractViewNode(pgfclc.CtrlNode):
    """
    Abstract View Node
    This is Node that displays image data in an View widget
    """
    nodeName = 'AbstractView'
    uiTemplate = [
        ('view',  'button', {}),
    ]
    def __init__(self, name):
        pgfclc.CtrlNode.__init__(self, name, terminals={'dataIn': {'io':'in'}})

        self.view = None
        self.sub_window = None

        # Create Button
        self.button = self.ctrls['view']
        self.button.setText('open view')
        self.button.clicked.connect(self._display)

        # Create Dock
        self.dockarea = pgda.DockArea()        
        self.dock = pgda.Dock(self.name(), size=(300, 400))
        self.dockarea.addDock(self.dock)

    def _display(self):
        if self.sub_window is None:
            self.sub_window = SubWindow(parent=self.ctrlWidget(), child=self.dockarea)
            self.sub_window.show()
        elif self.sub_window.isHidden():
            self.sub_window.show()
        else:
            self.sub_window.hide()

    def _setView(self, view):
        self.view = view
        self.dock.addWidget(view)

    def _getView(self):
        return self.view
        
    def getDock(self):
        # disable button and give dock instance to external widget
        self.button.setEnabled(False)
        self.button.setText('see right window')
        return self.dock



class ImageViewNode(AbstractViewNode):
    """
    Node that displays image data in an ImageView widget
    """
    nodeName = 'ImageView'
    uiTemplate = [
        ('view',  'button', {}),
    ]
    def __init__(self, name):
        AbstractViewNode.__init__(self, name)

        if False:
            ## pyqtgraph's ImageView
            self.image_view = pg.ImageView()
        else:
            ## my_pyqtgraph's  ImageView
            self.image_view = mypg.ImageView()

        self._setView(self.image_view)

    def process(self, dataIn, display=True):
        ## if process is called with display=False, then the flowchart is being operated
        ## in batch processing mode, so we should skip displaying to improve performance.
        
        if display and self.image_view is not None:
            if dataIn is None:
                self.image_view.setImage(np.zeros((1,1)))
            else:
                self.image_view.setImage(dataIn)



def add_image_process_library(library):
    if isinstance( library, pgfc.NodeLibrary.NodeLibrary ):
        library.addNodeType(ImageViewNode       , [('Image',),])
    return library