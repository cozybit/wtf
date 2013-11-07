# Copyright cozybit, Inc 2010-2011
# All rights reserved

"""
Simple test of throughput from one mesh node to another.
"""

import wtf.node.mesh as mesh
from wtf.util import *
import unittest
import wtf
import sys
import os

err = sys.stderr
wtfconfig = wtf.conf
sta = wtfconfig.mps

ref_clip = os.getenv("REF_CLIP")
# XXX: nose probably has something like this?
path_heal_time = {}
results = {}

# set default test results and override if provided
exp_results = {"test1": 0.01, "test2": 0.01}
if len(wtfconfig.exp_results) > 0:
    exp_results = wtfconfig.exp_results


# global setup, called once during this suite
def setUp(self):

# if_1 <-> if_2 <-> if_3
    global if_1
    global if_2
    global if_3

    if_1 = sta[0].iface[0]
    if_2 = sta[1].iface[0]
    if_3 = sta[2].iface[0]

    for n in wtfconfig.mps:
        n.shutdown()
        n.init()
        n.start()


def tearDown(self):
    for n in wtfconfig.nodes:
        n.stop()

    print "                                                     \
            ref_clip=%s" % (ref_clip,)
    if len(results) > 0:
        print_linkreports(results)
    if len(path_heal_time) > 0:
        print "Path healed in:        " + str(path_heal_time["path_heal"]) + " seconds"


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
        self.failIf(perf_report.tput < (exp_results["test1"]),
                    "reported throughput (" + str(perf_report.tput) + ") is \
                    lower than expected (" + str(exp_results["test1"]) + ")")

    def test_2_same_ch_mhop(self):
        fname = sys._getframe().f_code.co_name

        # do a -> b -> c
        ifs = [if_1, if_2, if_3]
        for iface in ifs:
            if iface != if_2:
                iface.conf.mesh_params = "mesh_auto_open_plinks=0"
            iface.node.reconf()

        if_1.add_mesh_peer(if_2)
        if_3.add_mesh_peer(if_2)

        perf_report = do_perf([if_1, if_3], if_3.ip)
        # test multi-hop performance using a single radio for forwarding
        results[fname] = LinkReport(perf_report=perf_report)
        if_2.dump_mesh_stats()
        self.failIf(perf_report.tput < (exp_results["test2"]),
                    "reported throughput (" + str(perf_report.tput) + ") is \
                    lower than expected (" + str(exp_results["test2"]) + ")")

    def test_3_path_healing(self):
        """Kill a radio, then bring back and measure path heal time."""
        count = 30
        interval = .1
        found = 0

        # check if ping is alive
        ping_results = if_1.node.ping(if_2.ip, count=3).stdout
        ping_results = ping_results[-2]
        self.failIf(ping_results.find("100%") != -1, "not connected on initial ping")

        # turn off radio and ping to make sure we drop all packets
        if_2.set_radio(0)
        ping_results = if_1.node.ping(if_2.ip, count=20, interval=.1, timeout=20).stdout
        ping_results = ping_results[-2]
        self.failIf(ping_results.find("100%") == -1,
                    "still connected")
        if_1.dump_mpaths()

        # turn back on radio and start ping
        if_2.set_radio(1)
        ping_results = if_1.node.ping(if_2.ip, count=count, interval=interval).stdout
        # look for first icmp_seq= and grab the request number
        for icmp in ping_results[1:]:
            if icmp.find("icmp_seq="):
                found = int(icmp.split(" ")[4][9:])
                break
        self.failIf(found == 0,
                    "Never reconnected after %d seconds" % (count * interval))

        #expects no loss after reconnected
        path_heal_time["path_heal"] = found * interval
