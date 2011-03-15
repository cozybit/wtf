import wtf.node as node

class P2PBase(node.NodeBase):
    """
    Peer-to-Peer node (i.e., wifi direct)

    This represents the platform-independent P2P node that should be used by
    tests.
    """

    def __init__(self, comm):
        """
        Create a P2P node with the supplied default comm channel.
        """
        node.NodeBase.__init__(self, comm=comm)

    def find_start(self):
        pass

    def find_stop(self):
        pass

    def peers(self):
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

class Wpap2p(node.LinuxNode, P2PBase):
    """
    wpa_supplicant-based AP
    """
    def __init__(self, comm, iface, driver=None, path="/root"):
        node.LinuxNode.__init__(self, comm, iface, driver, path)
        self.name = comm.name.replace(" ", "-")
        (r, self.mac) = comm.send_cmd("cat /sys/class/net/" + iface + "/address")
        self.mac = self.mac[0]

    base_config = """
ctrl_interface=/var/run/wpa_supplicant
ap_scan=1
device_type=1-0050F204-1
# If you need to modify the group owner intent, 0-15, the higher
# number indicates preference to become the GO
#p2p_go_intent=15
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
        self._cmd_or_die("echo -e \"" + config + "\"> /tmp/p2p.conf",
                         verbosity=0)

    def start(self):
        node.LinuxNode.start(self)
        self._configure()
        self._cmd_or_die("wpa_supplicant -Dnl80211 -c /tmp/p2p.conf -i " +
                         self.iface + " -B")

    def stop(self):
        node.LinuxNode.stop(self)
        node.LinuxNode.stop(self)
        self.comm.send_cmd("killall wpa_supplicant")
        self.comm.send_cmd("rm -f /var/run/wpa_supplicant/" + self.iface)

    def find_start(self):
        self._cmd_or_die("wpa_cli p2p_find")
        pass

    def find_stop(self):
        self._cmd_or_die("wpa_cli p2p_find_stop")
        pass

    def peers(self):
        # For some reason, the current version of wpa_supplicant returns -1
        # when it finds peers.  Maybe this is a bug?
        [ret, peer_macs] = self.comm.send_cmd("wpa_cli -i " + self.iface + \
                                              " p2p_peers")
        peers = []
        for m in peer_macs:
            [ret, pinfo] = self.comm.send_cmd("wpa_cli -i " + self.iface + \
                                                  " p2p_peer " + m,
                                              verbosity=0)
            # The first line that is returned is the mac address.  Ignore it.
            pprops = dict(prop.split("=") for prop in pinfo[1:])
            peers.append(Peer(m, pprops['device_name']))
        return peers
