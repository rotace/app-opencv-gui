# -*- coding: utf-8 -*-
"""
OpenCV-GUI implemented by pyqtgraph
"""

import os
import sys
import time
import socket
import struct
import threading

import numpy as np
import cv2
from tqdm import tqdm

from PyQt5 import QtCore, QtGui, QtWidgets
import deps.pyqtgraph.pyqtgraph as pg
import deps.pyqtgraph.pyqtgraph.dockarea as pgda
import deps.pyqtgraph.pyqtgraph.flowchart as pgfc

import node_calc
import node_view
import my_scapy
import scapy

# LIBRARY = pgfc.library.LIBRARY.copy() # start with the default node set
LIBRARY = pgfc.NodeLibrary.NodeLibrary() # start with empty node set
LIBRARY = node_calc.add_library(LIBRARY)
LIBRARY = node_view.add_library(LIBRARY)

class AbstractImporter(QtWidgets.QWidget):
    """
    This is Abstract Importer (Interface)
    """
    def __init__(self):
        super().__init__()
        self._layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._layout)

        lay1 = QtWidgets.QHBoxLayout()
        wid1 = QtWidgets.QWidget()
        wid1.setLayout(lay1)
        wid1.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.addWidget(wid1)

        self.btn_back = QtWidgets.QPushButton('<<')
        self.btn_refresh = QtWidgets.QPushButton('<>')
        self.btn_play = QtWidgets.QPushButton('|>')
        self.btn_step = QtWidgets.QPushButton('||>')
        self.btn_back.clicked.connect(self.back)
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_play.clicked.connect(self.play)
        self.btn_step.clicked.connect(self.step)
        lay1.addWidget(self.btn_back)
        lay1.addWidget(self.btn_refresh)
        lay1.addWidget(self.btn_play)
        lay1.addWidget(self.btn_step)

        self.setEnabled(back=False, refresh=False, play=False, step=False)
    
    def setEnabled(self, **kwargs):
        self.btn_back.setEnabled(kwargs.get('back', self.btn_back.isEnabled()))
        self.btn_refresh.setEnabled(kwargs.get('refresh', self.btn_refresh.isEnabled()))
        self.btn_play.setEnabled(kwargs.get('play', self.btn_play.isEnabled()))
        self.btn_step.setEnabled(kwargs.get('step', self.btn_step.isEnabled()))

    def addWidget(self, widget):
        self._layout.addWidget(widget)
    
    def get_data_signal(self):
        raise NotImplementedError

    def get_stop_signal(self):
        raise NotImplementedError
    
    def play(self):
        if self.is_playing():
            self.btn_play.setText('||')
        else:
            self.btn_play.setText('|>')

    def step(self):
        raise NotImplementedError

    def back(self):
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError

    def is_playing(self):
        raise NotImplementedError


class PacketImporter(AbstractImporter):
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
        sigPlayStoped = QtCore.pyqtSignal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self.quit_event = threading.Event()
            self.stop_event = threading.Event()
            self.parser = my_scapy.VideoProtocolParser()
            self.shost = 'localhost'
            self.sport = my_scapy.VP_PORT

        def run(self):
            ## snatch thread from event loop method, when main routine wake up
            fil_str = "udp and (dst {0}) and (port {1})".format(self.shost, self.sport)
            scapy.sendrecv.sniff(filter=fil_str, prn=self.recv_data)
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

        def recv_data(self, pkt):
            pkt = pkt[my_scapy.RTP]
            pkt.show3()
            image = self.parser.toimage(pkt)
            if image is not None:
                self.sigDataEmited.emit(dict(image=image))


    def __init__(self):
        super().__init__()
        self.setEnabled(back=False, refresh=False, play=True, step=False)

        self.capturer = self.PacketCapturer()
        self.capturer.start()

        self.label  = QtWidgets.QLabel('Packet Importer', self)
        self.addWidget(self.label)

    def get_name(self):
        return 'Packet'
    
    def get_data_signal(self):
        return self.capturer.sigDataEmited

    def get_stop_signal(self):
        return self.capturer.sigPlayStoped

    def is_playing(self):
        return not self.capturer.is_stoped()

    def play(self):
        if self.capturer.is_stoped():
            self.capturer.start_while_loop()
        else:
            self.capturer.stop_while_loop()
        super().play()

    def step(self):
        pass

    def back(self):
        pass
    
    def refresh(self):
        pass

    def deleteLater(self):
        # set stop_event and wait to exit main routine
        self.capturer.quit_while_loop()
        # then, wake up event loop
        # emit finished signal and exit event loop
        self.capturer.quit() 
        # delete myself
        super().deleteLater()


