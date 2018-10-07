# coding: utf-8

import sys
import time
import socket
import struct
import threading

import cv2
import numpy as np

import scapy
import my_scapy


class UdpServer():
    """
    This is UDP Server
    UDP Server は別スレッドで駆動（threading.Thread()）
    """
    def __init__(self):
        self.quit_event = threading.Event()
        self.stop_event = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = ('localhost', my_scapy.VP_PORT)
        self.parser = my_scapy.VideoProtocolParser()
        self.thread = threading.Thread(target = self.run)

        # self.capture = cv2.VideoCapture(0)

        self.stop_event.set()
        self.thread.start()

    def run(self):
        while not self.quit_event.wait(timeout=1.0):
            if self.stop_event.is_set():
                continue
            image = self.generate_image()
            if image is None:
                continue
            pkts = self.parser.fromimage(image)
            for pkt in pkts:
                time.sleep(0.01)
                buf = scapy.utils.raw(pkt)
                self.sock.sendto(buf, self.addr)

    def quit(self):
        self.quit_event.set()

    def stop(self):
        self.stop_event.set()

    def start(self):
        self.stop_event.clear()

    def generate_image(self):
        # generate random input data
        data = np.random.normal(size=(100,100))
        data[40:60, 40:60] += 15.0
        data[30:50, 30:50] += 15.0
        image = np.zeros(shape=(100,100), dtype=np.uint8)
        image[:,:] = data[:,:]
        return image

        # send camera image
        # success, image = self.capture.read()
        # if success:
        #     return image
        # else:
        #     return None



def loop():
    while True:
        # クライアントからの接続を待ち受ける (接続されるまでブロックする)
        client_sock, (client_addr, client_port) = server_sock.accept()
        print('New client: {0}:{1}'.format(client_addr, client_port))

        while True:
            # クライアントソケットから指定したバッファバイト数だけデータを受け取る
            try:
                # ヘッダ(データサイズ)を読み取る
                header = client_sock.recv(4)
                if len(header) == 0:
                    break
                datasize = struct.unpack('<I', header)[0]
                # メッセージを読み取る
                message = client_sock.recv(datasize-4)
                if len(message) == 0:
                    break

                # パケットに変換
                pkt = my_scapy.MessageProtocol(header + message)

                # Message is Running
                if pkt.dataflag == 0x55555555:
                    udp_server.start()
                    print('Recv: Running')
                # Message is Standby
                elif pkt.dataflag == 0xffffffff:
                    udp_server.stop()
                    print('Recv: Standby')
                
            except OSError:
                break

            # # 受信したデータの長さが 0 ならクライアントからの切断を表す
            # if len(message) == 0:
            #     break

            # # 受信したデータをそのまま送り返す (エコー)
            # client_sock.sendall(message)
            # print('Send: {}'.format(message))

        # 後始末
        client_sock.close()
        print('Bye-Bye: {0}:{1}'.format(client_addr, client_port))


# udp server
udp_server = UdpServer()

# IPv4/TCP のソケットを用意する
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 'Address already in use' の回避策 (必須ではない)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

# 待ち受けるアドレスとポートを指定する
# もし任意のアドレスで Listen したいときは '' を使う
host = 'localhost'
port = my_scapy.MP_PORT
server_sock.bind((host, port))

# クライアントをいくつまでキューイングするか
server_sock.listen(1)

try:
    loop()
except KeyboardInterrupt:
    print("")
    print("Ctrl+C is pressed. Now terminating thread. Please Wait...")
    udp_server.quit()
    sys.exit()
