class config():
    def __init__(self, suites, aps=[], stas=[], name="<unamed config>"):
        """
        A wtf config is a list of suites to run and the nodes to run them on.
        """
        self.suites = suites
        self.aps = aps
        self.stas = stas
        self.nodes = aps + stas
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