class SocketImporter(AbstractImporter):
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
        sigPlayStoped = QtCore.pyqtSignal()

        def __init__(self, parent=None):
            super().__init__(parent)

            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            host = self.udp_sock.getsockname()[0]
            port = my_scapy.VP_PORT
            self.udp_sock.bind((host, port))

        def recv_data(self):
            parser = my_scapy.VideoProtocolParser()
            while True:
                buf = self.udp_sock.recv(20000)
                pkt = my_scapy.RTP(buf)
                image = parser.toimage(pkt)
                if image is not None:
                    self.sigDataEmited.emit(dict(image=image))


    def __init__(self):
        super().__init__()
        self.setEnabled(back=False, refresh=False, play=True, step=False)

        lay1 = QtWidgets.QGridLayout()
        wid1 = QtWidgets.QWidget()
        wid1.setLayout(lay1)
        self.addWidget(wid1)

        self.label_host = QtWidgets.QLabel('Server Host', self)
        self.label_tcp = QtWidgets.QLabel('TCP Port', self)
        self.line_edit_host = QtWidgets.QLineEdit(self)
        self.spin_box_tcp = QtWidgets.QSpinBox(self)

        lay1.addWidget(self.label_host, 0,0)
        lay1.addWidget(self.line_edit_host, 0,1)
        lay1.addWidget(self.label_tcp, 1,0)
        lay1.addWidget(self.spin_box_tcp, 1,1)

        self.line_edit_host.setText('localhost')
        self.spin_box_tcp.setMinimum(0)
        self.spin_box_tcp.setMaximum(65535)
        self.spin_box_tcp.setValue(my_scapy.MP_PORT)

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

    def get_stop_signal(self):
        return self.udp_server.sigPlayStoped

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
        super().play()
    
    def step(self):
        pass
    
    def back(self):
        pass
    
    def refresh(self):
        pass
            

