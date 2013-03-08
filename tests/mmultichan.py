# Copyright cozybit, Inc 2010-2013
# All rights reserved
"""
Test Mesh multichannel operation.

Topology:
    sta[0]     sta[1]       sta[2]
    if_a <-> [if_b|if_c] <-> if_d

    if_a and if_b are on channel 1, if_c and if_d are on channel 149.

Tests:
    0. single-hop baseline throughput
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
    global if_a
    global if_b
    global if_c
    global if_d

    for n in wtfconfig.mps:
        n.shutdown()
        n.init()
        n.start()

# if_a -> if_b, if_c -> if_d
        if_a = sta[0].iface[0]
        if_b = sta[1].iface[1] # switched
        if_c = sta[1].iface[0] # because only the [0] interface supports ch. 149
        if_d = sta[2].iface[0]

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

        perf_report = do_perf([if_a, if_b], if_b.ip)
        results[fname + "_ab"] = LinkReport(perf_report=perf_report)
        perf_report = do_perf([if_c, if_d], if_d.ip)
        results[fname + "_cd"] = LinkReport(perf_report=perf_report)

    def test_1_sim_single_hop(self):
        fname = sys._getframe().f_code.co_name

# separate one of the links at IP layer
        old_ipc = if_c.ip
        old_ipd = if_d.ip

        subnet = "192.168.22."
        if_c.ip = subnet + "1"
        if_d.ip = subnet + "2"
        if_c.node.reconf()
        if_d.node.reconf()

        if_b.perf_serve()
        if_d.perf_serve()
        if_a.perf_client(dst_ip=if_b.ip, timeout=10, b=100, fork=True)
        if_c.perf_client(dst_ip=if_d.ip, timeout=10, b=100)

        perf_report = if_b.get_perf_report()
        results[fname + "_ab"] = LinkReport(perf_report=perf_report)
        perf_report = if_d.get_perf_report()
        results[fname + "_cd"] = LinkReport(perf_report=perf_report)

        if_c.ip = old_ipc
        if_d.ip = old_ipd

    def test_2_bridge(self):
        fname = sys._getframe().f_code.co_name
        dst_ip = sta[2].iface[0].ip

        sta[1].bridge([if_b, if_c], if_c.ip)

        perf_report = do_perf([if_a, if_d], if_d.ip)
        results[fname] = LinkReport(perf_report=perf_report)

    def test_3_mmbss(self):
        fname = sys._getframe().f_code.co_name

        # enable in-kernel intra-vif forwarding
        if_b.conf.shared = True
        if_c.conf.shared = True
        sta[1].reconf()

        perf_report = do_perf([if_a, if_d], if_d.ip)
        results[fname] = LinkReport(perf_report=perf_report)

    def test_4_same_ch_mhop(self):
        fname = sys._getframe().f_code.co_name

        # do a -> b -> d
# disable c
        if_c.enable = False
        if_c.node.reconf()

        ifs = [if_a, if_b, if_d]
        for iface in ifs:
            if iface != if_b:
                iface.conf.mesh_params = "mesh_auto_open_plinks=0"
            iface.conf.channel = 1
            iface.node.reconf()

        import time
        time.sleep(3)
        if_a.add_mesh_peer(if_b)
        if_d.add_mesh_peer(if_b)

        perf_report = do_perf([if_a, if_d], if_d.ip)
        # test multi-hop performance using a single radio for forwarding
        results[fname] = LinkReport(perf_report=perf_report)
