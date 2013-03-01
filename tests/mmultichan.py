# Copyright cozybit, Inc 2010-2013
# All rights reserved
"""
Test Mesh multichannel operation.

Topology:
    sta[0] <-> sta[1] <-> sta[2]

    sta[0] is on channel 1, sta[2] is on channel 12.
    sta[1] becomes a natural forwarding node by having two vifs on ch. 1 and 12

Tests:
    1. bridge baseline throughput, why not just use a linux bridge?
    2. throughput with in-kernel forwarding between vifs
"""

import wtf.node.mesh as mesh
import unittest
import time
import wtf
from wtf.util import *
import sys; err = sys.stderr
import time
import os

wtfconfig = wtf.conf
sta = wtfconfig.mps

results={}

# global setup, called once during this suite
def setUp(self):
    for n in wtfconfig.mps:
        n.shutdown()
        n.init()
        n.start()

def tearDown(self):
    for n in wtfconfig.nodes:
        n.stop()

    print_linkreports(results)

class TestMMBSS(unittest.TestCase):
    def setUp(self):
        for n in wtfconfig.nodes:
            n.stop()
            n.start()
        pass

    def tearDown(self):
        pass

    def test_0_baseline(self):
        fname = sys._getframe().f_code.co_name

        dst_ip = sta[1].configs[0].iface.ip
        perf_report = do_perf([sta[0], sta[1]], dst_ip)

        results[fname] = LinkReport(perf_report=perf_report)

    def test_1_bridge(self):
        fname = sys._getframe().f_code.co_name
        dst_ip = sta[2].configs[0].iface.ip

        if1 = sta[1].configs[0].iface
        if2 = sta[1].configs[1].iface
        sta[1].bridge([if1, if2], sta[1].configs[0].iface.ip)

        perf_report = do_perf([sta[0], sta[2]], dst_ip)
        results[fname] = LinkReport(perf_report=perf_report)

    def test_2_mmbss(self):
        fname = sys._getframe().f_code.co_name
        dst_ip = sta[2].configs[0].iface.ip

        # TODO: set vif forwarding = true and reconf

        perf_report = do_perf([sta[0], sta[2]], dst_ip)
        results[fname] = LinkReport(perf_report=perf_report)
