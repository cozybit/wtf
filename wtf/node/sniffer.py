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

    def __init__(self, channel=1, htmode="", iface=None):
        self.channel = channel
        self.htmode = htmode
        self.iface = iface

class SnifferSTA(node.LinuxNode, SnifferBase):
    def __init__(self, comm, ifaces, driver=None):
        node.LinuxNode.__init__(self, comm, ifaces, driver)
        self.configs = None

    def start(self):
        node.LinuxNode.stop(self)
        for conf in self.configs:
            self._cmd_or_die("iw " + conf.iface.name + " set type monitor")
            node.LinuxNode.start(self)
            self._cmd_or_die("iw " + conf.iface.name + " set channel " + str(conf.channel) +
                             " " + conf.htmode)
            conf.iface.monif = conf.iface

    def stop(self):
        node.LinuxNode.stop(self)
