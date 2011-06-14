import wtf.node.p2p
import wtf.comm
import wtf

p1_comm = wtf.comm.MvdroidSerial(port="/dev/ttyUSB0")
p1_comm.name = "mvdroid-1"
p1_comm.verbosity = 2
p1 = wtf.node.p2p.Mvdroid(p1_comm, force_driver_reload=True)

p2_comm = wtf.comm.MvdroidSerial(port="/dev/ttyUSB1")
p2_comm.name = "mvdroid-2"
p2_comm.verbosity = 2
p2 = wtf.node.p2p.Mvdroid(p2_comm, force_driver_reload=True)

# NOTE: the force_driver_reload option to the Mvdroid constructor forces a full
# reload of the underlying driver at node start/stop time instead of node
# init/shutdown time.  Currently, this option must be set to true to prevent
# the state of one test influencing another test.  Clearly, in a real system
# you would not want to reload the drivers for each wifi-direct use case.  So
# this is a bug in mvdroid.  Once it's fixed, we can stop using
# force_driver_reload=True.

wtf.conf = wtf.config("mvdroid", nodes=[p1, p2], name="mvdroid p2p tests")
