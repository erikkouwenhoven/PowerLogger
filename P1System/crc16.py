# https://github.com/raphaelnunes67/MODBUS-CRC16/blob/main/CRC16.py
# https://www.circuitsonline.net/forum/view/165811

def modbus_crc16(buf: bytes) -> int:
    table = [0x0000, 0xA001]
    crc = 0x0000
    for byte in buf:
        crc ^= byte
        for bit in range(8):
            xor = crc & 0x01
            crc >>= 1
            crc ^= table[xor]
    return crc
