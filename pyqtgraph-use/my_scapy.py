# -*- coding: utf-8 -*-
"""
my scapy extension
"""
from collections import defaultdict

from scapy.fields import *
from scapy.packet import *
from scapy.plist import PacketList
from scapy.layers.inet import *
from scapy.layers.rtp import *
from scapy.utils import *

import numpy as np
from tqdm import tqdm


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


class LESignedShortField(Field):
    def __init__(self, name, default):
        Field.__init__(self, name, default, "<h")


class XLEIntEnumField(LEIntEnumField):
    def i2repr_one(self, pkt, x):
        if self not in conf.noenum and not isinstance(x,VolatileValue):
            try:
                return self.i2s[x]
            except KeyError:
                pass
            except TypeError:
                ret = self.i2s_cb(x)
                if ret is not None:
                    return ret
        return lhex(x)

FLAG_DATA = {0x55555555:"Running",
             0xffffffff:"Standby",
             }

class MessageProtocol(Packet):
    """
    Message Protocol

    How to Use
    LEIntField      : 4byte  32bit ( little endian )
    XLEIntEnumField : 4byte  32bit ( little endian and hex )
    BitEnumField    : 1byte~ 1bit~ ( Total bits must be 8 x N bits )
    """
    name = "MP"
    fields_desc = [ LEIntField     ("datasize",       12),
                    XLEIntEnumField("dataflag",       0xffffffff, FLAG_DATA),

                    BitEnumField   ("flag_state",     0, 1, ["Green", "Red"]),
                    BitEnumField   ("flag_reserved1", 0, 3, {0:"reserved"}),
                    BitEnumField   ("flag_reserved2", 0, 4, ["reserved"]),
                    ByteField      ("flag_reserved3", 0),
                    ByteField      ("flag_reserved4", 0),
                    ByteField      ("flag_reserved5", 0),
                    ]
    
    def show3(self):
        """
        show only low layer info
        """
        pkt = self.copy()
        pkt.remove_payload()
        pkt.show()


class VideoProtocol(RTP):
    """
    Video Protocol

    This is Protocol for video using RTP

    """
    def show3(self):
        """
        show only low layer info
        """
        pkt = self.copy()
        pkt.remove_payload()
        pkt.show()


class VideoProtocolParser():
    """
    Video Protocol Parser

    """
    def __init__(self):
        self.buffer = b""

    def toimage(self, pkt):
        assert isinstance( pkt, VideoProtocol ) , "packet is not VideoProtocol"
        self.buffer += pkt.load
        if pkt.marker == 1:
            row, col = struct.unpack("II", self.buffer[:8])
            image = np.frombuffer(self.buffer[8:], dtype=np.uint8)
            image = image.reshape((row, col))
            self.buffer = b""
            return image
        else:
            return None

    @staticmethod
    def fromimage(image):
        assert isinstance( image, np.ndarray ) , "image is not ndarray"
        row = image.shape[0]
        col = image.shape[1]
        buf  = struct.pack("II", row, col)
        buf += image.tostring()
        buf_size = len(buf)
        pkt_list = []
        tmp_size = 1024
        tmp_sidx = 0
        tmp_eidx = tmp_size
        while tmp_eidx < buf_size:
            pkt_list.append(RTP()/buf[tmp_sidx:tmp_eidx])
            tmp_sidx += tmp_size
            tmp_eidx += tmp_size
        pkt_list.append(RTP(marker=1)/buf[tmp_sidx:])
        return pkt_list



