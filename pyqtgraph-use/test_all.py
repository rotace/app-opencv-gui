# -*- coding: utf-8 -*-
"""
test for my_scapy

ref) pytestに入門してみたメモ
https://qiita.com/hira_physics/items/1a2748e443d8282c94b2

ref) pytestのとりあえず知っておきたい使い方
https://qiita.com/kg1/items/4e2cae18e9bd39f014d4

"""

import unittest
import struct

import numpy as np

import my_scapy

class TestEnCodeDecode(unittest.TestCase):
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

    def test_float_decoder(self):
        yf = my_scapy.float_decoder(
            self.xi, self.len_sign, 
            self.len_exp, 
            self.len_coef)
        self.assertEqual(self.xf , yf)

    def test_float_encoder(self):
        yi = my_scapy.float_encoder(
            self.xf,
            self.len_sign,
            self.len_exp,
            self.len_coef)
        self.assertEqual(self.xi , yi)


class TestVideoProtocolParser(unittest.TestCase):
    """
    test VideoProtocolParser
    """
    parser = my_scapy.VideoProtocolParser()
    data = np.random.normal(size=(5,5))
    image = np.zeros(shape=(5,5), dtype=np.uint8)
    image[:,:] = data[:,:]

    def test_from_to_image(self):
        pkts = self.parser.fromimage(self.image)
        for pkt in pkts:
            image = self.parser.toimage(pkt)
            if image is None:
                break
        np.testing.assert_array_equal(self.image, image)

if __name__ == '__main__':
    unittest.main()