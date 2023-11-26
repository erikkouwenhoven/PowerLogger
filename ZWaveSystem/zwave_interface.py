from __future__ import annotations
import logging
from ZWaveSystem.network_interface import NetworkInterface
from ZWaveSystem.data_classes import SampleZWave
from typing import Dict, List, Optional


class ZWaveInterface:

    def __init__(self):
        self.post_sample_CB = None
        self.network_interface = NetworkInterface(self.value_received_CB)
        self.sample: Optional[SampleZWave] = None
        self.subscriptions: Optional[Dict[int, List[int]]] = None  # registered node-valueIDs that are called back

    def register(self, subscriptions: Optional[Dict[int, List[int]]], post_sample_CB=None):
        self.post_sample_CB = post_sample_CB
        self.subscriptions = subscriptions

    def value_received_CB(self, zWaveNode, zWaveValue):
        logging.info(f'valueReceived callback from network: node={zWaveNode.node_id}, parent_id {zWaveValue.parent_id}, value={zWaveValue.data} {zWaveValue.units} ({zWaveValue.label}, {zWaveValue.value_id})')
        self.sample = SampleZWave.from_zwave_data(zWaveNode, zWaveValue)
        if self.post_sample_CB:
            if zWaveNode.node_id in self.subscriptions:
                if zWaveValue.value_id in self.subscriptions[zWaveNode.node_id]:
                    self.post_sample_CB()
                else:
                    logging.debug(f'Niet geregistreerd: value {zWaveValue.value_id} zit niet in {self.subscriptions[zWaveNode.node_id]}')
            else:
                logging.debug(f'Niet geregistreerd: node {zWaveNode.node_id} zit niet in {self.subscriptions}')
        else:
            logging.debug('Geen post_sample_CB')

    def getSample(self) -> SampleZWave:
        return self.sample



