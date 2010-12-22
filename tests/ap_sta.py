"""
Test infrastructure sta/ap connectivity
"""

import wtfconfig
import wtf.node.ap as AP
import unittest
import time

def setUp(self):
    # start with all of the nodes initialized by idle
    for n in wtfconfig.nodes:
        n.shutdown()
        n.init()

class TestAPSTA(unittest.TestCase):

    def setUp(self):
        # start with all of the nodes stopped
        for n in wtfconfig.nodes:
            n.stop()

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
        wtfconfig.ap.start()
        wtfconfig.ap.set_ip("192.168.99.1")

        wtfconfig.sta.start()
        self.failIf(wtfconfig.sta.assoc(wtfconfig.ap.config),
                    "Failed to associate with AP")
        wtfconfig.sta.set_ip("192.168.99.2")
        self.failIf(wtfconfig.sta.ping("192.168.99.1") != 0,
                    "Failed to ping AP at 192.168.99.1")

    def test_wpa_psk_tkip_assoc(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-wpatest",
                                          security=AP.SECURITY_WPA,
                                          auth=AP.AUTH_PSK,
                                          password="thisisasecret",
                                          encrypt=AP.ENCRYPT_TKIP)
        wtfconfig.ap.start()
        wtfconfig.ap.set_ip("192.168.99.1")

        wtfconfig.sta.start()
        self.failIf(wtfconfig.sta.assoc(wtfconfig.ap.config),
                    "Failed to associate with AP")
        wtfconfig.sta.set_ip("192.168.99.2")
        self.failIf(wtfconfig.sta.ping("192.168.99.1") != 0,
                    "Failed to ping AP at 192.168.99.1")

    def test_wpa2_psk_tkip_assoc(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-wpatest",
                                            security=AP.SECURITY_WPA2,
                                            auth=AP.AUTH_PSK,
                                            password="thisisasecret",
                                            encrypt=AP.ENCRYPT_TKIP)
        wtfconfig.ap.start()
        wtfconfig.ap.set_ip("192.168.99.1")

        wtfconfig.sta.start()
        self.failIf(wtfconfig.sta.assoc(wtfconfig.ap.config),
                    "Failed to associate with AP")
        wtfconfig.sta.set_ip("192.168.99.2")
        self.failIf(wtfconfig.sta.ping("192.168.99.1") != 0,
                "Failed to ping AP at 192.168.99.1")

    def test_wpa_psk_ccmp_assoc(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-wpatest",
                                          security=AP.SECURITY_WPA,
                                          auth=AP.AUTH_PSK,
                                          password="thisisasecret",
                                          encrypt=AP.ENCRYPT_CCMP)
        wtfconfig.ap.start()
        wtfconfig.ap.set_ip("192.168.99.1")

        wtfconfig.sta.start()
        self.failIf(wtfconfig.sta.assoc(wtfconfig.ap.config),
                    "Failed to associate with AP")
        wtfconfig.sta.set_ip("192.168.99.2")
        self.failIf(wtfconfig.sta.ping("192.168.99.1") != 0,
                    "Failed to ping AP at 192.168.99.1")

    def test_wpa2_psk_ccmp_assoc(self):
        wtfconfig.ap.config = AP.APConfig(ssid="wtf-wpatest",
                                            security=AP.SECURITY_WPA2,
                                            auth=AP.AUTH_PSK,
                                            password="thisisasecret",
                                            encrypt=AP.ENCRYPT_CCMP)
        wtfconfig.ap.start()
        wtfconfig.ap.set_ip("192.168.99.1")

        wtfconfig.sta.start()
        self.failIf(wtfconfig.sta.assoc(wtfconfig.ap.config),
                    "Failed to associate with AP")
        wtfconfig.sta.set_ip("192.168.99.2")
        self.failIf(wtfconfig.sta.ping("192.168.99.1") != 0,
                "Failed to ping AP at 192.168.99.1")
