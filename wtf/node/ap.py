import wtf.node as node

class APBase(node.NodeBase):
    """
    Access Point

    This represents the platform-independent AP that should be used by tests.

    Real APs should extend this class and implement the actual AP functions.
    """

    def __init__(self, comm):
        """
        Create an AP with the supplied default configuration.
        """
        self.defconfig = None
        node.NodeBase.__init__(self, comm=comm)

class APConfig():
    """
    Access Point configuration object

    Access Points have all sorts of configuration variables.  Perhaps the most
    familiar ones are the SSID and the channel.
    """

    def __init__(self, ssid, channel=None):
        self.ssid = ssid
        self.channel = channel

class APSet(APBase):
    """
    Represent a set of confiured APs in your vicinity as one configurable AP

    Sometimes, you just want to run a frickin' test against an AP in your
    office without having to go through the rigamarole of setting up something
    that wtf can have absolute control over.  If this sounds like you, you're
    in the right place.
    """

    def __init__(self, comm, configs):
        """
        create an AP that represents all the supplied configs
        """
        self.configs = configs
        APBase.__init__(self, comm)
