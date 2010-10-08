import serial
import fdpexpect

class CommandFailureError(Exception):
    """
    Exception raised when a comm fails to send a command.
    """
    pass

class CommBase():
    """
    A command communication channel

    wtf needs a way to pass commands to nodes, retrieve return codes, and
    retrieve output.
    """

    def __init__(self):
        pass

    def send_cmd(self, command):
        """
        Send a command via this comm channel and return the return code

        raise a CommandFailureError if it was not possible to send the command.
        """
        raise CommandFailureError("send_cmd routine unimplemented")

class Serial(CommBase):
    """
    communicate with a node via a serial port

    The console on the other end must at least be able to 'echo $?' so we can
    get the return code.
    """
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200,
                 prompt="[root@localhost]# "):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        self.serial.flushInput()
        self.serial.flushOutput()
        self.ffd = fdpexpect.fdspawn(self.serial.fd)
        self.prompt = prompt
        # assume that because we flushed, we are at a bare prompt
        CommBase.__init__(self)

    def __del__(self):
        self.serial.flushInput()
        self.serial.flushOutput()
        self.serial.close()

    def send_cmd(self, command):
        self.ffd.send("%s\n" % command)
        r = self.ffd.expect_exact([self.prompt, fdpexpect.TIMEOUT])
        for l in self.ffd.before.split("\r\n")[:-1]:
            print l
        if r == 1:
            return -1

        # now grab the return code.
        self.ffd.send("echo $?\n")
        r = self.ffd.expect_exact([self.prompt, fdpexpect.TIMEOUT])
        if r == 1:
            return -1
        return int(self.ffd.before.split("\r\n")[-2])
