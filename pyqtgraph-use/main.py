# -*- coding: utf-8 -*-
"""
OpenCV-GUI implemented by pyqtgraph
"""

import sys
import time
import threading

import numpy as np
import cv2

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import pyqtgraph.dockarea as pgda
import pyqtgraph.flowchart as pgfc

import imageprocess
import view

# LIBRARY = pgfc.library.LIBRARY.copy() # start with the default node set
LIBRARY = pgfc.NodeLibrary.NodeLibrary() # start with empty node set
LIBRARY = imageprocess.add_image_process_library(LIBRARY)
LIBRARY = view.add_image_process_library(LIBRARY)



class EthernetTransceiver(QtCore.QThread):
    """
    This is Ethernet Transceiver
    """
    sigDataEmited = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.quit_event = threading.Event()
        self.stop_event = threading.Event()

    def run(self):
        ## snatch thread from event loop method, when main routine wake up
        while not self.quit_event.is_set():
            time.sleep(0.1)
            if self.stop_event.is_set():
                continue
            self._set_data()
        ## return thread  to  event loop method, when main routine exited
        self.exec_()

    def quit_while_loop(self):
        self.quit_event.set()
    
    def stop_while_loop(self):
        self.stop_event.set()
    
    def start_while_loop(self):
        self.stop_event.clear()

    def is_stoped(self):
        return self.stop_event.is_set()

    def _set_data(self):
        ## generate random input data
        data = np.random.normal(size=(100,100))
        data = 25 * pg.gaussianFilter(data, (5,5))
        data += np.random.normal(size=(100,100))
        data[40:60, 40:60] += 15.0
        data[30:50, 30:50] += 15.0
        image = np.zeros(shape=(100,100), dtype=np.uint8)
        image[:,:] = data[:,:]
        self.sigDataEmited.emit(dict(image=image))


class EthernetImporter(QtWidgets.QWidget):
    """
    This is Ethernet Importer
    """
    def __init__(self):
        super().__init__()

        self.transceiver = EthernetTransceiver()
        self.transceiver.start()

        self.layout = QtWidgets.QHBoxLayout()
        self.label  = QtWidgets.QLabel('Ethernet Importer', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def play(self):
        if self.transceiver.is_stoped():
            self.transceiver.start_while_loop()
        else:
            self.transceiver.stop_while_loop()

    def deleteLater(self):
        # set stop_event and wait to exit main routine
        self.transceiver.quit_while_loop()
        # then, wake up event loop
        # emit finished signal and exit event loop
        self.transceiver.quit() 
        # delete myself
        super().deleteLater()


class FileImporter(QtWidgets.QWidget):
    """
    This is File Importer
    """
    sigDataEmited = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.layout = QtWidgets.QHBoxLayout()
        self.label  = QtWidgets.QLabel('File Importer', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
    

class WebCamImporter(QtWidgets.QWidget):
    """
    This is USB WebCam Importer
    """
    sigDataEmited = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.layout = QtWidgets.QHBoxLayout()
        self.label  = QtWidgets.QLabel('WebCam Importer', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.capture = cv2.VideoCapture(0)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._set_data)
        self.timer.start(100)

    def play(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()

    def _set_data(self):
        success, image = self.capture.read()
        self.sigDataEmited.emit(dict(image=image))


class StreamController(QtWidgets.QWidget):
    """
    This is Controller which handle webcamera, ethernet, etc.
    """
    def __init__(self, parent=None, flowchart=None):
        super().__init__(parent)

        self.flowchart = flowchart
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.player = QtWidgets.QWidget()
        self.btn_back = QtWidgets.QPushButton('<<')
        self.btn_play = QtWidgets.QPushButton('|>')
        self.btn_step = QtWidgets.QPushButton('||>')
        player_layout = QtWidgets.QHBoxLayout()
        player_layout.addWidget(self.btn_back)
        player_layout.addWidget(self.btn_play)
        player_layout.addWidget(self.btn_step)
        self.player.setLayout(player_layout)
        self.layout.addWidget(self.player)
        
        combo = QtWidgets.QComboBox()
        combo.addItem('WebCam')
        combo.addItem('File')
        combo.addItem('Ethernet')
        combo.setCurrentIndex(0)
        combo.currentIndexChanged.connect(self._change_importer)
        self.layout.addWidget(combo)

        self.importer = None
        self._change_importer(0)

    def _change_importer(self, index):
        old_importer = self.importer
        if   index == 0:
            self.importer = WebCamImporter()
            self.importer.sigDataEmited.connect(self._set_data)
            self.btn_back.setEnabled(False)
            self.btn_step.setEnabled(False)
            self.btn_play.clicked.connect(self.importer.play)
        elif index == 1:
            self.importer = FileImporter()
            self.importer.sigDataEmited.connect(self._set_data)
            self.btn_back.setEnabled(True)
            self.btn_step.setEnabled(True)
            # self.btn_play.clicked.connect(self.importer.play)
        elif index == 2:
            self.importer = EthernetImporter()
            self.importer.transceiver.sigDataEmited.connect(self._set_data)
            self.btn_back.setEnabled(False)
            self.btn_step.setEnabled(False)
            self.btn_play.clicked.connect(self.importer.play)
        else:
            sentence = 'Assertion Failed: index:{0}'.format(index)
            assert False, sentence

        if old_importer is None:
            self.layout.addWidget(self.importer)
        else:
            self.layout.replaceWidget(old_importer, self.importer)
            old_importer.deleteLater()

    def _set_data(self, data):
        ## Set the raw data as the input value to the flowchart
        self.flowchart.setInput(import_data=data)


class MainForm(QtWidgets.QMainWindow):
    """
    Main Window
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle('app-opencv-gui')
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

        ## Create Stream Controller
        sc = StreamController(flowchart=fc)
        sp = sc.sizePolicy()
        sp.setHorizontalStretch(1)
        sc.setSizePolicy(sp)
        layout.addWidget(sc, 1,0)

        ## Create DockArea
        da = pgda.DockArea()
        sp = da.sizePolicy()
        sp.setHorizontalStretch(2)
        da.setSizePolicy(sp)
        layout.addWidget(da, 0,1,2,1)

        ## initial flowchart setting
        node0 = fc.createNode('ImageView', pos=(100, -150))
        node1 = fc.createNode('Canny', pos=(0,-150))
        dock0 = node0.get_dock()
        da.addDock(dock0)
        # fc.connectTerminals(fc['import_data'], node0['data_in'])
        fc.connectTerminals(fc['import_data'], node1['data_in'])
        fc.connectTerminals(node1['data_out'], node0['data_in'])
        fc.connectTerminals(fc['import_data'], fc['export_data'])

        self.fc = fc


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
