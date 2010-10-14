import wtf.node.ap
import wtf.node.sta
import wtf.comm

# create AP configuration for the mwl8k
ap_serial = wtf.comm.Serial(port="/dev/ttyUSB0", prompt="[root@fedora-arm /]# ")
ap_serial.name = "AP"
ap_serial.verbosity = 2
ap = wtf.node.ap.Hostapd(ap_serial, "wlan0")

# create a configuration for a nearby STA
sta_ssh = wtf.comm.SSH(ipaddr="192.168.1.60")
sta_ssh.name = "STA"
sta_ssh.verbosity = 1
sta = wtf.node.sta.LinuxSTA(sta_ssh, "wlan0", driver="libertas_tf_sdio")

# tell wtf about all of your nodes
nodes = [ ap, sta ]

# tell wtf which test suites you want to run
suites = [ "basic", "ap_sta" ]
