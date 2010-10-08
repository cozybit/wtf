import wtf.node.ap
import wtf.node.sta
import wtf.comm.serialcomm

# create AP configurations that match the APs in your vicinity
ap_config_1 = wtf.node.ap.APConfig(ssid="cozyguest", channel=11)
ap = wtf.node.ap.APSet(None, [ap_config_1])

sta_serial = wtf.comm.serialcomm.SerialComm(port="/dev/ttyUSB1",
                                            prompt="[root@localhost dev]# ")
sta = wtf.node.sta.LinuxSTA(sta_serial, "libertas_tf_sdio")

# tell wtf about all of your nodes
nodes = [ ap, sta ]

# tell wtf which test suites you want to run
suites = [ "basic" ]
