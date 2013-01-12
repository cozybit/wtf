import wtf.node.mesh
import wtf.node.sniffer
import wtf.comm
import wtf

zotacs=[]

# pre-configured zotac nodes
for n in range(10,12):
    z_ssh = wtf.comm.SSH(ipaddr="10.10.10." + str(n))
    z_ssh.name = "zotac-" + str(n)
    z_ssh.verbosity = 2
# XXX: giving a MAC is robust
    z = wtf.node.mesh.MeshSTA(z_ssh, iface="wlan3", driver="ath9k_htc")
# security=1 to turn security on
    z.config = wtf.node.mesh.MeshConf(ssid="meshpoo", channel=6, htmode="HT20")
    z.ip = "192.168.34." + str(10 + n)
    zotacs.append(z)

# XXX: decouple testbed description from the specific test suite
wtf.conf = wtf.config("11aa", nodes=zotacs, name="11aa mesh")
