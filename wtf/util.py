import sys
import commands
import os

CAP_FILE="/tmp/out.cap"

def reconf_stas(stas):
    for sta in stas:
        sta.reconf()

def tu_to_s(tu):
    return tu * 1024 / 1000 / float(1000)

def tu_to_us(tu):
    return tu * 32 * 32

def start_captures(stas):
    for sta in stas:
        for iface in sta.iface:
            sta.start_capture(iface)

def stop_captures(stas, cap_file=CAP_FILE):
    i = 0
    for sta in stas:
        if cap_file == CAP_FILE:
            cap_file += str(i)
        for iface in sta.iface:
            sta.stop_capture(iface, cap_file)
        i += 1

def killperfs(stas):
    for sta in stas:
        for iface in sta.iface:
            iface.killperf()

# collection of different link metric results
class LinkReport():
    def __init__(self, perf_report=None, vqm_report=None):
        self.perf = perf_report
        self.vqm = vqm_report

class VQMReport():
    def __init__(self, ref_clip="", out_clip="", ssim=0, psnr=0, dcm=0):
        self.ref_clip = ref_clip
        self.out_clip = out_clip
        self.ssim = ssim
        self.psnr = psnr
        self.dcm = dcm

def get_vqm_report(ref_clip, out_clip):
    print "getting VQM for " + out_clip

# XXX: the qpsnr metrics are currently more or less bogus since it will blindly
# compare the reference and output clips frame-by-frame, but both clips won't
# start at the *same* frame (due to client-side buffering). Although there is a
# correlation where SSIM closer to 1 means better quality, see DCM for a more
# reliable quality metric.

# comment these out for now since they take a lot of time.
# TODO: follow their stdout
#    o = commands.getoutput("qpsnr -a avg_ssim -s100 -m1000 -o fpa=1000 -r %s %s" % \
#                                    (ref_clip, out_clip))
#    print o
# final result should be on the last line
#    avg_ssim = o.splitlines()[-1].split(",")[1]
#
#    o = commands.getoutput("qpsnr -a avg_psnr -s100 -m1000 -o fpa=1000 -r %s %s" % \
#                                    (ref_clip, out_clip))
#    print o
# final result should be on the last line
#    avg_psnr = o.splitlines()[-1].split(",")[1]
#
# DCM == Dumb Completion Metric :D
    dcm = float(os.path.getsize(out_clip)) / os.path.getsize(ref_clip)
    avg_ssim = 0
    avg_psnr = 0
    return VQMReport(ref_clip, out_clip, avg_ssim, avg_psnr, dcm)

def do_vqm(ifaces, dst, ref_clip):
    # XXX: a bit nasty, test better be 1 frames above us!
    rcv_clip = "/tmp/" + sys._getframe(1).f_code.co_name + ".ts"
    rtp_port = 5004

# destination needs to match client in unicast.
    client = None
    for iface in ifaces:
        if dst == iface.ip:
            client = iface
            continue
        server = iface

# at least make transmitter (sta0) consistent in mcast case.
    if client == None:
        server = ifaces[0]
        client = ifaces[1]

    client.video_client(ip=dst, port=rtp_port)
    server.video_serve(video=ref_clip, ip=dst, port=rtp_port)

    client.get_video(rcv_clip)
    return get_vqm_report(ref_clip, rcv_clip)

class CapData():
    def __init__(self, cap_file=None, monif=None, promisc=False):
# local to the monif
        self.node_cap = cap_file
        self.local_cap = None
        self.monif = monif
        self.promisc = promisc
        self.pid = None

class PerfConf():
    def __init__(self, server=False, dst_ip=None, timeout=5,
                 dual=False, b=10, p=7777, L=6666, fork=False,
                 tcp=False):
        self.server = server
        self.dst_ip = dst_ip
        self.timeout = timeout
        self.dual = dual
        self.bw = b
        self.tcp = tcp
        self.listen_port = p
        self.dual_port = L
        self.fork = fork
        self.report = None
        self.pid = None

class IperfReport():
    def __init__(self, throughput=0.0, loss=0.0):
        self.tput = throughput
        self.loss = loss

# CSV iperf report as @r
def parse_perf_report(conf, r):
    if len(r) == 0:
        tput = 0
        loss = 0
    elif conf.tcp == True:
        tput = float(r[0].split(',')[-1]) / (1024 * 1024) # bits -> mbits
        loss = 0.0  # no loss stats with TCP...
    else:
# output comes as list of strings, hence r[0]...
        tput = float(r[0].split(',')[-6]) / (1024 * 1024) # bits -> mbits
        loss = float(r[0].split(',')[-2])
    return IperfReport(tput, loss)

# perform performance report between interfaces listed in ifaces[] and return
# report as an IperfReport
def do_perf(ifaces, dst, tcp=False):

# destination needs to match server in unicast.
    server  = None
    for iface in ifaces:
        if dst == iface.ip:
            server = iface
            continue
        client = iface

# at least make transmitter consistent in mcast case.
    if server == None:
        server = ifaces[1]
        client = ifaces[0]

    server.perf_serve(dst_ip=dst, tcp=tcp)
    client.perf_client(dst_ip=dst, timeout=10, b=100, tcp=tcp)
    server.killperf()
    return  server.get_perf_report()

# return packets found in tshark_filter
def do_tshark(cap_file, tshark_filter, extra=""):
    r, o = commands.getstatusoutput("tshark -r" + cap_file + " -R'" + tshark_filter +
                                    "' " + extra + " 2> /dev/null")
    if r != 0 and r != 256:
        raise Exception("tshark error %d! Is tshark installed and %s exists? Please verify filter %s" % (r, cap_file, tshark_filter))
    return o

def print_linkreports(results):
    header="TEST             "

# assuming we have same stats for all the tests...
    if results.values()[0].perf != None:
        header += "THROUGHPUT(Mb/s)        LOSS(%)       "
    if results.values()[0].vqm != None:
        header += "SSIM        PSNR      DCM     FILE           "

    print header
    for test in sorted(results):
        result = results[test]
        line = "%s      " % (test,)

        if result.perf != None:
            perf = result.perf
            line += "%f         %f      " % (perf.tput, perf.loss)
        if result.vqm != None:
            vqm = result.vqm
            line += "%s     %s  %s  %s      " % (vqm.ssim, vqm.psnr, vqm.dcm, vqm.out_clip)

        print line
