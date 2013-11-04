import wtf.node.mesh
import wtf.comm
from wtf.util import gen_mesh_id, is_dev_connected

subnet = "192.168.4"

meshid = gen_mesh_id()

channel = 1
htmode = "HT20"
phones = []
n = 0

# add your driver here
MARVEL_DRIVER = "mwl8787_sdio"
QCA_DRIVER = "wcn36xx_msm"

potential_devices = ["GT9", "GT10", "GT11", "SXZ1", "SXZ2", "SXZ3"]
devices = []
exp_results = {"test1": 30.0, "test2": 15.0}

#add as DUT's connecte devices only
for device in potential_devices:
    if is_dev_connected(device):
        devices.append(device)

for dev in devices:
    n += 1
    android_adb = wtf.comm.ADB(dev)
    android_adb.name = dev
    android_adb.verbosity = 2

    ifaces = []
    configs = []

    driver = MARVEL_DRIVER
    if dev.startswith("XZ") or dev.startswith("SXZ"):
        driver = QCA_DRIVER

    ifaces.append(wtf.node.Iface(name="wlan0", driver=driver,
                                 ip="%s.%d" % (subnet, 10 + n)))
    configs.append(wtf.node.mesh.MeshConf(ssid=meshid, channel=channel,
                                          htmode=htmode, iface=ifaces[0]))
    ifaces[-1].conf = configs[-1]

    adb = wtf.node.mesh.MeshSTA(android_adb, ifaces=ifaces)
    adb.configs = configs

    phones.append(adb)

if len(devices) > 2:
    wtf.conf = wtf.config("simplemesh", nodes=phones,
                          name="mesh tests over adb",
                          exp_results=exp_results)
else:
    raise ValueError("Number of devices connected was too small!")
