import sys
import commands

CAP_FILE="/tmp/out.cap"

def reconf_stas(stas, conf):
    for sta in stas:
        sta.reconf(conf)

def tu_to_s(tu):
    return tu * 1024 / 1000 / float(1000)

def tu_to_us(tu):
    return tu * 32 * 32

def start_captures(stas):
    for sta in stas:
        sta.start_capture()

def stop_captures(stas, cap_file=CAP_FILE):
    i = 0
    for sta in stas:
        if cap_file == CAP_FILE:
            cap_file += str(i)
        sta.stop_capture(cap_file)
        i += 1

def killperfs(stas):
    for sta in stas:
        sta.killperf()

# collection of different link metric results
class LinkReport():
    def __init__(self, perf_report=None, vqm_report=None):
        self.perf = perf_report
        self.vqm = vqm_report

class VQMReport():
    def __init__(self, ref_clip="", out_clip="", ssim=0, psnr=0):
        self.ref_clip = ref_clip
        self.out_clip = out_clip
        self.ssim = ssim
        self.psnr = psnr

def get_vqm_report(ref_clip, out_clip):
    print "getting VQM for " + out_clip

# TODO: follow their stdout
    o = commands.getoutput("qpsnr -a avg_ssim -s100 -m1000 -o fpa=1000 -r %s %s" % \
                                    (ref_clip, out_clip))
    print o
# final result should be on the last line
    avg_ssim = o.splitlines()[-1].split(",")[1]

    o = commands.getoutput("qpsnr -a avg_psnr -s100 -m1000 -o fpa=1000 -r %s %s" % \
                                    (ref_clip, out_clip))
    print o
# final result should be on the last line
    avg_psnr = o.splitlines()[-1].split(",")[1]
    return VQMReport(ref_clip, out_clip, avg_ssim, avg_psnr)

def do_vqm(sta, dst, ref_clip):
    # XXX: a bit nasty, test better be 1 frames above us!
    rcv_clip = "/tmp/" + sys._getframe(1).f_code.co_name + ".ts"
    rtp_port = 5004

# destination needs to match client in unicast.
    client = None
    for s in sta:
        if dst == s.ip:
            client = s
            continue
        server = s

# at least make transmitter (sta0) consistent in mcast case.
    if client == None:
        server = sta[0]
        client = sta[1]

    client.video_client(ip=dst, port=rtp_port)
    server.video_serve(video=ref_clip, ip=dst, port=rtp_port)

    client.get_video(rcv_clip)
    return get_vqm_report(ref_clip, rcv_clip)

class PerfConf():
    def __init__(self, server=False, dst_ip=None, timeout=5,
                 dual=False, b=10, p=7777, L=6666, fork=False):
        self.server = server
        self.dst_ip = dst_ip
        self.timeout = timeout
        self.dual = dual
        self.bw = b
        self.listen_port = p
        self.dual_port = L
        self.fork = fork
        self.report = None

class IperfReport():
    def __init__(self, throughput=0.0, loss=0.0):
        self.tput = throughput
        self.loss = loss

# CSV iperf report as @r
def parse_perf_report(r):
# output comes as list of strings, hence r[0]...
    tput = float(r[0].split(',')[-6]) / (1024 * 1024) # bits -> mbits
    loss = float(r[0].split(',')[-2])
    return IperfReport(tput, loss)

# TODO: pass a conf parameter
def do_perf(sta, dst):

# destination needs to match server in unicast.
    server  = None
    for s in sta:
        if dst == s.ip:
            server = s
            continue
        client = s

# at least make transmitter consistent in mcast case.
    if server == None:
        server = sta[1]
        client = sta[0]

    server.perf_serve(dst_ip=dst)
    client.perf_client(dst_ip=dst, timeout=10, b=100)
    server.killperf()
    return  server.get_perf_report()

# return packets found in tshark_filter
def do_tshark(cap_file, tshark_filter, extra=""):
    r, o = commands.getstatusoutput("tshark -r" + cap_file + " -R'" + tshark_filter +
                                    "' " + extra + " 2> /dev/null")
    if r != 0 and r != 256:
        raise Exception("tshark error %d! Is tshark installed and %s exists? Please verify filter %s" % (r, cap_file, tshark_filter))
    return o

