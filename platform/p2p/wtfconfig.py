import wtf.node.p2p
import wtf.comm
import wtf

p1_comm = wtf.comm.SSH(ipaddr="192.168.1.80")
p1_comm.name = "NODE 1"
p1_comm.verbosity = 2
p1 = wtf.node.p2p.Wpap2p(p1_comm, "wlan0", path="/root")

p2_comm = wtf.comm.SSH(ipaddr="192.168.1.90")
p2_comm.name = "NODE 2"
p2_comm.verbosity = 2
p2 = wtf.node.p2p.Wpap2p(p2_comm, "wlan0", path="/root")

# Marvell's mvdroid p2p node, which uses wfdd, wfd_cli, and wpa_supplicant is
# also supported.  Create such a node like this:
#p3_comm = wtf.comm.MvdroidSerial(port="/dev/ttyUSB0")
#p3_comm.name = "mvdroid"
#p3_comm.verbosity = 2
#p3 = wtf.node.p2p.Mvdroid(p3_comm)

wtf.conf = wtf.config("p2p", nodes=[p1, p2], name="wpa supplicant p2p")

