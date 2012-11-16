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
mon = wtfconfig.mons[0]

CAP_FILE="/tmp/mcca.cap"

BCN_INTVL=1000 #TUs
DTIM_PERIOD=2
DTIM_INTVL=BCN_INTVL * DTIM_PERIOD

# current target accuracy (us)
ACCURACY=256

# offset and duration are in 32us units
class MCCARes():
    def __init__(self, offset, duration, period):
        self.offset = offset
        self.duration = duration
        self.period = period

# XXX: factor these into a wtfutils module or something
def tu_to_s(tu):
    return tu * 1024 / 1000 / float(1000)

def tu_to_us(tu):
    return tu * 32 * 32

# return packets found in tshark_filter
def do_tshark(cap_file, tshark_filter, extra=""):
    r, o = commands.getstatusoutput("tshark -r" + cap_file + " -R'" + tshark_filter +
                                    "' " + extra + " 2> /dev/null")
    if r != 0 and r != 256:
        raise Exception("tshark error %d! Is tshark installed and %s exists? Please verify filter %s" % (r, cap_file, tshark_filter))
    return o

# returns 0 if no traffic was transmitted by peer from tstop to tstart
def check_no_traffic(cap_file, peer, tstop, tstart):
    tstop = int(tstop + (ACCURACY / 2.0))
    tstart = int(tstart - (ACCURACY / 2.0))
# TODO: not only data frames are disallowed (?)
    print "checking for data from " + str(tstop) + " to " + str(tstart) + " by " + peer.mac
    output = do_tshark(cap_file, "wlan.ta == " + peer.mac + " && data && (radiotap.mactime > " +\
                       str(tstop) + " && radiotap.mactime < " + str(tstart) + ")")
    if output:
        print output
        return -1
    return 0

# parse beacon received at rx_t for owner or responder reservations.
# returns a list of MCCARes reservation slots,
# all units are in 32us units
def get_mcca_res(cap_file, rx_t, owner=False):
    import struct
    res_type="res"
    if owner:
        res_type="own"

    ress = []
    raw_res = do_tshark(cap_file, "radiotap.mactime == " + str(rx_t),
                        "-Tfields -e wlan_mgt.cozybit.ie.mccaop." + res_type)

    raw_res = raw_res.split(":")
    i = 0
    while i < int(raw_res[0], 16):
        idx = i * 5
        duration = int(raw_res[idx + 1], 16)
        period = int(raw_res[idx + 2], 16)
        offset = "".join(raw_res[idx + 3 : idx + 6]) + "00"
        offset = struct.unpack("<L", offset.decode('hex'))
        ress.append(MCCARes(offset[0], duration, period))
        i += 1

    return ress

# check whether peer transmitted during owner's reservation
# owner_dtim is a flag controlling who's DTIM we'll check against. Set
# owner_dtim=False to merely check the parameters reported in the responder
# DTIM beacon.
def check_mcca_res(owner, responder, cap_file=None, owner_dtim=True):
    if not cap_file:
        cap_file = responder.local_cap
    rel_dtim = owner.mac
    if not owner_dtim:
        rel_dtim = responder.mac

    bcns = do_tshark(cap_file, "wlan.sa == " + rel_dtim + " && (wlan_mgt.tim.dtim_count == 0)",
                     "-Tfields -e radiotap.mactime -e wlan_mgt.fixed.timestamp -e radiotap.datarate")
# (dtim TBTT, [res periods for DTIM])
    abs_dtims = []
    for bcn in bcns.splitlines():
        rx_t = int(bcn.split()[0])
        ts = int(bcn.split()[1], 16)
# adjust rx_t to account for beacon header tx time, since beacon timestamp is
# when that field hits the transmitting phy
# (24 bytes of header * 8 bits/byte) / rate(Mbps)
        hdr_t = (24 * 8 ) / int(bcn.split()[2])
        ress = get_mcca_res(cap_file, rx_t, owner_dtim)
        abs_dtims.append((rx_t - (ts % tu_to_us(DTIM_INTVL) + hdr_t), ress))

    for dtim in abs_dtims:
        print "DTIM by " + rel_dtim  + " at " + str(dtim[0])  + " in " + cap_file
        for res in dtim[1]:
            tstop = dtim[0] + res.offset * 32
            tstart = tstop + res.duration * 32
            for i in range(res.period):
                if check_no_traffic(cap_file, responder, tstop, tstart):
                    return -1
                tstop = tstop + float(tu_to_us(DTIM_INTVL)) / res.period
                tstart = tstop + res.duration * 32
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
    sta[0].res = MCCARes(offset=100 * 32, duration=255, period=16)
    sta[1].res = MCCARes(offset=300 * 32, duration=255, period=16)
    sta[2].res = MCCARes(offset=550 * 32, duration=255, period=16)
    sta[3].res = MCCARes(offset=800 * 32, duration=255, period=16)

# start with just STA1 and 2 in the mesh
    i = 0
    for n in wtfconfig.mps:
        n.shutdown()
        n.init()
        if i < 2:
            n.start()
            n.mccatool_start()
            # avoid race with other nodes
            time.sleep(tu_to_s(BCN_INTVL))
            n.set_mcca_res()
        i += 1

# let reservations propagate before we start capturing
    time.sleep(tu_to_s(DTIM_INTVL))

# initialize monitor node
    mon.shutdown()
    mon.init()
    mon.start()

def tearDown(self):
    for n in wtfconfig.nodes:
        n.stop()

class TestMCCA(unittest.TestCase):

# setUp and tearDown are called by nose before / after each test, but all tests
# are a continuation of eachother, so do nothing between tests
    def setUp(self):
        pass

    def tearDown(self):
# TODO generate cool gnuplot!
# save old capture?
        pass

    def test_kern_sched(self):
# test kernel scheduling with some dummy peer reservation parameters
        # mccatool will advertise responder periods some offset from local
        # DTIM, we assume these have been correctly programmed into the kernel
        # and judge scheduling latency based on that.
        mon.start_capture()
# send traffic
        sta[0].perf()
        sta[1].perf(sta[0].ip, timeout=10, dual=True, b="60M")
        sta[0].killperf()
        sta[1].killperf()
        mon.stop_capture(CAP_FILE + "0")

        self.failIf(check_mcca_res(sta[0], sta[1], mon.local_cap, False), "failed")
        self.failIf(check_mcca_res(sta[1], sta[0], mon.local_cap, False), "failed")

    def test_1(self):
        mon.start_capture()
# send traffic
        sta[0].perf()
        sta[1].perf(sta[0].ip, timeout=10, dual=True, b="60M")
        sta[0].killperf()
        sta[1].killperf()
        mon.stop_capture(CAP_FILE + "1")

# verify against the 3rd party capture
        self.failIf(check_mcca_res(sta[0], sta[1], mon.local_cap) != 0, "failed")
        self.failIf(check_mcca_res(sta[1], sta[0], mon.local_cap) != 0, "failed")

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
