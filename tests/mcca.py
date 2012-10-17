# Copyright cozybit, Inc 2010-2011
# All rights reserved

"""
Test mesh MCCA deliverables as per the SoW:

	Test 1:
	-------
		STA1 and STA2 with MCCA enabled
		Generate continuous mcast and unicast traffic at each STA.
		PASS: traffic is transmitted only during alloted intervals

	Test 2:
	-------
		Add STA3 w/ MCCA on and STA4 w/ MCCA off
		Generate continuous mcast and unicast traffic at each STA.
		PASS: traffic is transmitted only during alloted intervals,
		except from STA4 who has no MCCA knowledge

	Test 3:
	-------
		Enable MCCA at STA4. Generate traffic and verify traffic is
		transmitted only during allotted intervals.

	Test 4:
	-------
		Disable MCCA reservations at STA1 and STA2, they should
		transmit whenever they please, while STA3 and STA4 still
		respects each other's MCCAOPs

PASS CRITERIA:
	Peer MCCAOPs are respected
"""

import wtf.node.mesh as mesh
import unittest
import time
import wtf

wtfconfig = wtf.conf
sta = wtfconfig.mps

# global setup, called once during this suite
def setUp(self):
# start with just STA1 and 2
    for n in wtfconfig.nodes[:2]:
        n.shutdown()
        n.init()

class TestMCCA(unittest.TestCase):

# setUp and tearDown are called by nose before / after each test, but all tests
# are a continuation of eachother, so do nothing between tests
    def setUp(self):
        pass

    def test_1(self):
# start capturing
        sta[0].start_capture()
# install reservations
        sta[0].set_mcca_res(sta[1])
        sta[1].set_mcca_res(sta[0])
# send traffic
        sta[0].perf()
        sta[1].perf(sta[0].ip, timeout=10)

        sta[0].killperf()
        sta[1].killperf()
        sta[0].stop_capture()
# stop capturing
