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

class Hostapd(APBase):
    """
    Hostapd-based AP
    """
    def __init__(self, comm, driver, iface):
        self.driver = driver
        self.iface = iface
        APBase.__init__(self, comm)
        self.config = None

    def init(self):
        r = self._cmd_or_die("modprobe " + self.driver)
        self.initialized = True

    def shutdown(self):
        self.stop()
        self.comm.send_cmd("ifconfig " + self.iface + " down")
        self.comm.send_cmd("modprobe -r " + self.driver)

    def start(self):
        if self.initialized != True:
            raise UninitializedError()
        if not self.config:
            raise node.InsufficientConfigurationError()
        self._configure()
        self._cmd_or_die("hostapd -B /tmp/hostapd.conf")

    def stop(self):
        self.comm.send_cmd("killall hostapd")

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
    def _configure_line(self, line):
        self._cmd_or_die("echo " + line + ">> /tmp/hostapd.conf")

    def _configure(self):
        self._cmd_or_die("rm -f /tmp/hostapd.conf")
        for l in self.base_config.split("\n"):
            self._configure_line(l)
        self._configure_line("ssid=" + self.config.ssid)
        self._configure_line("channel=%d" % self.config.channel)
        self._configure_line("interface=" + self.iface)
