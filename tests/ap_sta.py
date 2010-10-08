"""
Test infrastructure sta/ap connectivity
"""

import wtfconfig
import wtf.node.ap
import unittest

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
        wtfconfig.ap.config = wtf.node.ap.APConfig(ssid="wtf-scantest",
                                                   channel=11)
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
