import wtf.node.mesh
import wtf.node.sniffer
import wtf.comm
import wtf

subnet="192.168.2"
zotacs=[]

# pre-configured zotac nodes
for n in range(2,4):
#comms
    z_ssh = wtf.comm.SSH(ipaddr="192.168.55." + str(n))
    z_ssh.name = "zotac-" + str(n-2)
    z_ssh.verbosity = 2

    ifaces=[]
    configs=[]

# iface + ip
    ifaces.append(wtf.node.Iface(name="wlan0", driver="ath9k", ip="%s.%d" % (subnet, str(10 + n))))
# BSS
    configs.append(wtf.node.mesh.MeshConf(ssid="simplemesh", channel=channel, htmode="HT40+", iface=ifaces[0]))

    z = wtf.node.mesh.MeshSTA(z_ssh, ifaces=ifaces)
    z.configs = configs

    zotacs.append(z)

# XXX: decouple testbed description from the specific test suite
wtf.conf = wtf.config("simplemesh", nodes=zotacs, name="simple two zotac mesh throughput test")
