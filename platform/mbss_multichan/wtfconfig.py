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

    if n == 12:
        channel=11

    ifaces=[]
    configs=[]

# iface + ip
    ifaces.append(wtf.node.Iface(name="wlan0", driver="ath9k", ip="%s.%d" % (subnet, 10 + n)))
# BSS
    configs.append(wtf.node.mesh.MeshConf(ssid=meshid, channel=channel, htmode=htmode, iface=ifaces[0]))

# "middle" node
    if n == 11:
        ifaces.append(wtf.node.Iface(name="wlan1", driver="ath9k", ip="%s.%d" % (subnet, 40 + n)))
        configs.append(wtf.node.mesh.MeshConf(ssid=meshid, channel=11, htmode=htmode, iface=ifaces[1]))

    z = wtf.node.mesh.MeshSTA(z_ssh, ifaces=ifaces)
    z.configs = configs

    zotacs.append(z)

# XXX: decouple testbed description from the specific test suite
wtf.conf = wtf.config("mmultichan", nodes=zotacs, name="mesh multichan")
