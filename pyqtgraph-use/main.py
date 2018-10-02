# -*- coding: utf-8 -*-
"""
OpenCV-GUI implemented by pyqtgraph
"""

import sys
import time
import socket
import struct
import threading

import numpy as np
import cv2

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import pyqtgraph.dockarea as pgda
import pyqtgraph.flowchart as pgfc

import node_calc
import node_view
import my_scapy
import scapy

# LIBRARY = pgfc.library.LIBRARY.copy() # start with the default node set
LIBRARY = pgfc.NodeLibrary.NodeLibrary() # start with empty node set
LIBRARY = node_calc.add_library(LIBRARY)
LIBRARY = node_view.add_library(LIBRARY)


class PacketImporter(QtWidgets.QWidget):
    """
    This is Packet Importer
    非ソケット通信用インポータ
    ソケット通信をキャプチャする場合などに使用する
    PacketCapturerは別スレッドで駆動（run() オーバーライド方式）

    注意）run()メソッドのscapy.sendrecv.sniff()は内部でtcpdumpを使用しており、
    OSのsudo権限がないと動作しない。
    """
    class PacketCapturer(QtCore.QThread):
        """
        This is Packet Capturer (inner class)
        """
        sigDataEmited = QtCore.pyqtSignal(dict)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.quit_event = threading.Event()
            self.stop_event = threading.Event()
            self.parser = my_scapy.VideoProtocolParser()
            self.shost = 'localhost'
            self.sport = 50030

        def run(self):
            ## snatch thread from event loop method, when main routine wake up
            fil_str = "udp and (dst {0}) and (port {1})".format(self.shost, self.sport)
            scapy.sendrecv.sniff(filter=fil_str, prn=self._set_data)
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

        def _set_data(self, pkt):
            pkt = pkt[my_scapy.VideoProtocol]
            pkt.show3()
            image = self.parser.toimage(pkt)
            if image is not None:
                self.sigDataEmited.emit(dict(image=image))


    def __init__(self):
        super().__init__()

        self.capturer = self.PacketCapturer()
        self.capturer.start()

        self.layout = QtWidgets.QHBoxLayout()
        self.label  = QtWidgets.QLabel('Packet Importer', self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def get_name(self):
        return 'Packet'
    
    def get_data_signal(self):
        return self.capturer.sigDataEmited

    def is_playing(self):
        return not self.capturer.is_stoped()

    def play(self):
        if self.capturer.is_stoped():
            self.capturer.start_while_loop()
        else:
            self.capturer.stop_while_loop()

    def deleteLater(self):
        # set stop_event and wait to exit main routine
        self.capturer.quit_while_loop()
        # then, wake up event loop
        # emit finished signal and exit event loop
        self.capturer.quit() 
        # delete myself
        super().deleteLater()


class SocketImporter(QtWidgets.QWidget):
    """
    This is Socket Importer
    ソケット通信用インポータ
    UDPサーバは別スレッドで駆動（moveToThread方式）
    """
    class UdpServer(QtCore.QObject):
        """
        this inner class is UDP Server (inner class)
        """
        sigDataEmited = QtCore.pyqtSignal(dict)

        def __init__(self, parent=None):
            super().__init__(parent)

            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            host = self.udp_sock.getsockname()[0]
            port = 50030
            self.udp_sock.bind((host, port))

        def recv_data(self):
            parser = my_scapy.VideoProtocolParser()
            while True:
                buf = self.udp_sock.recv(20000)
                pkt = my_scapy.VideoProtocol(buf)
                image = parser.toimage(pkt)
                if image is not None:
                    self.sigDataEmited.emit(dict(image=image))


    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QGridLayout()
        self.label_host = QtWidgets.QLabel('Server Host', self)
        self.label_tcp = QtWidgets.QLabel('TCP Port', self)
        self.line_edit_host = QtWidgets.QLineEdit(self)
        self.spin_box_tcp = QtWidgets.QSpinBox(self)

        self.layout.addWidget(self.label_host, 0,0)
        self.layout.addWidget(self.line_edit_host, 0,1)
        self.layout.addWidget(self.label_tcp, 1,0)
        self.layout.addWidget(self.spin_box_tcp, 1,1)
        self.setLayout(self.layout)

        self.line_edit_host.setText('localhost')
        self.spin_box_tcp.setMinimum(0)
        self.spin_box_tcp.setMaximum(65535)
        self.spin_box_tcp.setValue(50000)

        self.tcp_sock = None
        self.udp_sock = None

        self.udp_server = self.UdpServer()
        self.sub_thread = QtCore.QThread()
        self.udp_server.moveToThread(self.sub_thread)
        self.sub_thread.started.connect(self.udp_server.recv_data)
        self.sub_thread.start()

    def get_name(self):
        return 'Socket'

    def get_data_signal(self):
        return self.udp_server.sigDataEmited

    def is_playing(self):
        return self.tcp_sock is not None
    
    def play(self):
        if self.is_playing():
            pkt = my_scapy.MessageProtocol(dataflag='Standby')
            try:
                self.tcp_sock.send(scapy.utils.raw(pkt))
                time.sleep(0.1)
                self.tcp_sock.shutdown(socket.SHUT_RDWR)
                self.tcp_sock.close()

                self.line_edit_host.setEnabled(True)
                self.spin_box_tcp.setEnabled(True)
                self.tcp_sock = None
            except socket.error as e:
                print(e)

        else:
            assert self.tcp_sock is None, 'TCP Socket is survive illegally'
            host = self.line_edit_host.text()
            port = self.spin_box_tcp.value()
            pkt = my_scapy.MessageProtocol(dataflag='Running')
            try:
                ## TCP Connection
                # self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # self.tcp_sock.bind(self.tcp_sock.getsockname())
                # self.tcp_sock.connect((host, port))
                self.tcp_sock = socket.create_connection((host, port))
                self.tcp_sock.send(scapy.utils.raw(pkt))

                self.line_edit_host.setEnabled(False)
                self.spin_box_tcp.setEnabled(False)
            except socket.error as e:
                print(e)
                return
            

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

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._set_data)
        self.timer.start(100)
        self.timer.stop()

    def get_name(self):
        return 'File'

    def get_data_signal(self):
        return self.sigDataEmited

    def is_playing(self):
        return self.timer.isActive()
    
    def play(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()

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

    def get_name(self):
        return 'WebCam'

    def get_data_signal(self):
        return self.sigDataEmited

    def is_playing(self):
        return self.timer.isActive()

    def play(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()

    def _set_data(self):
        success, image = self.capture.read()
        if success:
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
        
        self.importers = []
        self.importers.append(WebCamImporter())
        self.importers.append(FileImporter())
        self.importers.append(SocketImporter())
        # self.importers.append(PacketImporter())
        self.importer = None

        self.tab = QtWidgets.QTabWidget()
        self.tab.currentChanged.connect(self._change_importer)
        [ self.tab.addTab(i, i.get_name()) for i in self.importers ]
        [ i.get_data_signal().connect(self._set_data) for i in self.importers ]
        [ i.play() for i in self.importers if i.is_playing() ]
        self.layout.addWidget(self.tab)
        
        self._change_importer(0)

    def _change_importer(self, index):
        # get current widget
        self.importer = self.tab.currentWidget()
        # stop playing all widgets
        [ i.play() for i in self.importers if i.is_playing() ]
        # disconnect all widgets
        self.btn_play.disconnect()
        # set connect
        self.btn_play.clicked.connect(self.play)
        self.btn_play.setText('|>')
        if   index == 0:
            self.btn_back.setEnabled(False)
            self.btn_step.setEnabled(False)

        elif index == 1:
            self.btn_back.setEnabled(True)
            self.btn_step.setEnabled(True)

        elif index == 2:
            self.btn_back.setEnabled(False)
            self.btn_step.setEnabled(False)

        elif index == 3:
            self.btn_back.setEnabled(False)
            self.btn_step.setEnabled(False)

        else:
            sentence = 'Assertion Failed: index:{0}'.format(index)
            assert False, sentence

    def play(self):
        self.importer.play()
        if self.importer.is_playing():
            self.btn_play.setText('||')
        else:
            self.btn_play.setText('|>')

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
        fw = fc.widget()
        sp = fw.sizePolicy()
        sp.setHorizontalStretch(1)
        sp.setVerticalStretch(1)
        fw.setSizePolicy(sp)
        layout.addWidget(fw, 0,0)

        ## Create Stream Controller
        sc = StreamController(flowchart=fc)
        sp = sc.sizePolicy()
        sp.setHorizontalStretch(1)
        sp.setVerticalStretch(0.5)
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
        node1 = fc.createNode('CvtColor', pos=(0,-150))
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
