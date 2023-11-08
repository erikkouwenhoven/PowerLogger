import logging
from ZWaveSystem.network_interface import NetworkInterface


class ZWaveInterface:

    def __init__(self, postSampleCB=None):
        self.postSampleCB = postSampleCB
        self.network_interface = NetworkInterface(self.value_received_CB)
        self.data = None

    def value_received_CB(self, zWaveNode, zWaveValue):
        logging.info(f'valueReceived callback from network: node={zWaveNode.node_id}, value={zWaveValue.data} ({zWaveValue.label})')
        self.data = zWaveValue.data
        if self.postSampleCB:
            self.postSampleCB()

    def getSample(self):
        return self.data
