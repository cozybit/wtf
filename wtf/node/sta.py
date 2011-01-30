import wtf.node as node
import re, sys, time

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

    def stop(self):
        node.LinuxNode.stop(self)
        self.comm.send_cmd("killall wpa_supplicant")

    def start(self):
        node.LinuxNode.stop(self)
        self._cmd_or_die("iw " + self.iface + " set type station")
        node.LinuxNode.start(self)

    def perf(self, host):
        # start throughput test client, in this case iperf, just dump output for now
        (r, o) = self.comm.send_cmd("iperf -c " + host + " -i 1 -u -b 200M -t 5", verbosity=2)
        return o

    def stress(self, host):
        # do our worst
        (r, o) = self.comm.send_cmd("iperf -c " + host + " -d -P 10", verbosity=2)
        return o

    def scan(self):
        # first perform the scan.  Try a few times because the device still may
        # be coming up.
        (r, o) = self.comm.send_cmd("iwlist " + self.iface + " scan", verbosity=2)
        count = 10
        while count != 0 and \
                  o[0].endswith("Interface doesn't support scanning : Device or resource busy"):
            (r, o) = self.comm.send_cmd("iwlist " + self.iface + " scan")
            count = count - 1
        if count == 0:
            return []

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
            ret.append(node.ap.APConfig(ssid=ssid, channel=channel))
        return ret

    def _open_assoc(self, ssid):
        (r, o) = self.comm.send_cmd("iw " + self.iface + " connect " + ssid)
        if r == 142:    # error code -114
            # operation already in progress, means we're already connected
            # or not ready, try again
            time.sleep(0.5)
            self._cmd_or_die("iw " + self.iface + " connect " + ssid)
        elif r !=0:
            # something else went wrong
            raise wtf.node.ActionFailureError("iw failed with code %d" % r)
        for i in range(1, 30):
            time.sleep(0.5)
            (r, o) = self.comm.send_cmd("iw " + self.iface + " link", verbosity=2)
            if r != 0:
                raise wtf.node.ActionFailureError("iw failed with code %d" % r)

            if o[0] == "Not connected.":
                pass
            elif o[0].split()[0] == "Connected" and \
                 o[1].split()[1] == ssid:
                     return 0

        return -1

    base_config = """
ctrl_interface=/var/run/wpa_supplicant
ctrl_interface_group=root
"""

    def _configure_supplicant(self, apconfig):
        config = self.base_config
        if apconfig.security != None:
            config += "network={\n"
            config += '    ssid="' + apconfig.ssid + '"\n'
            if apconfig.auth == node.ap.AUTH_PSK:
                config += "    key_mgmt=WPA-PSK\n"
                config += '    psk="' + apconfig.password + '"\n'
            config += "}\n"

        self._cmd_or_die("echo -e '" + config + "'> /tmp/sup.conf",
                         verbosity=0)

    def _secure_assoc(self):
        cmd = "wpa_supplicant -B -Dwext -i" + self.iface + " -c/tmp/sup.conf"
        self._cmd_or_die(cmd)
        for i in range(1, 50):
            (r, o) = self.comm.send_cmd("wpa_cli status", verbosity=0)
            if r != 0:
                raise node.ActionFailureError("wpa_cli failed (err=%d)" % r)

            state = [re.match(r'wpa_state=.*', i) for i in o]
            state = [f for f in state if f != None]
            if state[0].group(0) == "wpa_state=COMPLETED":
                return 0
            time.sleep(0.5)
        return -1

    def assoc(self, apconfig):
        if not apconfig.security:
            return self._open_assoc(apconfig.ssid)
        self._configure_supplicant(apconfig)
        return self._secure_assoc()
