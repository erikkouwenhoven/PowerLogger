import logging
import os
import datetime
from openzwave.network import ZWaveNetwork, ZWaveException
from openzwave.option import ZWaveOption
from pydispatch import dispatcher
from Utils.settings import Settings


class NetworkInterface:
    """
    Basislaag die communiceert met de ZWave library en
    - Instantieert het ZWaveNetwork
    - vangt events af en stuurt door
    - roept callback aan bij value update of change
    """
    def __init__(self, value_received_cb):
        """"
        valueReceivedCB(node, value) functie wordt aangeroepen als waarde binnenkomt
        """
        self.value_received_CB = value_received_cb
        self.network = self.init_network()
        if self.network:
            self.connect_dispatcher()
            self.network.start()

    def init_network(self):
        # Define some manager options
        try:
            options = ZWaveOption(Settings().get_device(), config_path=Settings().get_config(), user_path=".", cmd_line="")
            # options.set_log_file(Settings().config["OpenZWaveSettings"]["Logging"]["Filename"])
            options.set_append_log_file(False)
            options.set_console_output(False)
            options.set_save_log_level("Debug")
            options.set_logging(True)
            options.set_save_configuration(True)
            options.lock()
            network = ZWaveNetwork(options, autostart=False)
            return network
        except ZWaveException as err:
            logging.debug(f"ZWaveException: {err}")

    def connect_dispatcher(self):
        dispatcher.connect(self.network_started, ZWaveNetwork.SIGNAL_NETWORK_STARTED)
        dispatcher.connect(self.network_failed, ZWaveNetwork.SIGNAL_NETWORK_FAILED)
        dispatcher.connect(self.network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)
        dispatcher.connect(self.network_awake, ZWaveNetwork.SIGNAL_NETWORK_AWAKED)

    def network_started(self, network):
        logging.info("***** Network has started")

    def network_failed(self, network):
        logging.info("***** Network has failed")

    def network_ready(self, network):
        logging.info("***** Network is ready")

    def network_awake(self, network):
        logging.info("***** Network is awake")
        dispatcher.connect(self.value_update, ZWaveNetwork.SIGNAL_VALUE)
        dispatcher.connect(self.value_changed, ZWaveNetwork.SIGNAL_VALUE_CHANGED)
        dispatcher.connect(self.node_event, ZWaveNetwork.SIGNAL_NODE_EVENT)

    def value_update(self, network, node, value):
        logging.info("Hello from value : {}.".format(value))
        self.show_result(node, value)
        self.value_received_CB(node, value)

    def value_changed(self, network, node, value):
        logging.info("Hello from value CHANGE : {}.".format(value))
        self.show_result(node, value)
        self.value_received_CB(node, value)

    def node_event(self, **kwargs):
        print("Hello from node event : {}.".format( kwargs ))

    def show_result(self, node, value):
        S = f'{datetime.datetime.now()}: {node.node_id} {value.label} ({value.value_id}) {value.data} {value.units}'
        with open('output.txt', 'at') as file:
            file.write(S + '\n')
