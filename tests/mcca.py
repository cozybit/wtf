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
import sys; err = sys.stderr
import time
import commands

wtfconfig = wtf.conf
sta = wtfconfig.mps

CAP_FILE="/tmp/mcca.cap"

BCN_INTVL=1000 #TUs
DTIM_PERIOD=2
DTIM_INTVL=BCN_INTVL * DTIM_PERIOD

# current attainable accuracy (s)
ACCURACY=0.002

class MCCARes():
    def __init__(self, offset, duration, period):
        self.offset = offset
        self.duration = duration
        self.period = period

# XXX: factor these into a wtfutils module or something
def tu_to_s(tu):
    return tu * 1024 / 1000 / float(1000)

# return packets found in tshark_filter
def do_tshark(cap_file, tshark_filter):
    r, o = commands.getstatusoutput("tshark -r" + cap_file + " -R'" + tshark_filter + "'")
    if r != 0 and r != 256:
        raise Exception("tshark error %d! Is tshark installed and %s exists? Please verify filter %s" % (r, cap_file, tshark_filter))
    return o

# returns 0 if no traffic was transmitted by peer from tstop to tstart
def check_no_traffic(cap_file, peer, tstop, tstart):
    tstop = tstop + (ACCURACY / 2.0)
    tstart = tstart - (ACCURACY / 2.0)
    print "checking for data from " + str(tstop) + " to " + str(tstart) + " by " + peer.mac
    output = do_tshark(cap_file, "wlan.ta == " + peer.mac + " && data && (frame.time_relative > " +\
                       str(tstop) + " && frame.time_relative < " + str(tstart) + ")")
    if output:
        print output
        return -1
    return 0

# check whether peer transmitted during owner's reservation
def check_mcca_res(owner, peer):
    bcns = do_tshark(peer.local_cap, "wlan.sa == " + owner.mac + " && (wlan_mgt.tim.dtim_count == 0)")
    abs_dtims = [float(x.split()[1]) for x in bcns.splitlines()]

    for dtim_t in abs_dtims:
        print "DTIM by " + owner.mac  + " at " + str(dtim_t)  + " in " + peer.local_cap
        tstop = dtim_t + tu_to_s(owner.res.offset)
        tstart = tstop + tu_to_s(owner.res.duration)
        for i in range(owner.res.period):
            if check_no_traffic(peer.local_cap, peer, tstop, tstart):
                return -1
            tstop = tstop + float(tu_to_s(DTIM_INTVL)) / owner.res.period
            tstart = tstop + tu_to_s(owner.res.duration)
    return 0

# check peers in $peers respected our reservation
def check_mcca_peers(owner, peers):
    for peer in peers:
        if check_mcca_res(owner, peer):
            return -1
    return 0

def start_captures(stas):
    for sta in stas:
        sta.start_capture()

def stop_captures(stas):
    i = 0
    for sta in stas:
        sta.stop_capture(CAP_FILE + str(i))
        i += 1

def killperfs(stas):
    for sta in stas:
        sta.killperf()

# global setup, called once during this suite
def setUp(self):
    #XXX: check for collisions on these
    sta[0].res = MCCARes(offset=100, duration=8, period=16)
    sta[1].res = MCCARes(offset=300, duration=8, period=16)
    sta[2].res = MCCARes(offset=550, duration=8, period=16)
    sta[3].res = MCCARes(offset=800, duration=8, period=16)

# start with just STA1 and 2 in the mesh
    i = 0
    for n in wtfconfig.nodes:
        n.shutdown()
        n.init()
        if i < 3:
            n.start()
        i += 1

class TestMCCA(unittest.TestCase):

# setUp and tearDown are called by nose before / after each test, but all tests
# are a continuation of eachother, so do nothing between tests
    def setUp(self):
        pass

    def tearDown(self):
# TODO generate cool gnuplot!
# save old capture?
        pass

    def test_1(self):
# install reservations
        sta[0].set_mcca_res(sta[1])
        sta[1].set_mcca_res(sta[0])
        start_captures(sta[:3])
# send traffic
        sta[0].perf()
        # > 2M we get so many bmisses, no peer reservations are respected :(
        # This way, at least a few DTIM beacons are observed
        sta[1].perf(sta[0].ip, timeout=10, dual=True, b="60M")
        sta[0].killperf()
        sta[1].killperf()
        stop_captures(sta[:3])

        self.failIf(check_mcca_res(sta[0], sta[1]) != 0, "failed")
        self.failIf(check_mcca_res(sta[1], sta[0]) != 0, "failed")

    def test_2(self):
# add STA3 and 4 into the mix
        sta[2].start()
        sta[3].start()
# STA4 has no MCCA knowledge
        sta[0].set_mcca_res(sta[2])
        sta[1].set_mcca_res(sta[2])
        sta[2].set_mcca_res(sta[1])
        sta[2].set_mcca_res(sta[0])

        start_captures(sta)
        sta[0].perf(p=7000)
        sta[0].perf(p=7001)
        sta[0].perf(p=7002)

        sta[1].perf(sta[0].ip, timeout=10, dual=True, L=6666, p=7000, b="2M", fork=True)
        sta[2].perf(sta[0].ip, timeout=10, dual=True, L=6667, p=7001, b="2M", fork=True)
        sta[3].perf(sta[0].ip, timeout=10, dual=True, L=6668, p=7002, b="2M", fork=False)
        killperfs(sta)
        stop_captures(sta)

        self.failIf(check_mcca_peers(sta[0], sta[1:3]) != 0, "failed")
        self.failIf(check_mcca_peers(sta[1], [sta[0], sta[2]]) != 0, "failed")
        self.failIf(check_mcca_peers(sta[2], sta[0:2]) != 0, "failed")

# STA4 ignored everyone else's reservation
        self.failIf(check_mcca_res(sta[0], sta[3]) == 0, "STA4 respected STA0's reservation!")
        self.failIf(check_mcca_res(sta[1], sta[3]) == 0, "STA4 respected STA1's reservation!")
        self.failIf(check_mcca_res(sta[2], sta[3]) == 0, "STA4 respected STA2's reservation!")
