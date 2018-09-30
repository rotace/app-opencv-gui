# -*- coding: utf-8 -*-
"""
my scapy extension
"""

from scapy.fields import *
from scapy.packet import *
from scapy.plist import PacketList
from scapy.layers.inet import *
from scapy.layers.rtp import *
from scapy.utils import *


def float_decoder(buffer, len_sign, len_exp, len_coef):
    """
    common floating point decoder

    ref) Floating point number
    https://ja.wikipedia.org/wiki/%E6%B5%AE%E5%8B%95%E5%B0%8F%E6%95%B0%E7%82%B9%E6%95%B0
    ref) Signed number representations
    https://ja.wikipedia.org/wiki/%E7%AC%A6%E5%8F%B7%E4%BB%98%E6%95%B0%E5%80%A4%E8%A1%A8%E7%8F%BE

    example)

    when,

     sign (len_sign=1, val_sign=0)
     |
     |        (len_exp=5, val_sign=24)
     |         |                     (len_coef=10, val_coef=93)
     |         |                      |
    < ><  expornent  ><          fraction          >
    [0][1][1][0][0][0][0][0][0][1][0][1][1][1][0][1]

    then,

    ans = ((-1)^n_sign)  *  (2^n_exp)  *  (1+n_coef)
    n_sign = val_sign
    n_exp  = val_exp  - ( 2^(len_exp-1) - 1 )   # 2^(len_exp-1)-1 is Offset Binary (EXCESS-N)
    n_coef = val_coef *   2^(-len_coef)

    therefore,
    n_sign = 0
    n_exp  = 24 - 15 = 9  # EXCESS-15 (5-1 bit num)
    n_coef = 93 * 0.0009765265 = 0.0908
    ans = 1 * 2^9 * 1.0908 = 464.896


    major encoding)
    
    IEEE754 binary64: float_decoder(buf, 1, 11, 52)
    IEEE754 binary32: float_decoder(buf, 1,  8, 23)
    IEEE754 binary16: float_decoder(buf, 1,  5, 10)

    """
    if buffer is None:
        return 0.0
    
    assert isinstance(buffer, int), "buffer is unexpected type"
    
    length = len_sign + len_exp + len_coef
    offset = 0
    lentmp = len_sign
    valtmp = (2**length-1) >> (length-lentmp) << (length-lentmp-offset)
    valtmp = (valtmp & buffer) >> (length-lentmp-offset)
    val_sign = valtmp

    offset += lentmp
    lentmp = len_exp
    valtmp = (2**length-1) >> (length-lentmp) << (length-lentmp-offset)
    valtmp = (valtmp & buffer) >> (length-lentmp-offset)
    val_exp = valtmp

    offset += lentmp
    lentmp = len_coef
    valtmp = (2**length-1) >> (length-lentmp) << (length-lentmp-offset)
    valtmp = (valtmp & buffer) >> (length-lentmp-offset)
    val_coef = valtmp

    ret = (-1)**val_sign
    ret = ret * (1+2.**(-len_coef)*val_coef)
    ret = ret * 2.**(val_exp-2**(len_exp-1)+1)
    return ret


def float_encoder(buffer, len_sign, len_exp, len_coef):
    """
    common floating point number encoder

    hex format)

    -0x1.0400000000000p+5
      |<  val_coef   > <>--val_exp 
      |               |
      idx_x           idx_p

    """
    if buffer is None:
        return 0
    
    assert isinstance(buffer, float), "buffer is unexpected type"

    s = buffer.hex()
    idx_x = s.find("x")
    idx_p = s.find("p")

    if s[0] == '-':
        val_sign = 1
    else:
        val_sign = 0

    val_exp  = int(s[idx_p+1:]     , 10)+2**(len_exp-1)-1
    val_coef = int(s[idx_x+3:idx_p], 16) >> (52-len_coef)

    length = len_sign + len_exp + len_coef
    offset = 0
    ret = 0
    offset += 0; lentmp = len_sign
    ret = ret | (val_sign << (length-offset-lentmp))
    offset += lentmp; lentmp = len_exp
    ret = ret | (val_exp << (length-offset-lentmp))
    offset += lentmp; lentmp = len_coef
    ret = ret | (val_coef << (length-offset-lentmp))
    return ret


