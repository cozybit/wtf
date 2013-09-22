# Copyright cozybit, Inc 2010-2011
# All rights reserved

"""
Simple test of throughput from one zotac to another.
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

ref_clip = os.getenv("REF_CLIP")
# XXX: nose probably has something like this?
results={}

# global setup, called once during this suite
def setUp(self):

# if_1 <-> if_2 <-> if_3
    global if_1
    global if_2
    global if_3
    global if_4

    print sta
    if_1 = sta[0].iface[0]
    if_2 = sta[1].iface[0]
    if_3 = sta[2].iface[0]
    if_4 = sta[3].iface[0]

    for n in wtfconfig.mps:
        n.shutdown()
        n.init()
        n.start()

def tearDown(self):
    for n in wtfconfig.nodes:
        n.stop()

    print "                                                     ref_clip=%s" % (ref_clip,)
    print_linkreports(results)

class SimpleMeshTest(unittest.TestCase):

# run before / after each test
    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_1_throughput(self):
        fname = sys._getframe().f_code.co_name

        dst_ip = if_2.ip

        perf_report = do_perf([if_1, if_2], dst_ip)

        results[fname] = LinkReport(perf_report=perf_report)

    def test_2_same_ch_mhop(self):
        fname = sys._getframe().f_code.co_name

        # do a -> b -> c
        ifs = [if_1, if_2, if_3]
        for iface in ifs:
            if iface != if_2:
                iface.conf.mesh_params = "mesh_auto_open_plinks=0"
            iface.conf.channel = 1
            iface.node.reconf()

        if_1.add_mesh_peer(if_2)
        if_3.add_mesh_peer(if_2)

        perf_report = do_perf([if_1, if_3], if_3.ip)
        # test multi-hop performance using a single radio for forwarding
        results[fname] = LinkReport(perf_report=perf_report)
        if_2.dump_mesh_stats()

    def test_3_single_hop(self):
        fname = sys._getframe().f_code.co_name

        perf_report = do_perf([if_1, if_2], if_2.ip)
        results[fname + "_ab"] = LinkReport(perf_report=perf_report)
        perf_report = do_perf([if_3, if_4], if_4.ip)
        results[fname + "_cd"] = LinkReport(perf_report=perf_report)

    def test_4_sim_single_hop(self):
        fname = sys._getframe().f_code.co_name

# separate one of the links at IP layer
        old_ipc = if_3.ip
        old_ipd = if_4.ip

        subnet = "192.168.22.15"
        if_3.ip = subnet + "4"
        if_4.ip = subnet + "5"
        if_3.node.reconf()
        if_4.node.reconf()

        if_2.perf_serve()
        if_4.perf_serve()
        if_1.perf_client(dst_ip=if_2.ip, timeout=10, b=100, fork=True)
        if_3.perf_client(dst_ip=if_4.ip, timeout=10, b=100)

        perf_report = if_2.get_perf_report()
        results[fname + "_ab"] = LinkReport(perf_report=perf_report)
        perf_report = if_4.get_perf_report()
        results[fname + "_cd"] = LinkReport(perf_report=perf_report)

        if_3.ip = old_ipc
        if_4.ip = old_ipd

    def test_5_same_ch_mhop(self):
        fname = sys._getframe().f_code.co_name

        # do a -> b -> d
# disable c
        if_3.enable = False
        if_3.node.reconf()

        ifs = [if_1, if_2, if_4]
        for iface in ifs:
            if iface != if_2:
                iface.conf.mesh_params = "mesh_auto_open_plinks=0"
            iface.conf.channel = 1
            iface.node.reconf()

        if_1.add_mesh_peer(if_2)
        if_4.add_mesh_peer(if_2)

        perf_report = do_perf([if_1, if_4], if_4.ip)
        # test multi-hop performance using a single radio for forwarding
        results[fname] = LinkReport(perf_report=perf_report)
        if_2.dump_mesh_stats()

    def test_6_path_selection(self):
        fname = sys._getframe().f_code.co_name

        dst_if = if_4 # can be changed here as more nodes are added

        ifs = [if_1, if_2, if_3, if_4]
        for iface in ifs:
            if iface == if_1 or iface == dst_if: # source or dest
                iface.conf.mesh_params = "mesh_auto_open_plinks=0"
            iface.conf.channel = 1
            iface.node.reconf()

        if_1.add_mesh_peer(if_2)
        if_1.add_mesh_peer(if_3)

        if_4.add_mesh_peer(if_2)
        if_4.add_mesh_peer(if_3)

        perf_report = do_perf([if_1, dst_if], dst_if.ip)
        results[fname] = LinkReport(perf_report=perf_report)
        if_2.dump_mesh_stats()
        if_3.dump_mesh_stats()
