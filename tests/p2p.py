import wtf, time, unittest
wtfconfig = wtf.conf

def setUp(self):
    for n in wtfconfig.nodes:
        n.shutdown()
        n.init()

def tearDown(self):
    for n in wtfconfig.nodes:
        n.stop()

class TestP2P(unittest.TestCase):

    def setUp(self):
        for n in wtfconfig.nodes:
            n.stop()

    def test_find(self):
        wtfconfig.p2ps[0].start()
        wtfconfig.p2ps[1].start()
        wtfconfig.p2ps[0].find_start()
        wtfconfig.p2ps[1].find_start()
        count = 10
        while count != 0:
            peers = wtfconfig.p2ps[0].peers()
            for p in peers:
                if p.mac == wtfconfig.p2ps[1].mac and \
                       p.name == wtfconfig.p2ps[1].name:
                    return
            count = count - 1
            time.sleep(1)
        self.failIf(1, "%s failed to find %s" % (wtfconfig.p2ps[0].name,
                                                 wtfconfig.p2ps[1].name))