class FileImporter(AbstractImporter):
    """
    This is File Importer
    """
    sigDataEmited = QtCore.pyqtSignal(dict)
    sigPlayStoped = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.filename = None
        self.dirname = os.getcwd()
        self.video = None
        self.video_itr = None
        self.image = None

        self.setEnabled(back=True, refresh=True, play=True, step=True)

        # Widget1
        lay1 = QtWidgets.QHBoxLayout()
        wid1 = QtWidgets.QWidget()
        wid1.setLayout(lay1)
        self.addWidget(wid1)

        self.label_file = QtWidgets.QLabel('File', self)
        self.line_edit_file = QtWidgets.QLineEdit(self)
        self.line_edit_file.setEnabled(False)
        self.tool_button_file = QtWidgets.QToolButton(self)
        self.tool_button_file.clicked.connect(self._open_file)
        lay1.addWidget(self.label_file)
        lay1.addWidget(self.line_edit_file)
        lay1.addWidget(self.tool_button_file)

        # Widget2
        lay2 = QtWidgets.QHBoxLayout()
        wid2 = QtWidgets.QWidget()
        wid2.setLayout(lay2)
        self.addWidget(wid2)
       
        self.h_slider = QtWidgets.QSlider()
        self.spin_box = QtWidgets.QSpinBox()
        self.h_slider.setOrientation(QtCore.Qt.Horizontal)
        self.h_slider.setEnabled(False)
        self.spin_box.setEnabled(False)
        self.h_slider.valueChanged.connect(self.spin_box.setValue)
        self.spin_box.valueChanged.connect(self.h_slider.setValue)
        lay2.addWidget(self.h_slider)
        lay2.addWidget(self.spin_box)

        # Timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update)
        self.timer.start(100)
        self.timer.stop()

    def _open_file(self):
        filename_list = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Open Video File',
            self.dirname,
            "All (*)"
            + ";;Pcap files (*.pcap *.pcapng)"
            + ";;Video files (*.mp4)"
            )
        if len(filename_list[0]) == 0:
            return
        else:
            self.filename = filename_list[0]
            self.dirname = os.path.dirname(self.filename)
            self.line_edit_file.setText(self.filename)

            _, ext = os.path.splitext(self.filename)
            if    ext in {"", ".pcap", ".pcapng"}:
                # Load pcap/pcapng
                self.video = my_scapy.load_pcap_file(self.filename)
            elif  ext in {".mp4"}:
                cap = cv2.VideoCapture(self.filename)
                self.video = []
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                pbar = tqdm(total=frame_count, desc="Loading Video")
                while cap.isOpened():
                    ret, image = cap.read()
                    pbar.update(1)
                    if ret:
                        self.video.append(image)
                    else:
                        break
                pbar.close()
                cap.release()
            else:
                self.video = None
                return
            self.h_slider.setMaximum(len(self.video))
            self.spin_box.setMaximum(len(self.video))

    def get_name(self):
        return 'File'

    def get_data_signal(self):
        return self.sigDataEmited

    def get_stop_signal(self):
        return self.sigPlayStoped

    def is_playing(self):
        return self.timer.isActive()
    
    def play(self):
        if self.video is None:
            return
        if self.timer.isActive():
            self.timer.stop()
            self.h_slider.setEnabled(True)
            self.spin_box.setEnabled(True)
        else:
            if self.spin_box.value() >= len(self.video):
                self.spin_box.setValue(0)
            self.h_slider.setEnabled(False)
            self.spin_box.setEnabled(False)
            idx = self.spin_box.value()
            self.video_itr = iter(self.video[idx:])
            self.timer.start()
        super().play()

    def step(self):
        if self.video is None:
            return
        idx = self.spin_box.value()
        self.video_itr = iter(self.video[idx:])
        self._update()
    
    def back(self):
        self.spin_box.setValue(0)
    
    def refresh(self):
        if self.image is not None:
            self.sigDataEmited.emit(dict(image=self.image))

    def _update(self):
        try:
            self.image = next(self.video_itr)
            idx = self.spin_box.value()
            self.spin_box.setValue(idx+1)
            if self.image is not None:
                self.sigDataEmited.emit(dict(image=self.image))
        except StopIteration:
            self.sigPlayStoped.emit()


class WebCamImporter(AbstractImporter):
    """
    This is USB WebCam Importer
    """
    sigDataEmited = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setEnabled(back=False, refresh=False, play=True, step=False)

        self.label  = QtWidgets.QLabel('WebCam Importer', self)
        self.addWidget(self.label)

        self.capture = cv2.VideoCapture(0)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update)
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
        super().play()

    def step(self):
        self._update()

    def back(self):
        pass
    
    def refresh(self):
        pass

    def _update(self):
        success, image = self.capture.read()
        if success:
            self.sigDataEmited.emit(dict(image=image))


class StreamController(QtWidgets.QTabWidget):
    """
    This is Controller which handle webcamera, ethernet, etc.
    """
    def __init__(self, parent=None, flowchart=None):
        super().__init__(parent)

        self.flowchart = flowchart

        self.importers = []
        self.importers.append(WebCamImporter())
        self.importers.append(FileImporter())
        self.importers.append(SocketImporter())
        # self.importers.append(PacketImporter())
        self.importer = None

        self.currentChanged.connect(self._change_importer)
        [ self.addTab(i, i.get_name()) for i in self.importers ]
        [ i.get_data_signal().connect(self.set_data) for i in self.importers ]
        [ i.play() for i in self.importers if i.is_playing() ]
        
        self._change_importer(0)

    def _change_importer(self, index):
        # stop playing all widgets
        [ i.play() for i in self.importers if i.is_playing() ]
        # get current widget
        self.importer = self.currentWidget()



    def set_data(self, data):
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
