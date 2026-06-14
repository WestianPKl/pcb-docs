from machine import SPI, Pin
import utime

CMD_RESET = 0xC0
CMD_READ = 0x03
CMD_WRITE = 0x02
CMD_BIT_MODIFY = 0x05
CMD_READ_STATUS = 0xA0
CMD_RX_STATUS = 0xB0
CMD_RTS_TXB0 = 0x81

CANSTAT = 0x0E
CANCTRL = 0x0F
CNF1 = 0x2A
CNF2 = 0x29
CNF3 = 0x28
CANINTE = 0x2B
CANINTF = 0x2C

TXB0CTRL = 0x30
TXB0SIDH = 0x31
TXB0SIDL = 0x32
TXB0EID8 = 0x33
TXB0EID0 = 0x34
TXB0DLC = 0x35
TXB0D0 = 0x36

RXB0CTRL = 0x60
RXB0SIDH = 0x61
RXB0SIDL = 0x62
RXB0EID8 = 0x63
RXB0EID0 = 0x64
RXB0DLC = 0x65
RXB0D0 = 0x66

MODE_NORMAL = 0x00
MODE_SLEEP = 0x20
MODE_LOOPBACK = 0x40
MODE_LISTEN = 0x60
MODE_CONFIG = 0x80


class CAN_MCP2515:
    def __init__(self, spi: SPI, cs_pin: Pin, int_pin: Pin = None):
        self.spi = spi
        self.cs = cs_pin
        self.int_pin = int_pin

        self.cs.init(Pin.OUT, value=1)

        self._reset()
        utime.sleep_ms(5)

        self._config_500k_20mhz()

        if not self.set_mode(MODE_NORMAL):
            raise OSError("MCP2515: failed to enter NORMAL mode")

    def _cs_low(self):
        self.cs.value(0)

    def _cs_high(self):
        self.cs.value(1)

    def _reset(self):
        try:
            self._cs_low()
            self.spi.write(bytes([CMD_RESET]))
        finally:
            self._cs_high()

    def _write_reg(self, addr, value):
        try:
            self._cs_low()
            self.spi.write(bytes([CMD_WRITE, addr, value & 0xFF]))
        finally:
            self._cs_high()

    def _read_reg(self, addr):
        try:
            self._cs_low()
            self.spi.write(bytes([CMD_READ, addr]))
            val = self.spi.read(1, 0x00)[0]
            return val
        finally:
            self._cs_high()

    def _bit_modify(self, addr, mask, data):
        try:
            self._cs_low()
            self.spi.write(bytes([CMD_BIT_MODIFY, addr, mask & 0xFF, data & 0xFF]))
        finally:
            self._cs_high()

    def set_mode(self, mode):
        self._bit_modify(CANCTRL, 0xE0, mode)
        for _ in range(100):
            stat = self._read_reg(CANSTAT) & 0xE0
            if stat == mode:
                return True
            utime.sleep_ms(1)
        return False

    def _config_500k_20mhz(self):
        self.set_mode(MODE_CONFIG)

        self._write_reg(CNF1, 0x00)
        self._write_reg(CNF2, 0xFA)
        self._write_reg(CNF3, 0x87)

        self._write_reg(CANINTE, 0x01)
        self._write_reg(RXB0CTRL, 0x60)

    def send_std(self, can_id: int, data: bytes):
        dlc = min(len(data), 8)
        can_id &= 0x7FF

        sidh = (can_id >> 3) & 0xFF
        sidl = (can_id & 0x07) << 5

        self._write_reg(TXB0SIDH, sidh)
        self._write_reg(TXB0SIDL, sidl)
        self._write_reg(TXB0EID8, 0x00)
        self._write_reg(TXB0EID0, 0x00)
        self._write_reg(TXB0DLC, dlc & 0x0F)

        for i in range(dlc):
            self._write_reg(TXB0D0 + i, data[i])

        try:
            self._cs_low()
            self.spi.write(bytes([CMD_RTS_TXB0]))
        finally:
            self._cs_high()
        return True

    def recv_std(self):
        intf = self._read_reg(CANINTF)
        if not (intf & 0x01):
            return None

        sidh = self._read_reg(RXB0SIDH)
        sidl = self._read_reg(RXB0SIDL)
        dlc = self._read_reg(RXB0DLC) & 0x0F

        can_id = (sidh << 3) | (sidl >> 5)

        data = bytearray()
        for i in range(dlc):
            data.append(self._read_reg(RXB0D0 + i))

        self._bit_modify(CANINTF, 0x01, 0x00)

        return can_id, bytes(data)
