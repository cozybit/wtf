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

    def __init__(self, ssid, channel=1, htmode="", security=0):
        self.ssid = ssid
        self.channel = channel
        self.htmode = htmode
        self.security = security

class MeshSTA(node.LinuxNode, MeshBase):
    """
    mesh STA node
    """
    def __init__(self, comm, iface, driver=None):
        node.LinuxNode.__init__(self, comm, iface, driver)
        self.config = None
        self.mccapipe = None

    def start(self):
    # This is the configuration template for the authsae config
        security_config_base = '''
/* this is a comment */
authsae:
{
 sae:
  {
    debug = 480;
    password = \\"thisisreallysecret\\";
    group = [19, 26, 21, 25, 20];
    blacklist = 5;
    thresh = 5;
    lifetime = 3600;
  };
 meshd:
  {
    meshid = \\"%s\\";
    interface = \\"%s\\";
    band = \\"11g\\";
    channel = %s;
    htmode = \\"none\\";
    mcast-rate = 12;
  };
};

''' % ( str(self.config.ssid), str(self.iface), str(self.config.channel))
        # XXX: self.stop() should work since we extend LinuxNode?? 
        node.LinuxNode.stop(self)
        #self.set_iftype("mesh")
        self._cmd_or_die("iw " + self.iface + " set type mp")
        #node.set_channel(self.config.channel)
        self._cmd_or_die("iw " + self.iface + " set channel " + str(self.config.channel) +
                         " " + self.config.htmode)
        node.LinuxNode.start(self)
        # XXX: where does it get this config???
        if not self.config:
            raise node.InsufficientConfigurationError()
        #self._configure()
        if self.config.security:
            self._cmd_or_die("echo -e \"" + security_config_base + "\"> /tmp/authsae.conf", verbosity=0);
            self._cmd_or_die("meshd-nl80211 -c /tmp/authsae.conf /tmp/authsae.log &")
        else:
            self._cmd_or_die("iw " + self.iface + " mesh join " + self.config.ssid)

    def stop(self):
        if self.config.security:
            self.comm.send_cmd("start-stop-daemon --quiet --stop --exec meshd-nl80211")
        else:
            self.comm.send_cmd("iw " + self.iface + " mesh leave")
        self.mccatool_stop()
        node.LinuxNode.stop(self)

# restart mesh with supplied new mesh conf
    def reconf(self, nconf):
            # LinuxNode.shutdown()????
            self.shutdown()
            self.config = nconf
            self.init()
            self.start()

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
            self.comm.send_cmd("killall mccatool")
            self.comm.send_cmd("rm %s" % self.mccapipe)
            self.mccapipe = None
