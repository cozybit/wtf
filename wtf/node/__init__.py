# Copyright cozybit, Inc 2010-2011
# All rights reserved

from wtf.util import *

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
        self.local_cap = None
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
        self.set_ip(self.ip)
        if self.config.mcast_route:
            self.set_mcast(self.config.mcast_route)

    def stop(self):
        self.comm.send_cmd("ifconfig " + self.iface + " down")

    def set_ip(self, ipaddr):
        self.comm.send_cmd("ifconfig " + self.iface + " " + ipaddr + " up")

    def set_mcast(self, mcast_route):
        self.comm.send_cmd("route add -net %s netmask 255.255.255.255 %s" % (mcast_route,  self.iface))

    def ping(self, host, timeout=2, count=1, verbosity=2):
        return self.comm.send_cmd("ping -c " + str(count) + " -w " +
                                  str(timeout) + " " + host, verbosity=verbosity)[0]

    def start_perf(self, conf):
        self.perf = conf
        self.perf.log = "/tmp/iperf.log"
        if conf.server == True:
            cmd = "iperf -s -u -p" + str(conf.listen_port)
            if conf.dst_ip:
                cmd += " -B" + conf.dst_ip
# -x  [CDMSV]   exclude C(connection) D(data) M(multicast) S(settings) V(server) reports
            cmd += " -y c -x CS | tee " + self.perf.log
            cmd += " &"
        else:
# in o11s the mpath expiration is pretty aggressive (or it hasn't been set up
# yet), so prime it with a ping first. Takes care of initial "losses" as the
# path is refreshed.
            self.ping(conf.dst_ip, verbosity=0, timeout=3)
            cmd = "iperf -c " + conf.dst_ip + \
                  " -i1 -u -b" + str(conf.bw) + "M -t" + str(conf.timeout) + \
                  " -p" + str(conf.listen_port)
            if conf.dual:
                cmd += " -d -L" + str(conf.dual_port)
            if conf.fork:
# -x  [CDMSV]   exclude C(connection) D(data) M(multicast) S(settings) V(server) reports
                cmd += " -y c -x CS | tee " + self.perf.log
                cmd += " &"

        r, o = self.comm.send_cmd(cmd)
        if conf.server != True and conf.fork != True:
# we blocked on completion and report is ready now
            self.perf.report = o[1]

    def perf_serve(self, dst_ip=None, p=7777):
        self.start_perf(PerfConf(server=True, dst_ip=dst_ip, p=p))

    def perf_client(self, dst_ip=None, timeout=5, dual=False, b=10, p=7777, L=6666, fork=False):
        if dst_ip == None:
            raise InsufficientConfigurationError("need dst_ip for perf")
        self.start_perf(PerfConf(dst_ip=dst_ip, timeout=timeout,
                                 dual=dual, b=b, p=p, L=L, fork=fork))

# server @video to @dst_ip using VLC. Blocks until stream completion
    def video_serve(self, video=None, ip=None, port=5004):
        if ip == None or video == None:
            raise InsufficientConfigurationError("need a reference clip and destination ip!")
        print "%s: starting video server" % (self.ip,)
        import os
        self.ref_clip = "/tmp/" + os.path.basename(video)
        self.comm.put_file(video, self.ref_clip)
# prime mpath so we don't lose inital frames in unicast!
        self.ping(ip, verbosity=0)
        self.comm.send_cmd("su nobody -c 'vlc -I dummy %s :sout=\"#rtp{dst=%s,port=%d,mux=ts,ttl=1}\" :sout-all :sout-keep vlc://quit' &> /tmp/video.log" % (self.ref_clip, ip, port))

    def video_client(self, out_file="/tmp/video.ts", ip=None, port=5004):
        print "%s: starting video client" % (self.ip,)
        if ip == None:
            raise InsufficientConfigurationError("need a reference clip and destination ip!")
        self.video_file = out_file
        self.comm.send_cmd("su nobody -c 'vlc -I dummy rtp://%s:%d --sout file/ts:%s' &> /tmp/video.log &" % (ip, port, self.video_file))

    def killvideo(self):
        self.comm.send_cmd("killall -w vlc")
        self.comm.send_cmd("cat /tmp/video.log")

    def get_video(self, path="/tmp/out.ts"):
        if self.video_file == None:
            pass
        self.killvideo()
        self.comm.get_file(self.video_file, path)

    def killperf(self):
        # only need to kill servers or forked clients. This is really to
        # protect against missing report output in o, but that's not obvious :(
        if self.perf.server != True and self.perf.fork != True:
            raise ActionFailureError("don't kill me bro")
        self.comm.send_cmd("killall -w iperf")
        
    def get_perf_report(self):
        r, o = self.comm.send_cmd("cat " + self.perf.log)
        print "parsing perf report"
        return parse_perf_report(o)

    def start_capture(self, cap_file="/tmp/out.cap"):
        self.cap_file = cap_file
        if not self.monif:
            self.monif = self.iface + ".mon"
            self._cmd_or_die("iw " + self.iface + " interface add " + self.monif + " type monitor")
            self._cmd_or_die("ip link set " + self.monif + " up")

        self._cmd_or_die("tcpdump -i " + self.monif + " -ll -xx -p -U -w " + self.cap_file + " &")

# return path to capture file now available on local system
    def get_capture(self, path=None):
        if not path:
            import tempfile
            path = tempfile.mktemp()
        self.comm.get_file(self.cap_file, path)
# save a pointer
        self.local_cap = path
        return path

# stop capture and get a copy for analysis
    def stop_capture(self, path=None):
        if not self.monif:
            pass
        self.comm.send_cmd("killall -9 tcpdump")
        return self.get_capture(path)

