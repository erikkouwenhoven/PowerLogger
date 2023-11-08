import os
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
from pydispatch import dispatcher
from Utils.settings import Settings


class NetworkInterface:
    """
    Basislaag die communiceert met de ZWave library en
    - Instantieert het ZWaveNetwork
    - vangt events af en stuurt door
    """
    def __init__(self, valueReceivedCB):
        """"
        valueReceivedCB(node, value) functie wordt aangeroepen als waarde binnenkomt
        """
        self.valueReceivedCB = valueReceivedCB
        self.network = self.initNetwork()
        self.networkStatus = []
        self.connectDispatcher()
        self.network.start()

    def initNetwork(self):
        # Define some manager options
        options = ZWaveOption(Settings().get_device(), config_path=Settings().get_config(), user_path=".", cmd_line="")
        # options.set_log_file(Settings().config["OpenZWaveSettings"]["Logging"]["Filename"])
        options.set_append_log_file(False)
        options.set_console_output(False)
        options.set_save_log_level(log)
        options.set_logging(True)
        options.lock()
# Create a network object
        network = ZWaveNetwork(options, autostart=False)
        return network

    def connectDispatcher(self):
        # We connect to the louie dispatcher
        dispatcher.connect(self.louie_network_started, ZWaveNetwork.SIGNAL_NETWORK_STARTED)
        dispatcher.connect(self.louie_network_failed, ZWaveNetwork.SIGNAL_NETWORK_FAILED)
        dispatcher.connect(self.louie_network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)
        dispatcher.connect(self.louie_network_awake, ZWaveNetwork.SIGNAL_NETWORK_AWAKED)
        dispatcher.connect(self.louie_value_update, ZWaveNetwork.SIGNAL_VALUE)
        dispatcher.connect(self.louie_value_changed, ZWaveNetwork.SIGNAL_VALUE_CHANGED)

    def louie_network_started(self, network):
        print("***** Network has started")
        self.networkStatus.append("Started")

    def louie_network_failed(self, network):
        print("***** Network has failed")
        self.networkStatus.append("Failed")

    def louie_network_ready(self, network):
        print("***** Network is ready")
        self.networkStatus.append("Ready")

    def louie_network_awake(self, network):
        print("***** Network is awake")
        self.networkStatus.append("Awake")

    def louie_value_update(self, network, node, value):
        print("Hello from value : {}.".format(value))

    def louie_value_changed(self, network, node, value):
        print("Hello from value CHANGE : {}.".format(value))
        self.valueReceivedCB(node, value)

    def isNodeCommunicating(self, nodeID):
        if self.network.nodes[nodeID].is_sleeping is False and self.network.nodes[nodeID].is_ready is True:
            return True
        else:
            return False
