# Copyright cozybit, Inc 2010-2011
# All rights reserved

"""
Test mesh MCCA deliverables as per the SoW
"""

import wtf.node.mesh as mesh
import unittest
import time
import wtf

wtfconfig = wtf.conf
sta = wtfconfig.mps

class TestMCCA(unittest.TestCase):

# setUp and tearDown are called by nose before / after each test
    def setUp(self):
        for n in wtfconfig.nodes:
            n.shutdown()
            n.init()

    def test_init_shutdown(self):
        for n in wtfconfig.nodes:
            n.init()
            n.shutdown()
            n.init()
            n.shutdown()

    def test_ping(self):
        self.failIf(sta[0].ping(sta[1].ip, timeout=5) != 0,
                    "failed to ping sta1 at" + sta[1].ip)

