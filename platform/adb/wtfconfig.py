import wtf
import wtf.node.mesh
import wtf.comm

subnet="192.168.4"
meshid="meshmesh"
channel=1
htmode="HT20"
phones=[]
n=0
devices=["GT9", "GT10"]

for dev in devices:
    n += 1
    android_adb = wtf.comm.ADB(dev)
    android_adb.name = dev
    android_adb.verbosity = 2

    ifaces=[]
    configs=[]
    ifaces.append(wtf.node.Iface(name="wlan0", driver="mwl8787_sdio", ip="%s.%d" % (subnet, 10 + n)))
    configs.append(wtf.node.mesh.MeshConf(ssid=meshid, channel=channel, htmode=htmode, iface=ifaces[0]))
    ifaces[-1].conf=configs[-1]

    adb = wtf.node.mesh.MeshSTA(android_adb, ifaces=ifaces)
    adb.configs = configs

    phones.append(adb)


wtf.conf = wtf.config("adb", nodes=phones, name="mesh tests over android's adb")
