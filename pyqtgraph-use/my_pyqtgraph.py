from PyQt5 import QtCore, QtGui, QtWidgets
import deps.pyqtgraph.pyqtgraph as pg


class ImageView(QtWidgets.QWidget):
    """
    Widget used for display and analysis of image data.
    """
    def __init__(self, parent=None, name="ImageView", view=None, imageItem=None, *args):
        QtWidgets.QWidget.__init__(self, parent, *args)
        
        self.layout = QtWidgets.QHBoxLayout()
        self.graphicsView = pg.GraphicsView(self)
        self.layout.addWidget(self.graphicsView)
        self.setLayout(self.layout)

        if view is None:
            self.view = pg.ViewBox()
        else:
            self.view = view
        self.graphicsView.setCentralItem(self.view)
        self.view.setAspectLocked(True)
        self.view.invertY()
        
        if imageItem is None:
            self.imageItem = pg.ImageItem()
        else:
            self.imageItem = imageItem
        self.view.addItem(self.imageItem)

    def setImage(self, img, autoRange=True, autoLevels=True, levels=None, axes=None, xvals=None, pos=None, scale=None, transform=None, autoHistogramRange=True):
        self.imageItem.setImage(img)