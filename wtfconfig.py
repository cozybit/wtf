import wtf.node.mesh
import wtf.comm
import wtf

subnet="192.168.2"
meshid="meshmesh"
channel=1
htmode="HT20"
androids=[]
n=1


#static tplink ip addresses
ips = { "CB1":"11.47.207.117" , "CB7":"11.201.207.89" }
for device,ip in ips.iteritems():
#comms
    a_ssh = wtf.comm.SSH(ipaddr=ip)
    a_ssh.name = device
    a_ssh.verbosity = 2

    ifaces=[]
    configs=[]

# iface + ip
    ifaces.append(wtf.node.Iface(name="wlan0", driver="android", ip="%s.%d" % (subnet, 10 + n)))
    n+=1
# BSS
    configs.append(wtf.node.mesh.MeshConf(ssid=meshid, channel=channel, htmode=htmode, iface=ifaces[0]))
    ifaces[-1].conf=configs[-1]

    a = wtf.node.mesh.MeshSTA(a_ssh, ifaces=ifaces)
    a.configs = configs

    androids.append(a)

# XXX: decouple testbed description from the specific test suite
wtf.conf = wtf.config("simplemesh", nodes=androids, name="simple two android mesh throughput test")
