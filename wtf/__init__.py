import wtf.node.ap as ap
import wtf.node.sta as sta
import wtf.node.p2p as p2p

class config():
    def __init__(self, suite=None, nodes=[], name="<unamed config>"):
        """
        A wtf config is a list of suites to run and the nodes to run them on.
        """
        self.suite = suite
        self.nodes = nodes

        # populate node lists used by tests.
        self.aps = []
        self.stas = []
        self.p2ps = []
        for n in nodes:
            if isinstance(n, ap.APBase):
                self.aps.append(n)
            elif isinstance(n, sta.STABase):
                self.stas.append(n)
            elif isinstance(n, p2p.P2PBase):
                self.p2ps.append(n)

        self.name = name

    def setUp(self):
        """
        setUp is called before this configuration is run
        """
        pass

    def tearDown(self):
        """
        tearDown is called after the configuration is run
        """
        pass
