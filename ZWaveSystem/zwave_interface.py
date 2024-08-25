import logging
from datetime import datetime
from ZWaveSystem.network_interface import NetworkInterface
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from DataHolder.data_item import DataItemSpec, DataItem


class ZWaveInterface:

    def __init__(self, post_sample_cb):
        self.post_sample_CB = post_sample_cb
        self.network_interface = NetworkInterface(self._value_received_CB)
        self.subscriptions: dict[int, list[str]] | None = None  # registered node-valueIDs that are called back

    def register(self, subscriptions: dict[int, list[str]] | None):
        self.subscriptions = subscriptions

    def _value_received_CB(self, z_wave_node: ZWaveNode, z_wave_value: ZWaveValue):
        logging.info(f'valueReceived callback from network: node={z_wave_node.node_id}, parent_id {z_wave_value.parent_id}, value={z_wave_value.data} {z_wave_value.units} ({z_wave_value.label}, {z_wave_value.value_id})')
        if self.post_sample_CB:
            if z_wave_node.node_id in self.subscriptions:
                if z_wave_value.label in self.subscriptions[z_wave_node.node_id]:
                    data_item = self.zwave_to_data_item(z_wave_node, z_wave_value)
                    self.post_sample_CB(data_item)
                else:
                    logging.debug(f'Niet geregistreerd: value {z_wave_value.label} zit niet in {self.subscriptions[z_wave_node.node_id]}')
            else:
                logging.debug(f'Niet geregistreerd: node {z_wave_node.node_id} zit niet in {self.subscriptions}')
        else:
            logging.debug('Geen post_sample_CB')

    def zwave_to_data_item(self, z_wave_node: ZWaveNode, z_wave_value: ZWaveValue) -> DataItem:
        zwave_signal_name = self.zwave_signal_name(z_wave_node, z_wave_value)
        data_item = DataItem(DataItemSpec({zwave_signal_name: z_wave_value.units}),
                             timestamp=datetime.timestamp(datetime.now()))
        data_item.set_value(zwave_signal_name, z_wave_value.data)
        return data_item

    @staticmethod
    def zwave_signal_name(z_wave_node: ZWaveNode, z_wave_value: ZWaveValue) -> str:
        return f"{z_wave_value.label}_{z_wave_node.node_id}"
