# Copyright cozybit, Inc 2010-2011
# All rights reserved
# author: johan@cozybit.com, brian@cozybit.com

import wtf
import unittest
wtfconfig = wtf.conf
from scapy.layers.dot11 import *
import commands
from lxml import etree
import binascii

class dot11Packet():
    pkt = None;

    def __init__(self, packet):
        # First, create the basic packet
        proto = packet.xpath("proto[@name='wlan']")[0]
        frame_ctl = proto.xpath("field[@name='wlan.fc']")[0]
        self.type = int(frame_ctl.xpath("field[@name='wlan.fc.type']")[0].get("show"))
        self.subtype = int(frame_ctl.xpath("field[@name='wlan.fc.subtype']")[0].get("show"))
        addr1 = proto.xpath("field[@name='wlan.da']")[0].get("show").encode("ascii", "ignore")
        addr2 = proto.xpath("field[@name='wlan.sa']")[0].get("show").encode("ascii", "ignore")
        addr3 = proto.xpath("field[@name='wlan.bssid']")[0].get("show").encode("ascii", "ignore")

        if self.type == 0:
            mgmt = packet.xpath("proto[@name='wlan_mgt']")[0]
            fixed = mgmt.xpath("field[@name='wlan_mgt.fixed.all']")[0]
            tagged = mgmt.xpath("field[@name='wlan_mgt.tagged.all']")[0]
            if self.subtype == 0x8:
                self.pkt = Dot11(addr1=addr1, addr2=addr2, addr3=addr3)
                caps = int(fixed.xpath("field[@name='wlan_mgt.fixed.capabilities']")[0].get("value"), 16)
                self.pkt = self.pkt / Dot11Beacon(cap=caps)
            else:
                raise Exception("Unsupported mgmt subtype %d" % self.subtype)
            for t in tagged:
                ID = int(t.xpath("field[@name='wlan_mgt.tag.number']")[0].get("value"))
                info = ""
                for v in t.xpath("field"):
                    name = v.get("name")
                    if name == "wlan_mgt.tag.number" or name == "wlan_mgt.tag.length":
                        continue
                    s = v.get("value").encode("ascii", "ignore")
                    info += binascii.unhexlify("".join(map(lambda x,y: x+y, s[0::2], s[1::2])))
                self.pkt = self.pkt / Dot11Elt(ID=ID, info=info)
        else:
            raise Exception("Unsupported type %d" % self.type)

def tshark_xml_parser(txt):
    pkts = []

    tree = etree.fromstring(txt)
    for packet in tree.xpath("packet"):
        pkt = dot11Packet(packet).pkt
        pkts.append(pkt)
    return pkts

class TestTShark(unittest.TestCase):

    # write the specified packets to tshark and return his XML txt output
    def do_tshark(self, pkts):
        wrpcap("/tmp/tshark-test.pcap", pkts, 105)
        err, out = commands.getstatusoutput("tshark -Tpdml -n -r /tmp/tshark-test.pcap")
        if err != 0:
            self.failIf(True, "Failed to invoke tshark")
        return tshark_xml_parser(out)

    def expectEquals(self, p1, p2):
        self.failIf(p1.command() != p2.command(),
                    "EXPECTED:\n" + p1.command().replace("/", "\n/") +
                    "\nBUT GOT:\n" + p2.command().replace("/", "\n/"))

    def test_beacon(self):
        addr1s = "ff:ff:ff:ff:ff:ff"
        addr2s = "42:00:00:00:01:00"
        addr3s = "42:00:00:00:02:00"
        pkt = Dot11(addr1=addr1s,addr2=addr2s,addr3=addr3s)\
              / Dot11Beacon(cap="ESS")\
              / Dot11Elt(ID="SSID",info="fooSSID")\
              / Dot11Elt(ID="Rates",info='\x82\x84\x0b\x16')\
              / Dot11Elt(ID="DSset",info="\x03")\
              / Dot11Elt(ID="TIM",info="\x00\x01\x00\x00")
        pkts = self.do_tshark(pkt)
        self.expectEquals(pkt, pkts[0])
