import wtf.node.mesh
import wtf.node.sniffer
import wtf.comm
import wtf

zotacs=[]

# pre-configured zotac nodes
for n in range(8,12):
    z_ssh = wtf.comm.SSH(ipaddr="10.10.10." + str(n))
    z_ssh.name = "zotac-" + str(n)
    z_ssh.verbosity = 2
# XXX: giving a MAC is robust
    z = wtf.node.mesh.MeshSTA(z_ssh, iface="wlan0", driver="ath9k")
    z.config = wtf.node.mesh.MeshConf(ssid="meshpoo", channel=108, htmode="")
    z.ip = "192.168.34." + str(10 + n)
    zotacs.append(z)

# configure your sniffer node here
ssh = wtf.comm.SSH(ipaddr="10.10.10." + str(6))
ssh.name = "sniffer"
ssh.verbosity = 2
sniffer = wtf.node.sniffer.SnifferSTA(ssh, iface="wlan0", driver="ath9k")
sniffer.config = wtf.node.sniffer.SnifferConf(channel=108, htmode="HT20")
zotacs.append(sniffer)

# XXX: decouple testbed description from the specific test suite
wtf.conf = wtf.config("mcca", nodes=zotacs, name="zotac mesh")
