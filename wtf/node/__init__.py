# Copyright cozybit, Inc 2010-2011
# All rights reserved

class UninitializedError(Exception):
    """
    Exception raised when routines are called prior to initialization.
    """
    pass

class InsufficientConfigurationError(Exception):
    """
    Exception raised when sufficient configuration information is not available.
    """
    pass

class UnsupportedConfigurationError(Exception):
    """
    Exception raised when an unsupported configuration has been attempted.
    """
    pass

class ActionFailureError(Exception):
    """
    Exception raised when an action on a node fails.
    """
    pass

class UnimplementedError(Exception):
    """
    A method should have been implemented by a subclass but is not.
    """
    pass

class NodeBase():
    """
    A network node that will participate in tests

    A network node could be an AP, a mesh node, a client STA, or some new thing
    that you are inventing.  Minimally, it can be initialized and shutdown
    repeatedly.  So init and shutdown are really not the same thing as __init__
    and __del__.  Once a node has been successfully initialized, it can be
    started and stopped, repeatedly.
    """

    def __init__(self, comm):
        self.initialized = False
        self.comm = comm

    def init(self):
        """
        initialize the node

        override this method to customize how your node is initialized.  For
        some nodes, perhaps nothing is needed.  Others may have to be powered
        on and configured.
        """
        self.initialized = True

    def shutdown(self):
        """
        shutdown the node

        override this method to customize how your node shuts down.
        """
        self.initialized = False

    def start(self):
        """
        start the node in its default configuration

        raises an UninitializedError if init was not called.

        raises an InsufficientConfigurationError exception if sufficient
        default values are not available.
        """
        if self.initialized != True:
            raise UninitializedError()
        raise InsufficientConfigurationError()

    def stop(self):
        """
        stop the node
        """
        pass

    def set_ip(self, ipaddr):
        """
        set the ip address of a node
        """
        raise UnimplementedError("set_ip is not implemented for this node")

    def ping(self, host, timeout=2, count=1):
        """
        ping a remote host from this node

        timeout: seconds to wait before quitting

        count: number of ping requests to send

        return 0 on success, anything else on failure
        """
        raise UnimplementedError("ping is not implemented for this node")

    def _cmd_or_die(self, cmd, verbosity=None):
        (r, o) = self.comm.send_cmd(cmd, verbosity)
        if r != 0:
            raise ActionFailureError("Failed to \"" + cmd + "\"")
        return o

class LinuxNode(NodeBase):
    """
    A linux network node

    Expects: iw, mac80211 debugfs
    """
    def __init__(self, comm, iface, driver=None, path=None):
        self.driver = driver
        self.iface = iface
        self.monif = None
        NodeBase.__init__(self, comm)
        if path != None:
            self.comm.send_cmd("export PATH=" + path + ":$PATH:", verbosity=0)

        # who knows what was running on this machine before.  Be sure to kill
        # anything that might get in our way.
        self.comm.send_cmd("killall hostapd; killall wpa_supplicant",
                           verbosity=0)

    def init(self):
        if self.driver:
            self._cmd_or_die("modprobe " + self.driver)
            # give ifaces time to come up
            import time
            time.sleep(1)
        # TODO: check for error and throw something!
        r, self.phy = self.comm.send_cmd("echo `find /sys/kernel/debug/ieee80211 -name netdev:" + self.iface + " | cut -d/ -f6`", verbosity=0)
        r, self.mac = self.comm.send_cmd("echo `ip link show " + self.iface + " | awk '/ether/ {print $2}'`", verbosity=0)

        # XXX: Python people help!!
        self.phy = self.phy[0]
        self.mac = self.mac[0]

        self.initialized = True

    def shutdown(self):
        self.stop()
        self.comm.send_cmd("ifconfig " + self.iface + " down")
        if self.driver:
            self.comm.send_cmd("modprobe -r " + self.driver)
        self.initialized = False

    def start(self):
        if self.initialized != True:
            raise UninitializedError()
        self._cmd_or_die("ifconfig " + self.iface + " up")

    def stop(self):
        self.comm.send_cmd("ifconfig " + self.iface + " down")

    def set_ip(self, ipaddr):
        self.comm.send_cmd("ifconfig " + self.iface + " " + ipaddr + " up")

    def ping(self, host, timeout=2, count=1):
        return self.comm.send_cmd("ping -c " + str(count) + " -w " +
                                  str(timeout) + " " + host)[0]

    def perf(self, client=None, timeout=5):
        if client == None:
            # we're the server
            self._cmd_or_die("iperf -s -u -D > /dev/null")
        else:
            self.comm.send_cmd("iperf -c " + client + " -i 1 -u -b 200M -t " + str(timeout), verbosity=2)

    def killperf(self):
        self.comm.send_cmd("killall -9 iperf")

    def start_capture(self, cap_file="/tmp/out.cap"):
        self.cap_file = cap_file
        if not self.monif:
            self.monif = self.iface + ".mon"
            self._cmd_or_die("iw " + self.iface + " interface add " + self.monif + " type monitor")
            self._cmd_or_die("ip link set " + self.monif + " up")

        self._cmd_or_die("tcpdump -i " + self.monif + " -ll -xx -p -U -w " + self.cap_file + " &")

    def stop_capture(self):
        if not self.monif:
            pass
        self.comm.send_cmd("killall tcpdump")
