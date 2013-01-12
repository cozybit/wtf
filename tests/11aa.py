# Copyright cozybit, Inc 2010-2011
# All rights reserved

"""
Test mesh 11aa performance (using ath9k_htc cards)

These tests comprise scripts for assessing the feasibility of multicast HD
video over wifi. Things you will need:

    - qpsnr in your path, see: git://github.com/hsanson/qpsnr.git
    - cvlc installed on your test nodes
    - custom 9271 fw with mcast rate patch

    vlc (can't run as root):
        server:
        cvlc -I dummy $file :sout="#rtp{dst=$client_ip,port=5004,mux=ts,ttl=1}" :sout-all :sout-keep vlc://quit

        client:
        cvlc -I dummy rtp://$client_ip --sout file/ts:out.ts

    qpsnr:
        ./qpsnr -a avg_ssim -s100 -m1000 -o fpa=1000 -r <ref_vid> <recv_vid>
        ./qpsnr -a avg_psnr -s100 -m1000 -o fpa=1000 -r <ref_vid> <recv_vid>

TODO: The idea is to run these in a controlled environment simulating
"real-world" conditions by generating contention and collisions. For now the
tests are just run in an enclosure.

Each test surverys the link quality with iperf and some video streaming
metrics, but modifies the channel type and unicast / mcast address.
Test script:
    0. run UDP iperf and get throughput / losses
    1. stream video and do quality metric analysis
    2. change mesh conf for next test

We test the following link cases:
    1. unicast HT20.
    2. unicast noHT.
    3. mcast MCS7.
    4. mcast 54mb/s
"""

import wtf.node.mesh as mesh
import unittest
import time
import wtf
import sys; err = sys.stderr
import time
import commands

wtfconfig = wtf.conf
sta = wtfconfig.mps

# XXX: nose probably has something like this?
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
    print "TEST             THROUGHPUT(Mb/s)  LOSS(%)"
    for test, result in results.iteritems():
        print "%s       %s      %s" % (test,  result.tput, result.loss)

class Test11aa(unittest.TestCase):

# run before / after each test
    def setUp(self):
        pass

    def tearDown(self):
        pass

#XXX: our crude reporting only works if these are run in order!
    def test_1_unicast_ht20(self):
        sta[0].perf_serve()
        sta[1].perf_client(dst_ip=sta[0].ip, timeout=10, b=100)
        sta[0].killperf()
        print "server sta0 reports:"
        results[sys._getframe().f_code.co_name] = sta[0].perf.report

    def test_2_unicast_noht(self):
        #for n in wtfconfig.mps:
        #    conf = n.config
        #    conf.htmode = ""
        #    n.reconf(conf)
        pass

    def test_3_mcast_mcs7(self):
        # XXX: need new firmware, derp
        # better to support mcast_rate in kernel and 9271 firmware
        pass

    def test_4_mcast_54mbps(self):
        pass