def ip_defragment(plist):
    """defrag(plist) -> plist defragmented as much as possible """
    frags = defaultdict(lambda:[])
    final = []

    pos = 0
    for p in plist:
        p._defrag_pos = pos
        pos += 1
        if IP in p:
            ip = p[IP]
            if ip.frag != 0 or ip.flags & 1:
                ip = p[IP]
                uniq = (ip.id,ip.src,ip.dst,ip.proto)
                frags[uniq].append(p)
                continue
        final.append(p)

    pbar = tqdm(total=len(frags), desc="IP defrag(1/2) ")
    defrag = []
    missfrag = []
    for lst in six.itervalues(frags):
        pbar.update(1)
        lst.sort(key=lambda x: x.frag)
        p = lst[0]
        lastp = lst[-1]
        if p.frag > 0 or lastp.flags & 1 != 0: # first or last fragment missing
            missfrag += lst
            continue
        p = p.copy()
        if conf.padding_layer in p:
            del(p[conf.padding_layer].underlayer.payload)
        ip = p[IP]
        if ip.len is None or ip.ihl is None:
            clen = len(ip.payload)
        else:
            clen = ip.len - (ip.ihl<<2)
        txt = conf.raw_layer()
        for q in lst[1:]:
            if clen != q.frag<<3: # Wrong fragmentation offset
                if clen > q.frag<<3:
                    warning("Fragment overlap (%i > %i) %r || %r ||  %r" % (clen, q.frag<<3, p,txt,q))
                missfrag += lst
                break
            if q[IP].len is None or q[IP].ihl is None:
                clen += len(q[IP].payload)
            else:
                clen += q[IP].len - (q[IP].ihl<<2)
            if conf.padding_layer in q:
                del(q[conf.padding_layer].underlayer.payload)
            txt.add_payload(q[IP].payload.copy())
        else:
            ip.flags &= ~1 # !MF
            del(ip.chksum)
            del(ip.len)
            p = p/txt
            p._defrag_pos = max(x._defrag_pos for x in lst)
            defrag.append(p)
    pbar.close()
    defrag2=[]
    for p in tqdm(defrag, desc="IP defrag(2/2) "):
        q = p.__class__(raw(p))
        q._defrag_pos = p._defrag_pos
        defrag2.append(q)
    final += defrag2
    final += missfrag
    final.sort(key=lambda x: x._defrag_pos)
    for p in final:
        del(p._defrag_pos)

    if hasattr(plist, "listname"):
        name = "Defragmented %s" % plist.listname
    else:
        name = "Defragmented"
    
    return PacketList(final, name=name)



def rtp_defragment(plist):
    """ 
    dfragment rtp packets
    """
    frags = defaultdict(lambda:[])
    final = []
    mark = 1
    mark_last = 1

    pos = 0
    for p in plist:
        p._defrag_pos = pos
        pos += 1
        if RTP in p:
            rtp  = p[RTP] 
            mark_last = mark
            mark = rtp.marker
            if mark_last == 0 or mark == 0:
                rtp = p[RTP]
                uniq = (rtp.timestamp)
                frags[uniq].append(p)
                continue
        final.append(p)

    defrag = []
    for lst in six.itervalues(frags):
        lst.sort(key=lambda x: x.sequence)
        p = lst[0]
        lastp = lst[-1]
        # if p.frag > 0 or lastp.flags & 1 != 0: # first or last fragment missing
        #     missfrag += lst
        #     continue
        p = p.copy()
        rtp = p[RTP]
        clen = len(rtp.payload)
        txt = conf.raw_layer()
        for q in lst[1:]:
            clen += len(q[RTP].payload)
            txt.add_payload(q[RTP].payload.copy())
        else:
            rtp.marker = 1 # !marker
            # del(ip.chksum)
            # del(ip.len)
            p = p/txt
            p._defrag_pos = max(x._defrag_pos for x in lst)
            defrag.append(p)
    defrag2=[]
    for p in defrag:
        q = p.__class__(raw(p))
        q._defrag_pos = p._defrag_pos
        defrag2.append(q)
    final += defrag2
    final.sort(key=lambda x: x._defrag_pos)
    for p in final:
        del(p._defrag_pos)

    if hasattr(plist, "listname"):
        name = "Defragmented %s" % plist.listname
    else:
        name = "Defragmented"

    return PacketList(final, name=name)


bind_layers(TCP, MessageProtocol, dport=50000)
bind_layers(UDP, VideoProtocol,   dport=50030)