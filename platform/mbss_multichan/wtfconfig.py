import wtf.node.mesh
import wtf.node.sniffer
import wtf.comm
import wtf

subnet="192.168.34"
meshid="meshmesh"
channel=1
htmode="HT20"
zotacs=[]

# pre-configured zotac nodes
for n in range(10,13):
#comms
    z_ssh = wtf.comm.SSH(ipaddr="10.10.10." + str(n))
    z_ssh.name = "zotac-" + str(n)
    z_ssh.verbosity = 2

    if n == 12 or n == 11:
        channel=149

    ifaces=[]

# iface + ip
    ifaces.append(wtf.node.Iface(name="wlan0", driver="ath9k", ip="%s.%d" % (subnet, 10 + n)))
# BSS
    ifaces[-1].conf = wtf.node.mesh.MeshConf(ssid=meshid, channel=channel, htmode=htmode, iface=ifaces[-1])

# "middle" node
    if n == 11:
        ifaces.append(wtf.node.Iface(name="wlan1", driver="ath9k", ip="%s.%d" % (subnet, 40 + n)))
        ifaces[-1].conf = wtf.node.mesh.MeshConf(ssid=meshid, channel=1, htmode=htmode, iface=ifaces[-1])

    z = wtf.node.mesh.MeshSTA(z_ssh, ifaces=ifaces)

    zotacs.append(z)

# XXX: decouple testbed description from the specific test suite
wtf.conf = wtf.config("mmultichan", nodes=zotacs, name="mesh multichan")
