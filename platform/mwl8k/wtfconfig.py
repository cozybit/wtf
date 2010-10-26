import wtf.node.ap
import wtf.node.sta
import wtf.comm
import wtf

# The mwl8k can be either an STA or an AP.  Start by making a test
# configuration for the AP case.
mwl8k_serial = wtf.comm.Serial(port="/dev/ttyUSB0", prompt="[root@fedora-arm /]# ")
mwl8k_serial.name = "mwl8k"
mwl8k_serial.verbosity = 2
mwl8k_ap = wtf.node.ap.Hostapd(mwl8k_serial, "wlan1")

# create a configuration for a nearby STA
sta_ssh = wtf.comm.SSH(ipaddr="192.168.1.60")
sta_ssh.name = "STA"
sta_ssh.verbosity = 2
sta = wtf.node.sta.LinuxSTA(sta_ssh, "wlan0", driver="libertas_tf_sdio")

# Override the setup method to change the name of the node.  Also, mwl8k cannot
# have both ap and sta interfaces up at the same time.  So make sure they are
# both down before starting the tests.
class apConfig(wtf.config):
    def setUp(self):
        self.aps[0].comm.send_cmd("killall hostapd; killall wpa_supplicant",
                                  verbosity=2)
        self.aps[0].comm.send_cmd("ifconfig wlan0 down; ifconfig wlan1 down",
                                  verbosity=2)
        self.aps[0].comm.name = "mwl8k-AP"

mwl8k_as_ap = apConfig(["ap_sta"], aps=[mwl8k_ap], stas=[sta],
                       name="mwl8k as AP")

# now make a configuration for the STA case.
mwl8k_sta = wtf.node.sta.LinuxSTA(mwl8k_serial, "wlan0")

ap_serial = wtf.comm.Serial(port="/dev/ttyUSB1", prompt="[root@localhost dev]# ")
ap_serial.name = "mwl8k-AP"
ap_serial.verbosity = 2
ap = wtf.node.ap.Hostapd(ap_serial, "wlan1")

class staConfig(wtf.config):
    def setUp(self):
        self.stas[0].comm.send_cmd("killall hostapd; killall wpa_supplicant",
                                   verbosity=2)
        self.stas[0].comm.send_cmd("ifconfig wlan0 down; ifconfig wlan1 down",
                                   verbosity=2)
        self.stas[0].comm.name = "mwl8k-STA"

mwl8k_as_sta = staConfig(["ap_sta"], aps=[ap], stas=[mwl8k_sta],
                         name="mwl8k as STA")

# tell wtf about our configs
configs = [mwl8k_as_sta]
