# Copyright cozybit, Inc 2010-2012
# All rights reserved

import wtf.node as node
import sys; err = sys.stderr

class SnifferBase(node.NodeBase) :
    """
    Sniffer STA

    This represents a platform-independent monitor STA that should be used by tests.

    Real Sniffer STAs should extend this class and implement the actual AP functions.
    """

    def __init__(self, comm):
        """
        Create sniffer STA with the supplied default configuration.
        """
        node.NodeBase.__init__(self, comm=comm)

class SnifferConf():

    def __init__(self, channel=1, htmode=""):
        self.channel = channel
        self.htmode = htmode

class SnifferSTA(node.LinuxNode, SnifferBase):
    def __init__(self, comm, iface, driver=None):
        node.LinuxNode.__init__(self, comm, iface, driver)
        self.config = None

    def start(self):
        # XXX: self.stop() should work since we extend LinuxNode?? 
        node.LinuxNode.stop(self)
        self._cmd_or_die("iw " + self.iface + " set type monitor")
        node.LinuxNode.start(self)
        self._cmd_or_die("iw " + self.iface + " set channel " + str(self.config.channel) +
                         " " + self.config.htmode)
        self.monif = self.iface
        # XXX: where does it get this config???
        if not self.config:
            raise node.InsufficientConfigurationError()

    def stop(self):
        node.LinuxNode.stop(self)
