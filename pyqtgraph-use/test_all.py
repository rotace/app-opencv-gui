# -*- coding: utf-8 -*-
"""
test for my_scapy

ref) pytestに入門してみたメモ
https://qiita.com/hira_physics/items/1a2748e443d8282c94b2

ref) pytestのとりあえず知っておきたい使い方
https://qiita.com/kg1/items/4e2cae18e9bd39f014d4

"""

import struct
import my_scapy


def test_float_decoder():
    """
    test float_decoder()

    ref) Pythonでdouble型のbinary表現を確認する
    http://inaz2.hatenablog.com/entry/2013/12/05/234357

    """
    xf = 3.14159
    xs = struct.pack('>d', xf)
    xi = struct.unpack('>Q', xs)[0]

    # 64bit
    len_sign = 1
    len_exp  = 11
    len_coef = 52
    yf = my_scapy.float_decoder(xi, len_sign, len_exp, len_coef)
    yi = my_scapy.float_encoder(xf, len_sign, len_exp, len_coef)
    assert xf == yf


def test_float_encoder():
    """
    test float_encoder()

    ref) Pythonでdouble型のbinary表現を確認する
    http://inaz2.hatenablog.com/entry/2013/12/05/234357

    """
    xf = 3.14159
    xs = struct.pack('>d', xf)
    xi = struct.unpack('>Q', xs)[0]

    # 64bit
    len_sign = 1
    len_exp  = 11
    len_coef = 52
    yf = my_scapy.float_decoder(xi, len_sign, len_exp, len_coef)
    yi = my_scapy.float_encoder(xf, len_sign, len_exp, len_coef)
    assert xi == yi