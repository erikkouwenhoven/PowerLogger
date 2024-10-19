from typing import Dict, List, Union
import logging
from ZWaveSystem.network_interface import NetworkInterface
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue


class ZWaveInterface:

    def __init__(self, post_sample_cb: callable((ZWaveNode, ZWaveValue))):
        self.post_sample_CB = post_sample_cb
        self.network_interface = NetworkInterface(self._value_received_cb)  # als je dit een lokale var. leidt dit tot access violation
        self.subscriptions: Union[Dict[int, List[str]], None] = None  # registered node-valueIDs that are called back

    def register(self, subscriptions: Union[Dict[int, List[str]], None]):
        self.subscriptions = subscriptions

    def _value_received_cb(self, z_wave_node: ZWaveNode, z_wave_value: ZWaveValue):
        logging.info(f'valueReceived callback from network: node={z_wave_node.node_id}, '
                     f'parent_id {z_wave_value.parent_id}, value={z_wave_value.data} {z_wave_value.units} '
                     f'({z_wave_value.label}, {z_wave_value.value_id})')
        if self.post_sample_CB:
            if z_wave_node.node_id in self.subscriptions:
                if z_wave_value.label in self.subscriptions[z_wave_node.node_id]:
                    self.post_sample_CB(z_wave_node, z_wave_value)
                else:
                    logging.debug(f'Niet geregistreerd: value {z_wave_value.label} zit niet in {self.subscriptions[z_wave_node.node_id]}')
            else:
                logging.debug(f'Niet geregistreerd: node {z_wave_node.node_id} zit niet in {self.subscriptions}')
        else:
            logging.debug('Geen post_sample_CB')

    @staticmethod
    def zwave_signal_name(z_wave_node: ZWaveNode, z_wave_value: ZWaveValue) -> str:
        return f"{z_wave_value.label}_{z_wave_node.node_id}"
