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
        node.NodeBase.__init__(self, comm=comm)

# Security options
SECURITY_WEP = 1
SECURITY_WPA = 2
SECURITY_WPA2 = 3

# Client authentication schemes.  None is used to represent open.
AUTH_PSK = 1
AUTH_EAP = 2

# Encryption ciphers
ENCRYPT_TKIP = 1
ENCRYPT_CCMP = 2

class APConfig():
    """
    Access Point configuration object

    Access Points have all sorts of configuration variables.  Perhaps the most
    familiar ones are the SSID and the channel.
    """

    def __init__(self, ssid, channel=6, security=None, auth=None,
                 password=None, encrypt=None):
        self.ssid = ssid
        self.channel = channel
        self.security = security
        self.auth = auth
        self.password = password
        self.encrypt = encrypt
        if security == SECURITY_WEP and not password:
            raise InsufficientConfigurationError("WEP requires a password")
        if (security == SECURITY_WPA or security == SECURITY_WPA2) and \
               (not password or not auth):
            raise InsufficientConfigurationError("WPA(2) requires a password and auth scheme")

class Hostapd(node.LinuxNode, APBase):
    """
    Hostapd-based AP
    """
    def __init__(self, comm, iface, driver=None):
        node.LinuxNode.__init__(self, comm, iface, driver)
        self.config = None

    def start(self):
        # iface must be down before we can set type
        node.LinuxNode.stop(self)
        self._cmd_or_die("iw " + self.iface + " set type __ap")
        node.LinuxNode.start(self)
        if not self.config:
            raise node.InsufficientConfigurationError()
        self._configure()
        self._cmd_or_die("hostapd -B /tmp/hostapd.conf")

    def stop(self):
        node.LinuxNode.stop(self)
        self.comm.send_cmd("killall hostapd")
        self.comm.send_cmd("iw dev mon." + self.iface + " del")
        self.comm.send_cmd("rm -f /var/run/hostapd/" + self.iface)

    def perf(self):
        (r, o) = self.comm.send_cmd("iperf -s &", verbosity=2)
        return o

    def killperf(self):
        (r, o) = self.comm.send_cmd("killall iperf", verbosity=2)

    base_config = """
driver=nl80211
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-1
logger_stdout_level=0
dump_file=/tmp/hostapd.dump
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
hw_mode=g
beacon_int=100
dtim_period=2
max_num_sta=255
rts_threshold=2347
fragm_threshold=2346
macaddr_acl=0
auth_algs=3
ignore_broadcast_ssid=0
eapol_key_index_workaround=0
eap_server=0
own_ip_addr=127.0.0.1
"""
    def _configure(self):
        config = self.base_config
        config += "ssid=" + self.config.ssid + "\n"
        config += "channel=%d\n" % self.config.channel
        config += "interface=" + self.iface + "\n"
        if self.config.security != None:
            if self.config.security == SECURITY_WPA: 
                config += "wpa=1\n"
            elif self.config.security == SECURITY_WPA2:
                config += "wpa=2\n"
        if self.config.auth != None:
            if self.config.auth == AUTH_PSK:
                config += "wpa_key_mgmt=WPA-PSK\n"
                config += 'wpa_passphrase="' + self.config.password + '"\n'
        if self.config.encrypt != None:
            if self.config.encrypt == ENCRYPT_TKIP:
                config += "wpa_pairwise=TKIP\n"
            elif self.config.encrypt == ENCRYPT_CCMP:
                config += "wpa_pairwise=CCMP\n"

        self._cmd_or_die("echo -e \"" + config + "\"> /tmp/hostapd.conf",
                         verbosity=0)
