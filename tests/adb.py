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

results={}

def setUp(self):
    global if_1
    global if_2

    if_1 = sta[0].iface[0]
    if_2 = sta[1].iface[0]

    for n in wtfconfig.mps:
        n.shutdown()
        n.init()
        n.start()

def tearDown(self):
    for n in wtfconfig.nodes:
        n.stop()

    print "                                                     ref_clip=%s" % (ref_clip,)
    print_linkreports(results)

class adbTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_1_iperf(self):
        fname = sys._getframe().f_code.co_name

        dst_ip = if_2.ip

        perf_report = do_perf([if_1, if_2], dst_ip)

        results[fname] = LinkReport(perf_report=perf_report)
