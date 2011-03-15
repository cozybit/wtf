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

wtf.conf = wtf.config("p2p", nodes=[p1, p2], name="wpa supplicant p2p")

