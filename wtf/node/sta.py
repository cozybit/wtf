import wtf.node as node

class STABase(node.NodeBase):
    """
    client STA

    This represents the platform-independent client STA that should be used by tests.

    Real STAs should extend this class and implement the actual STA functions.
    """

    def __init__(self, comm):
        """
        Create an STA with the supplied comm channel.
        """
        node.NodeBase.__init__(self, comm=comm)

class LinuxSTA(STABase):
    """
    Represent a typical linux STA with iwconfig, ifconfig, etc.  It should have
    wireless hardware controlled by the specified driver.
    """

    def __init__(self, comm, driver):
        self.driver = driver
        STABase.__init__(self, comm)

    def init(self):
        r = self.comm.send_cmd("modprobe " + self.driver)
        if r == 0:
            self.initialized = True
        else:
            raise node.ActionFailureError("Failed to modprobe " + self.driver)

    def shutdown(self):
        r = self.comm.send_cmd("modprobe -r " + self.driver)
        if r == 0:
            self.initialized = False
        else:
            raise node.ActionFailureError("Failed to remove " + self.driver)

    def start(self):
        if self.initialized != True:
            raise UninitializedError()
        raise node.InsufficientConfigurationError()

    def stop(self):
        pass
