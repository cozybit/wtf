import wtf.node as node
import time

WPS_METHOD_PBC = 1
WPS_METHOD_PIN = 2

class P2PBase(node.NodeBase):
    """
    Peer-to-Peer node (i.e., wifi direct)

    This represents the platform-independent P2P node that should be used by
    tests.  If the GO intent is not specified, the default value of 6 is used.
    If a test wishes to change this value, it must do so before invoking start.
    """

    def __init__(self, comm, intent=6):
        """
        Create a P2P node with the supplied default comm channel.
        """
        node.NodeBase.__init__(self, comm=comm)
        self.intent = intent

    def find_start(self):
        pass

    def find_stop(self):
        pass

    def peers(self):
        pass

    def connect_start(self, peer, method=WPS_METHOD_PBC):
        """
        Initiate a connection with the specified peer and method

        return 0 for success and non-zero for failure.  This function should
        not block waiting for the WPS dialog to proceed.  It should return and
        expect a call to connect_finish after the peer's button has been
        pressed or pin entered depending on the method.  That function can
        check the status of the WPS dialog and finalize the connection as
        necessary.
        """
        pass

    def pbc_push(self):
        """
        Push the PBC button.

        return 0 for success and non-zero for failure.  Note that this is most
        sensibly called after somebody else somewhere has called connect_start
        with the pbc method.
        """
        pass

    def connect_finish(self, peer):
        """
        Finish the connection

        return 0 if the WPS dialog terminated successfully and a link is
        available.
        """
        pass

class Peer:
    """
    Peer

    This is the wtf representation of a peer used to communicate detected peers
    between P2P classes and tests.
    """
    def __init__(self, mac, name):
        self.mac = mac
        self.name = name

class Wpap2p(node.LinuxNode, P2PBase, node.sta.LinuxSTA):
    """
    wpa_supplicant-based AP
    """
    def __init__(self, comm, iface, driver=None, path="/root"):
        node.LinuxNode.__init__(self, comm, iface, driver, path)
        P2PBase.__init__(self, comm)
        self.name = comm.name.replace(" ", "-")
        (r, self.mac) = comm.send_cmd("cat /sys/class/net/" + iface + "/address")
        self.mac = self.mac[0]

    base_config = """
ctrl_interface=/var/run/wpa_supplicant
ap_scan=1
device_type=1-0050F204-1
# optional, can be useful for monitoring, forces
# wpa_supplicant to use only channel 1 rather than
# 1, 6 and 11:
#p2p_listen_reg_class=81
#p2p_listen_channel=1
#p2p_oper_reg_class=81
#p2p_oper_channel=1
"""
    def _configure(self):
        config = self.base_config
        config += "device_name=" + self.name + "\n"
        config += "p2p_go_intent=%d\n" % self.intent
        self._cmd_or_die("echo -e \"" + config + "\"> /tmp/p2p.conf",
                         verbosity=0)

    def start(self, auto_go=False, client_only=False):
        node.LinuxNode.start(self)
        self._configure()
        self._cmd_or_die("wpa_supplicant -Dnl80211 -c /tmp/p2p.conf -i " +
                         self.iface + " -dd > /tmp/p2p.log  2>&1 &")
        time.sleep(1)
        if auto_go and client_only:
            raise UnsupportedConfigurationError("Can't be an auto GO and a client only!")
        if auto_go:
            self._cmd_or_die("wpa_cli p2p_group_add")
        self.auto_go = auto_go
        self.client_only = client_only

    def stop(self):
        node.LinuxNode.stop(self)
        node.LinuxNode.stop(self)
        self.comm.send_cmd("killall wpa_supplicant")
        self.comm.send_cmd("rm -f /var/run/wpa_supplicant/" + self.iface)

    def find_start(self):
        self._cmd_or_die("wpa_cli p2p_find")
        pass

    def find_stop(self):
        self._cmd_or_die("wpa_cli p2p_stop_find")
        pass

    def peers(self):
        # For some reason, the current version of wpa_supplicant returns -1
        # when it finds peers.  Maybe this is a bug?
        [ret, peer_macs] = self.comm.send_cmd("wpa_cli -i " + self.iface + \
                                              " p2p_peers")
        peers = []
        for m in peer_macs:
            [ret, pinfo] = self.comm.send_cmd("wpa_cli -i " + self.iface + \
                                                  " p2p_peer " + m)
            # The first line that is returned is the mac address.  Ignore it.
            pprops = dict(prop.split("=") for prop in pinfo[1:])
            peers.append(Peer(m, pprops['device_name']))
        return peers

    def connect_start(self, peer, method=WPS_METHOD_PBC):
        cmd = "wpa_cli -i " + self.iface + " p2p_connect " + peer.mac
        if method == WPS_METHOD_PBC:
            cmd += " pbc"
        else:
            raise UnimplementedError("Unimplemented WPS method")

        if self.client_only:
            cmd += " join"
        [ret, o] = self.comm.send_cmd(cmd)
        return ret

    def pbc_push(self):
        [ret, o] = self.comm.send_cmd("wpa_cli -i " + self.iface + \
                                      " wps_pbc")
        return ret

    def connect_finish(self, peer):
        self.comm.send_cmd("echo Waiting for WPS to finish. This may take a while.")
        return node.sta.LinuxSTA._check_auth(self)

class Mvdroid(node.LinuxNode, P2PBase, node.sta.LinuxSTA):
    """
    mvdroid p2p node uses wfdd and wfd_cli for p2p negotiation and
    wpa_supplicant to establish a link.
    """

    # This is the hard-coded location where wfdd will write the wpa_supplicant
    # config file after becoming a wfd client.
    wpa_conf="/data/wfd/wpas_wfd.conf"

    def __init__(self, comm, iface="wfd0"):
        P2PBase.__init__(self, comm)
        node.LinuxNode.__init__(self, comm, iface, driver=None)
        self.name = comm.name.replace(" ", "-")

    def init(self):
        self.comm.send_cmd("killall wfdd")

        # Ensure the driver is loaded and the interface is available
        [r, o] = self.comm.send_cmd("lsmod | grep sd8xxx")
        if r != 0:
            self._cmd_or_die("insmod /system/lib/modules/mlan.ko")
            self._cmd_or_die("insmod /system/lib/modules/sd8787.ko")
        self._cmd_or_die("rfkill unblock wifi")
        r = 1
        count = 20
        while r != 0 and count > 0:
            [r, o] = self.comm.send_cmd("ls /sys/class/net/ | grep " + \
                                        self.iface)
            count = count - 1
            time.sleep(0.5)
        if r != 0:
            raise node.ActionFailureError("Interface " + self.iface + \
                                          " never appeared")
        (r, self.mac) = self.comm.send_cmd("cat /sys/class/net/" + self.iface +
                                           "/address")
        self.mac = self.mac[0]
        node.LinuxNode.init(self)

        # Make sure various directories and files exist or are cleaned up as
        # necessary
        self.comm.send_cmd("mkdir -p /data/wfd; mkdir -p /var/run;")
        self.comm.send_cmd("rm -f " + self.wpa_conf)

    def shutdown(self):
        self.comm.send_cmd("killall wpa_supplicant")
        self.comm.send_cmd("rm -f /var/run/wpa_supplicant/" + self.iface)
        node.LinuxNode.stop(self)
        self.comm.send_cmd("rfkill block wifi")
        self.comm.send_cmd("rmmod sd8xxx")
        self.comm.send_cmd("rmmod mlan")
        self.comm.send_cmd("rm -f /tmp/wfd.conf")
        node.LinuxNode.shutdown(self)
