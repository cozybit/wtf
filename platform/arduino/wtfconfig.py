import wtf
import wtf.node.ap
import wtf.comm
import wtf.node.sta

# path to arduino directory... must be changed
IDE = "/home/jacob/dev/arduino_project/MeshableMCU/arduino-1.5.6-r2"

arduino_comm = wtf.comm.Serial(port="/dev/ttyUSB2", prompt="")
arduino_comm.name = "arduino"
arduino_comm.verbosity = 2

wtf.conf = wtf.config("arduino", comm=arduino_comm,
                      name="arduino mc200 tests", data={'IDE': IDE})
