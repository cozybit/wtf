import wtf.node.ap
import wtf.node.sta
import wtf.comm
import wtf

arduino_comm = wtf.comm.Serial(
    port="/dev/ttyUSB2", prompt="")
arduino_comm.name = "arduino"
arduino_comm.verbosity = 2

wtf.conf = wtf.config("arduino", comm=arduino_comm, name="arduino as AP")
