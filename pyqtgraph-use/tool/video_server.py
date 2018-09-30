# coding: utf-8

import socket

# IPv4/TCP のソケットを用意する
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 'Address already in use' の回避策 (必須ではない)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

# 待ち受けるアドレスとポートを指定する
# もし任意のアドレスで Listen したいときは '' を使う
host = 'localhost'
port = 50000
server_sock.bind((host, port))

# クライアントをいくつまでキューイングするか
server_sock.listen(1)

while True:
    # クライアントからの接続を待ち受ける (接続されるまでブロックする)
    client_sock, (client_addr, client_port) = server_sock.accept()
    print('New client: {0}:{1}'.format(client_addr, client_port))

    while True:
        # クライアントソケットから指定したバッファバイト数だけデータを受け取る
        try:
            message = client_sock.recv(1024)
            print('Recv: {}'.format(message))
        except OSError:
            break

        # 受信したデータの長さが 0 ならクライアントからの切断を表す
        if len(message) == 0:
            break

        # 受信したデータをそのまま送り返す (エコー)
        client_sock.sendall(message)
        print('Send: {}'.format(message))

    # 後始末
    client_sock.close()
    print('Bye-Bye: {0}:{1}'.format(client_addr, client_port))