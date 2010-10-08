import serial
import fdpexpect
import pxssh

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

class SSH(CommBase):
    """
    communicate with a node via ssh

    The console on the other end must at least be able to 'echo $?' so we can
    get the return code.
    """
    def __init__(self, ipaddr, user="root"):
        self.session = pxssh.pxssh()
        self.session.login(ipaddr, user)
        CommBase.__init__(self)

    def send_cmd(self, command):
        # TODO: Okay.  Here's a mystery.  If the command is 69 chars long,
        # pxssh chokes on whatever it sees over ssh and all subsequent tests
        # fail.  Amazing!  If it's longer, or shorter, everything works fine.
        # But the magic number 69 breaks the command flow.  Why?  Could it be
        # that the prompt "[PEXPECT]# " is 11 chars, and 69 + 11 is 80, and
        # there's a line discipline problem somewhere?  If you figure it out
        # you'll be my hero.
        if len(command) == 69:
            command = "  " + command

        self.session.sendline(command)
        self.session.prompt()
        for l in self.session.before.split("\r\n")[:-1]:
            print l
        self.session.sendline("echo $?")
        self.session.prompt()
        return int(self.session.before.split("\n")[-2])
