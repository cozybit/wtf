# These are mvdroid-specific tests for testing two mvdroid nodes against
# eachother.  Don't expect them to work for anything else.  On that note, don't
# expect the mvdroid nodes to pass any other test besides these.  C'est la vie.

import wtf, time, unittest
import wtf.node.p2p as p2p

wtfconfig = wtf.conf

def setUp(self):
    for n in wtfconfig.p2ps:
        if not isinstance(n, p2p.Mvdroid):
            raise Exception("mvdroid tests only support mvdroid nodes")

    for n in wtfconfig.nodes:
        n.shutdown()
        n.init()

class TestMvdroid(unittest.TestCase):

    def setUp(self):
        for n in wtfconfig.nodes:
            n.stop()

    # Helper routines
    def expect_find(self, n0, n1):
        # expect that n1 shows up in n0's list of peers
        count = 10
        while count != 0:
            peers = n0.peers()
            for p in peers:
                if p.mac == n1.mac and \
                       p.name == n1.name:
                    return
            count = count - 1
            time.sleep(1)
        self.failIf(1, "%s failed to find %s" % (n0.name, n1.name))

    def expect_connect(self, node1, node2):
        ret = node1.connect_start(node2)
        self.failIf(ret != 0, "%s failed to initiate connection with %s" % \
                    (node1.name, node2.name))
        ret = node2.connect_finish(node1)
        self.failIf(ret != 0, node2.name + " failed to finish connection")
        ret = node1.connect_finish(node2)
        self.failIf(ret != 0, node1.name + " failed to finish connection")

        node1.set_ip("192.168.88.1")
        node2.set_ip("192.168.88.2")
        self.failIf(node1.ping("192.168.88.1", timeout=5) != 0,
                    "%s failed to ping %s" % (node1.name, node2.name))

    def expect_pdreq(self, src, dest, method, expected_method):
        # Sometimes, we send a PDREQ but the target node is off channel in the
        # find phase.  So send a few.
        expected = ["module=wifidirect", "event=pd_req",
                    "device_id=%s" % src.mac.upper(),
                    "methods=%04X" % expected_method]
        dest.clear_events()
        src.clear_events()
        for i in range(1, 8):
            ret = src.pdreq(dest, method)
            self.failIf(ret != 0,
                        "%s failed to send pd req to %s" % \
                        (src.name, dest.name))

            # Other events (e.g, peer_found), may be in the queue.  So try a
            # few times to get the desired event.
            for i in range(1, 4):
                e = dest.get_next_event(timeout=1)
                if e == expected:
                    return;

        self.failIf(e != expected, "%s failed to rx pdreq" % (dest.name))

    def expect_find_eachother(self, node1, node2):
        node1.start()
        node2.start()
        node1.find_start()
        node2.find_start()
        self.expect_find(node1, node2)
        self.expect_find(node2, node1)

    # Actual tests start here
    def test_find_peer(self):
        wtfconfig.p2ps[0].start()
        wtfconfig.p2ps[1].start()
        wtfconfig.p2ps[0].find_start()
        wtfconfig.p2ps[1].find_start()
        self.expect_find(wtfconfig.p2ps[0], wtfconfig.p2ps[1])
        self.expect_find(wtfconfig.p2ps[1], wtfconfig.p2ps[0])

    def test_default_connect(self):
        node1 = wtfconfig.p2ps[0]
        node2 = wtfconfig.p2ps[1]
        node1.start()
        node2.start()
        node1.find_start()
        node2.find_start()

        self.expect_connect(node1, node2)

        # Finally, perform a traffic test
        node1.perf()
        node2.perf("192.168.88.1")
        node1.killperf()

    def test_only_initiator_starts_find(self):
        node1 = wtfconfig.p2ps[0]
        node2 = wtfconfig.p2ps[1]
        node1.start()
        node1.find_start()
        self.expect_find(node1, node2)
        self.expect_connect(node1, node2)

    def test_pdreq_success(self):
        node1 = wtfconfig.p2ps[0]
        node2 = wtfconfig.p2ps[1]
        self.expect_find_eachother(node1, node2)
        self.expect_pdreq(node1, node2, method=p2p.WPS_METHOD_PBC,
                          expected_method=p2p.WPS_METHOD_PBC)

    def test_pdreq_fail(self):
        node1 = wtfconfig.p2ps[0]
        node2 = wtfconfig.p2ps[1]
        self.expect_find_eachother(node1, node2)
        self.expect_pdreq(node1, node2, method=p2p.WPS_METHOD_LABEL,
                          expected_method=p2p.WPS_METHOD_NONE)
