"""
Test infrastructure sta/ap connectivity
"""

import wtfconfig
import wtf.node.ap as AP
import unittest
import time

AP_IP = "192.168.99.1"
STA_IP = "192.168.99.2"

def setUp(self):
    # start with all of the nodes initialized by idle
    for n in wtfconfig.nodes:
        n.shutdown()
        n.init()

def tearDown(self):
    for n in wtfconfig.nodes:
        n.stop()

class TestAPSTA(unittest.TestCase):

    def setUp(self):
        # start with all of the nodes stopped
        for n in wtfconfig.nodes:
            n.stop()
        # set IP addrs, stack doesn't care if iface goes up or down
        wtfconfig.ap.set_ip(AP_IP)
        wtfconfig.sta.set_ip(STA_IP)

    def startNodes(self):
        for n in wtfconfig.nodes:
            n.start()

    def pingTest(self):
        self.failIf(wtfconfig.sta.ping(AP_IP) != 0,
                    "Failed to ping AP at %s" % AP_IP)

    def assocTest(self):
        self.failIf(wtfconfig.sta.assoc(wtfconfig.ap.config),
                    "Failed to associate with AP")

    def throughput(self):
        wtfconfig.ap.perf()
        results = wtfconfig.sta.perf(AP_IP)
        wtfconfig.ap.killperf()

    def stressTest(self):
        wtfconfig.ap.perf()
        results = wtfconfig.sta.stress(AP_IP)
        wtfconfig.ap.killperf()
        self.pingTest()

    def test_scan(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-scantest", channel=11)
        wtfconfig.ap.start()
        wtfconfig.sta.start()
        results = wtfconfig.sta.scan()
        found = None
        for r in results:
            if r.ssid == "wtf-scantest":
                found = r
                break

        self.failIf(found == None, "Failed to find ssid wtf-scantest")
        self.failIf(r.channel != 11, "Expected wtf-scantest on channel 11")

    def test_open_associate(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-assoctest", channel=6)

        self.startNodes()
        self.assocTest()
        self.pingTest()
        self.throughput()
        #self.stressTest()

    def test_wpa_psk_tkip_assoc(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-wpatest",
                                          security=AP.SECURITY_WPA,
                                          auth=AP.AUTH_PSK,
                                          password="thisisasecret",
                                          encrypt=AP.ENCRYPT_TKIP)
        self.startNodes()
        self.assocTest()
        self.pingTest()

    def test_wpa2_psk_tkip_assoc(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-wpatest",
                                            security=AP.SECURITY_WPA2,
                                            auth=AP.AUTH_PSK,
                                            password="thisisasecret",
                                            encrypt=AP.ENCRYPT_TKIP)
        self.startNodes()
        self.assocTest()
        self.pingTest()

    def test_wpa_psk_ccmp_assoc(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-wpatest",
                                          security=AP.SECURITY_WPA,
                                          auth=AP.AUTH_PSK,
                                          password="thisisasecret",
                                          encrypt=AP.ENCRYPT_CCMP)
        self.startNodes()
        self.assocTest()
        self.pingTest()

    def test_wpa2_psk_ccmp_assoc(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-wpatest",
                                            security=AP.SECURITY_WPA2,
                                            auth=AP.AUTH_PSK,
                                            password="thisisasecret",
                                            encrypt=AP.ENCRYPT_CCMP)
        self.startNodes()
        self.assocTest()
        self.pingTest()

