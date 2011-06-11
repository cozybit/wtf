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
        node2.start()
        node1.find_start()
        self.expect_find(node1, node2)
        self.expect_connect(node1, node2)

    def test_pdreq(self):
        node1 = wtfconfig.p2ps[0]
        node2 = wtfconfig.p2ps[1]
        node1.start()
        node2.start()
        node1.find_start()
        node2.find_start()
        self.expect_find(node1, node2)
        self.expect_find(node2, node1)
        ret = node1.pdreq(node2)
        self.failIf(ret != 0,
                    "%s failed to send pd req to %s" % (node1.name, node2.name))
        # We'd like to test whether or not we actually got the pd req on the
        # other side.  But currently we don't have a way to get events into
        # this framework.  So we just let this go.
