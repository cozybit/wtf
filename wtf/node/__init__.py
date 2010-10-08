class UninitializedError(Exception):
    """
    Exception raised when routines are called prior to initialization.
    """
    pass

class InsufficientConfigurationError(Exception):
    """
    Exception raised when sufficient configuration information is not available.
    """
    pass

class UnsupportedConfigurationError(Exception):
    """
    Exception raised when an unsupported configuration has been attempted.
    """
    pass

class ActionFailureError(Exception):
    """
    Exception raised when an action on a node fails.
    """
    pass

class UnimplementedError(Exception):
    """
    A method should have been implemented by a subclass but is not.
    """
    pass

class NodeBase():
    """
    A network node that will participate in tests

    A network node could be an AP, a mesh node, a client STA, or some new thing
    that you are inventing.  Minimally, it can be initialized and shutdown
    repeatedly.  So init and shutdown are really not the same thing as __init__
    and __del__.  Once a node has been successfully initialized, it can be
    started and stopped, repeatedly.
    """

    def __init__(self, comm):
        self.initialized = False
        self.comm = comm

    def init(self):
        """
        initialize the node

        override this method to customize how your node is initialized.  For
        some nodes, perhaps nothing is needed.  Others may have to be powered
        on and configured.
        """
        self.initialized = True

    def shutdown(self):
        """
        shutdown the node

        override this method to customize how your node shuts down.
        """
        self.initialized = False

    def start(self):
        """
        start the node in its default configuration

        raises an UninitializedError if init was not called.

        raises an InsufficientConfigurationError exception if sufficient
        default values are not available.
        """
        if self.initialized != True:
            raise UninitializedError()
        raise InsufficientConfigurationError()

    def stop(self):
        """
        stop the node
        """
        pass

    def _cmd_or_die(self, cmd):
        (r, o) = self.comm.send_cmd(cmd)
        if r != 0:
            raise ActionFailureError("Failed to \"" + cmd + "\"")
        return o
