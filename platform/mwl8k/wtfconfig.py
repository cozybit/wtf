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

mwl8k_as_ap = wtf.config(["ap_sta"], aps=[mwl8k_ap], stas=[sta],
                       name="mwl8k as AP")

# now make a configuration for the STA case.
mwl8k_sta = wtf.node.sta.LinuxSTA(mwl8k_serial, "wlan0")

ap_ssh = wtf.comm.SSH(ipaddr="192.168.1.80")
ap_ssh.name = "AP"
ap_ssh.verbosity = 2
ap = wtf.node.ap.Hostapd(ap_ssh, "wlan0")

mwl8k_as_sta = wtf.config(["ap_sta"], aps=[ap], stas=[mwl8k_sta],
                         name="mwl8k as STA")

# tell wtf about our configs
configs = [mwl8k_as_ap, mwl8k_as_sta]  # also reboots mwl8k..
#configs = [mwl8k_as_sta, mwl8k_as_ap] # reboots mwl8k once hostapd closes
