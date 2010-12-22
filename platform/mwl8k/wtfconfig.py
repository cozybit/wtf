import wtf.node.ap
import wtf.node.sta
import wtf.comm
import wtf

# The mwl8k can be either an STA or an AP.  Start by making a test
# configuration for the AP case.
mwl8k_serial = wtf.comm.Serial(port="/dev/ttyUSB2", prompt="[root@fedora-arm /]# ")
mwl8k_serial.name = "mwl8k"
mwl8k_serial.verbosity = 2
mwl8k_ap = wtf.node.ap.Hostapd(mwl8k_serial, "wlan0")

# create a configuration for a nearby STA
sta_ssh = wtf.comm.SSH(ipaddr="192.168.1.80")
sta_ssh.name = "STA"
sta_ssh.verbosity = 2
sta = wtf.node.sta.LinuxSTA(sta_ssh, "wlan0")

# Override the setup method to change the name of the node.  Also, change the
# interface type to be __ap so hostapd will work.
class apConfig(wtf.config):
    def setUp(self):
        self.aps[0].comm.send_cmd("killall hostapd; killall wpa_supplicant",
                                  verbosity=0)
        self.aps[0].comm.send_cmd("ifconfig wlan0 down; iw wlan0 set type __ap",
                                  verbosity=0)
        self.aps[0].comm.name = "mwl8k-AP"

    def tearDown(self):
        # Be sure to tear down the AP in our setup in case somebody wants to
        # run another test
        self.aps[0].comm.send_cmd("killall hostapd", verbosity=0)

mwl8k_as_ap = apConfig(["ap_sta"], aps=[mwl8k_ap], stas=[sta],
                       name="mwl8k as AP")

# now make a configuration for the STA case.
mwl8k_sta = wtf.node.sta.LinuxSTA(mwl8k_serial, "wlan0")

ap_ssh = wtf.comm.SSH(ipaddr="192.168.1.80")
ap_ssh.name = "AP"
ap_ssh.verbosity = 2
ap = wtf.node.ap.Hostapd(ap_ssh, "wlan0")

class staConfig(wtf.config):
    def setUp(self):
        self.stas[0].comm.send_cmd("killall hostapd; killall wpa_supplicant",
                                   verbosity=0)
        self.stas[0].comm.send_cmd("ifconfig wlan0 up; iw wlan0 set type station",
                                   verbosity=0)
        self.stas[0].comm.name = "mwl8k-STA"

    def tearDown(self):
        self.stas[0].comm.send_cmd("killall wpa_supplicant; ifconfig wlan0 down",
                                   verbosity=0)

mwl8k_as_sta = staConfig(["ap_sta"], aps=[ap], stas=[mwl8k_sta],
                         name="mwl8k as STA")

# tell wtf about our configs
#configs = [mwl8k_as_ap, mwl8k_as_sta] # reboots mwl8k!
configs = [mwl8k_as_sta, mwl8k_as_ap]
