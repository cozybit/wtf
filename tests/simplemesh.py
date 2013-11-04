# Copyright cozybit, Inc 2010-2011
# All rights reserved

"""
Simple test of throughput from one mesh node to another.
"""

import unittest
import wtf
from wtf.util import *
import sys; err = sys.stderr
import os

wtfconfig = wtf.conf
sta = wtfconfig.mps

ref_clip = os.getenv("REF_CLIP")
# XXX: nose probably has something like this?
results={}
path_heal_time = {}

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

    print "                                                     ref_clip=%s" % (ref_clip,)
    print_linkreports(results)
    print "Path healed in:        " + path_heal_time["path_heal"]

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

    def test_3_path_healing(self):
        """Kill a radio, then bring back and measure path heal time."""
        count = 100
        interval = .1

        # check if ping is alive
        _, ping_results = if_1.node.ping(if_2.ip, count=3)
        ping_results = ping_results.strip("\n")[-1]
        self.failIf(ping_results.find("100%"), "not connected on initial ping")

        # turn off radio and ping to make sure
        if_2.set_radio(0)
        _, ping_results = if_1.node.ping(if_2.ip, count=3)
        print "debug: ", ping_results
        ping_results = ping_results.strip("\n")[-1]
        print "debug: ", ping_results
        self.failIf(not ping_results.find("100%"),
                    "not connected on initial ping")

        # turn back on radio and start ping
        if_2.set_radio(1)
        _, ping_results = if_1.node.ping(if_2.ip,
                                         count=count, interval=interval)
        print "debug: ", ping_results
        ping_results = ping_results.strip("\n")[-1]
        print "debug: ", ping_results
        #the fifth is the packet loss hopefully
        ping_results = ping_results.strip(" ")[5]
        print "debug: ", ping_results
        #take off the precent sign
        ping_results = ping_results[0:-1]
        print "debug: ", ping_results
        self.failIf(int(ping_results) == 100,
                    "Never reconnected after %d seconds" % (count * interval))

        #expects no loss after reconnected
        path_heal_time["path_heal"] = (count * interval) - \
            (count * interval) * (ping_results / 100)
        print "debug: ", path_heal_time["path_heal"]
