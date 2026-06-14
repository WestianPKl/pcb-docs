from machine import I2C
import time

REG_CONFIG = 0x00
REG_SHUNT_VOLT = 0x01
REG_BUS_VOLT = 0x02
REG_POWER = 0x03
REG_CURRENT = 0x04
REG_CALIB = 0x05
REG_MASK_ENABLE = 0x06
REG_ALERT_LIMIT = 0x07


class MEASUREMENT_INA226:
    def __init__(self, i2c: I2C, addr=0x40, r_shunt_ohm=0.1, max_current=3.2):
        self.i2c = i2c
        self.addr = addr
        self.r_shunt = r_shunt_ohm

        self._write_u16(REG_CONFIG, 0x4127)
        self.current_lsb = max_current / 32768.0
        cal = int(0.00512 / (self.current_lsb * self.r_shunt) + 0.5)
        self._write_u16(REG_CALIB, cal)

    def _write_u16(self, reg, value):
        buf = bytes([reg, (value >> 8) & 0xFF, value & 0xFF])
        try:
            self.i2c.writeto(self.addr, buf)
        except OSError as e:
            raise OSError(f"INA226 write_u16 failed (reg=0x{reg:02X}): {e}")

    def _read_u16(self, reg):
        try:
            self.i2c.writeto(self.addr, bytes([reg]))
            data = self.i2c.readfrom(self.addr, 2)
            return (data[0] << 8) | data[1]
        except OSError as e:
            raise OSError(f"INA226 read_u16 failed (reg=0x{reg:02X}): {e}")

    def _read_s16(self, reg):
        v = self._read_u16(reg)
        if v & 0x8000:
            v -= 0x10000
        return v

    def bus_voltage_V(self):
        raw = self._read_u16(REG_BUS_VOLT)
        return raw * 1.25e-3

    def shunt_voltage_V(self):
        raw = self._read_s16(REG_SHUNT_VOLT)
        return raw * 2.5e-6

    def current_A(self):
        raw = self._read_s16(REG_CURRENT)
        return raw * self.current_lsb

    def power_W(self):
        raw = self._read_u16(REG_POWER)
        power_lsb = 25 * self.current_lsb
        return raw * power_lsb

    def set_overcurrent_alert(self, current_limit_A):
        self._write_u16(REG_MASK_ENABLE, 0x8002)
        v_shunt = current_limit_A * self.r_shunt
        limit_raw = int(v_shunt / 2.5e-6 + 0.5)
        self._write_u16(REG_ALERT_LIMIT, limit_raw)

    def clear_alert(self):
        _ = self._read_u16(REG_MASK_ENABLE)

    def is_present(self) -> bool:
        try:
            _ = self._read_u16(REG_CONFIG)
            return True
        except OSError:
            return False
