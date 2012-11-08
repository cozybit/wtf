# Copyright cozybit, Inc 2010-2012
# All rights reserved

import wtf.node as node
import sys; err = sys.stderr

class MeshBase(node.NodeBase):
    """
    Mesh STA

    This represents a platform-independent mesh STA that should be used by tests.

    Real Mesh STAs should extend this class and implement the actual AP functions.
    """

    def __init__(self, comm):
        """
        Create mesh STA with the supplied default configuration.
        """
        node.NodeBase.__init__(self, comm=comm)

class MeshConf():
    """
    Mesh STA configuration object

    Use this to set options for the MBSS; SSID, channel, etc.
    XXX: add support for authsae
    """

    def __init__(self, ssid, channel=1, htmode=""):
        self.ssid = ssid
        self.channel = channel
        self.htmode = htmode

class MeshSTA(node.LinuxNode, MeshBase):
    """
    mesh STA node
    """
    def __init__(self, comm, iface, driver=None):
        node.LinuxNode.__init__(self, comm, iface, driver)
        self.config = None
        self.mccapipe = None

    def start(self):
        # XXX: self.stop() should work since we extend LinuxNode?? 
        node.LinuxNode.stop(self)
        self._cmd_or_die("iw " + self.iface + " set type mp")
        #self.set_iftype("mesh")
        node.LinuxNode.start(self)
        #node.set_channel(self.config.channel)
        self._cmd_or_die("iw " + self.iface + " set channel " + str(self.config.channel) +
                         " " + self.config.htmode)
        # XXX: where does it get this config???
        if not self.config:
            raise node.InsufficientConfigurationError()
        #self._configure()
        self._cmd_or_die("iw " + self.iface + " mesh join " + self.config.ssid)
        self.set_ip(self.ip)

    def stop(self):
        self.comm.send_cmd("iw " + self.iface + " mesh leave")
        self.mccatool_stop()
        node.LinuxNode.stop(self)

# empty owner means just configure own owner reservation, else install
# specified interference reservation.
    def set_mcca_res(self, owner=None):
        if not self.mccapipe:
            raise node.InsufficientConfigurationError()

        if owner != None:
            self._cmd_or_die("echo i %d %d %d > %s" % (owner.res.offset,
                                                       owner.res.duration,
                                                       owner.res.period,
                                                       self.mccapipe))
        else:
            self._cmd_or_die("echo a %d %d > %s" % (self.res.duration,
                                                    self.res.period,
                                                    self.mccapipe))

    def mccatool_start(self):
        if not self.mccapipe:
            import tempfile
            self.mccapipe = tempfile.mktemp()
            self._cmd_or_die("mkfifo %s" % self.mccapipe)
# keep the pipe open :|
            self._cmd_or_die("nohup sleep 10000 > %s &" % self.mccapipe)

        self._cmd_or_die("nohup mccatool %s > /tmp/mccatool.out 2> /dev/null < %s &" % (self.iface, self.mccapipe))

    def mccatool_stop(self):
        if self.mccapipe:
            self._cmd_or_die("echo q > %s" % self.mccapipe)
            self._cmd_or_die("rm %s" % self.mccapipe)
            self.mccapipe = None
