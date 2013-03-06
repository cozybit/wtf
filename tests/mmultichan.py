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

    def test_0_single_hop(self):
        fname = sys._getframe().f_code.co_name

        dst_ip = sta[1].configs[0].iface.ip
        perf_report = do_perf([sta[0], sta[1]], dst_ip)

        results[fname] = LinkReport(perf_report=perf_report)

    def test_1_dual_single_hop(self):
        fname = sys._getframe().f_code.co_name

# separate one of the interfaces at IP layer
        subnet = "192.168.22."
        old_ip1 = sta[1].configs[1].iface.ip
        old_ip2 = sta[2].configs[0].iface.ip
        dst_1 = sta[1].configs[0].iface.ip
        dst_2 = subnet + "2"
        sta[1].configs[1].iface.ip = subnet + "1"
        sta[2].configs[0].iface.ip = dst_2
        sta[1].reconf()
        sta[2].reconf()

        sta[1].perf_serve(dst_ip=dst_1)
        sta[2].perf_serve(dst_ip=dst_2)
        sta[0].perf_client(dst_ip=dst_1, timeout=10, b=100, fork=True)
        sta[1].perf_client(dst_ip=dst_2, timeout=10, b=100)

        perf_report = sta[1].get_perf_report()
        results[fname + "_a"] = LinkReport(perf_report=perf_report)
        perf_report = sta[2].get_perf_report()
        results[fname + "_b"] = LinkReport(perf_report=perf_report)

        sta[1].configs[1].iface.ip = old_ip1
        sta[2].configs[0].iface.ip = old_ip2

    def test_2_bridge(self):
        fname = sys._getframe().f_code.co_name
        dst_ip = sta[2].configs[0].iface.ip

        if1 = sta[1].configs[0].iface
        if2 = sta[1].configs[1].iface
        sta[1].bridge([if1, if2], sta[1].configs[0].iface.ip)

        perf_report = do_perf([sta[0], sta[2]], dst_ip)
        results[fname] = LinkReport(perf_report=perf_report)

    def test_3_mmbss(self):
        fname = sys._getframe().f_code.co_name
        dst_ip = sta[2].configs[0].iface.ip

        # enable in-kernel intra-vif forwarding
        sta[1].configs[0].shared = True
        sta[1].configs[1].shared = True
        sta[1].reconf()

        perf_report = do_perf([sta[0], sta[2]], dst_ip)
        results[fname] = LinkReport(perf_report=perf_report)
