import wtf.node.mesh
import wtf.comm
import wtf

zotacs=[]

# pre-configured zotac nodes
for n in range(8,12):
    z_ssh = wtf.comm.SSH(ipaddr="192.168.66." + str(10 + n))
    z_ssh.name = "zotac-" + str(n)
    z_ssh.verbosity = 2
# XXX: giving a MAC is robust
    z = wtf.node.mesh.MeshSTA(z_ssh, "wlan2")
    z.config = wtf.node.mesh.MeshConf(ssid="meshpoo", channel=1)
    z.ip = "192.168.33." + str(10 + n)
    zotacs.append(z)

# XXX: decouple testbed description from the specific test suite
wtf.conf = wtf.config("mcca", nodes=zotacs, name="zotac mesh")
