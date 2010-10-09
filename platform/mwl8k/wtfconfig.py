import wtf.node.ap
import wtf.node.sta
import wtf.comm

# create AP configurations that match the APs in your vicinity
ap_serial = wtf.comm.Serial(port="/dev/ttyUSB1",
                            prompt="[root@localhost dev]# ")
ap_serial.name = "AP"
ap_serial.verbosity = 1
ap = wtf.node.ap.Hostapd(ap_serial, "libertas_tf_sdio", "wlan0")

sta_ssh = wtf.comm.SSH(ipaddr="192.168.1.61")
sta_ssh.name = "STA"
sta_ssh.verbosity = 1
sta = wtf.node.sta.LinuxSTA(sta_ssh, "libertas_tf_sdio", "wlan0")

# tell wtf about all of your nodes
nodes = [ ap, sta ]

# tell wtf which test suites you want to run
suites = [ "basic", "ap_sta" ]
