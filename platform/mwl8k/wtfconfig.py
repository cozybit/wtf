import wtf.node.ap

# create AP configurations that match the APs in your vicinity
ap_config_1 = wtf.node.ap.APConfig(ssid="cozyguest", channel=11)
ap = wtf.node.ap.APSet([ap_config_1])

# tell wtf about all of your nodes
nodes = [ ap ]
