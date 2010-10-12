import wtf.node as node
import re, sys

class STABase(node.NodeBase):
    """
    client STA

    This represents the platform-independent client STA that should be used by
    tests.

    Real STAs might extend this class and implement the actual STA functions.
    """

    def __init__(self, comm):
        """
        Create an STA with the supplied comm channel.
        """
        node.NodeBase.__init__(self, comm=comm)

    def scan(self):
        """
        scan for wireless networks

        Return a list of APConfigs representing the APs in the neighborhood.
        """
        raise node.UnimplementedError("scan not implemented!")

class LinuxSTA(node.LinuxNode, STABase):
    """
    Represent a typical linux STA with iwconfig, ifconfig, etc.  It should have
    wireless hardware controlled by the specified driver.
    """

    def __init__(self, comm, driver, iface):
        self.driver = driver
        self.iface = iface
        STABase.__init__(self, comm)

    def init(self):
        self._cmd_or_die("modprobe " + self.driver)
        self.initialized = True

    def shutdown(self):
        self.stop()
        self._cmd_or_die("modprobe -r " + self.driver)
        self.initialized = False

    def start(self):
        if self.initialized != True:
            raise UninitializedError()
        self._cmd_or_die("ifconfig " + self.iface + " up")

    def stop(self):
        self.comm.send_cmd("ifconfig " + self.iface + " down")

    def scan(self):
        o = self._cmd_or_die("iwlist " + self.iface + " scan")
        # the first line is "<interface>     scan completed".  Skip it.
        results = "".join(o[1:]).split(" "*10 + "Cell ")
        ret = []
        for r in results:
            fields = r.split(" "*20)
            bssid = ""
            channel = None
            ssid = ""
            for f in fields:
                if re.match(".*Address:.*", f):
                    bssid = f.split("Address: ")[1]
                if re.match(".*Channel:.*", f):
                    channel = int(f.split("Channel:")[1])
                if re.match(".*ESSID:.*", f):
                    ssid = f.split("ESSID:")[1].replace('"','')
            ret.append(node.ap.APConfig(ssid, channel))
        return ret

    def assoc(self, ssid):
        self._cmd_or_die("iwconfig " + self.iface + " essid " + ssid)
        for i in range(1, 10):
            (r, o) = self.comm.send_cmd("iwconfig " + self.iface)
            if r != 0:
                raise ActionFailureError("iwconfig failed with code %d" % r)
            if o[0].split("ESSID:")[1].strip() == '"' + ssid + '"':
                return 0
        return -1
