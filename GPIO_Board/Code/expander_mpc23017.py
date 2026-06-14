from machine import I2C


IODIRA = 0x00
IODIRB = 0x01
GPPUA = 0x0C
GPPUB = 0x0D
GPIOA = 0x12
GPIOB = 0x13
OLATA = 0x14
OLATB = 0x15

GPINTENA = 0x04
GPINTENB = 0x05
DEFVALA = 0x06
DEFVALB = 0x07
INTCONA = 0x08
INTCONB = 0x09
IOCON = 0x0A
INTFA = 0x0E
INTFB = 0x0F
INTCAPA = 0x10
INTCAPB = 0x11


class EXPANDER_MCP23017:
    IN = 1
    OUT = 0

    def __init__(self, i2c: I2C, addr: int = 0x20):
        self.i2c = i2c
        self.addr = addr

        self._write_reg(IODIRA, 0xFF)
        self._write_reg(IODIRB, 0xFF)
        self._write_reg(GPPUA, 0x00)
        self._write_reg(GPPUB, 0x00)

    def _write_reg(self, reg, value):
        try:
            self.i2c.writeto(self.addr, bytes([reg, value & 0xFF]))
        except OSError as e:
            raise OSError(f"MCP23017 write_reg failed (reg=0x{reg:02X}): {e}")

    def _read_reg(self, reg):
        try:
            self.i2c.writeto(self.addr, bytes([reg]))
            return self.i2c.readfrom(self.addr, 1)[0]
        except OSError as e:
            raise OSError(f"MCP23017 read_reg failed (reg=0x{reg:02X}): {e}")

    def _pin_to_port_bit(self, pin):
        if not (0 <= pin <= 15):
            raise ValueError("Pin musi być z zakresu 0..15")
        if pin < 8:
            return 0, pin
        else:
            return 1, pin - 8

    def pin_mode(self, pin, mode):
        port, bit = self._pin_to_port_bit(pin)
        mask = 1 << bit

        if port == 0:
            iodir = self._read_reg(IODIRA)
            if mode == self.IN:
                iodir |= mask
            else:
                iodir &= ~mask
            self._write_reg(IODIRA, iodir)
        else:
            iodir = self._read_reg(IODIRB)
            if mode == self.IN:
                iodir |= mask
            else:
                iodir &= ~mask
            self._write_reg(IODIRB, iodir)

    def set_pullup(self, pin, enable: bool):
        port, bit = self._pin_to_port_bit(pin)
        mask = 1 << bit

        if port == 0:
            gppu = self._read_reg(GPPUA)
            if enable:
                gppu |= mask
            else:
                gppu &= ~mask
            self._write_reg(GPPUA, gppu)
        else:
            gppu = self._read_reg(GPPUB)
            if enable:
                gppu |= mask
            else:
                gppu &= ~mask
            self._write_reg(GPPUB, gppu)

    def digital_write(self, pin, value: bool):
        port, bit = self._pin_to_port_bit(pin)
        mask = 1 << bit

        if port == 0:
            olat = self._read_reg(OLATA)
            if value:
                olat |= mask
            else:
                olat &= ~mask
            self._write_reg(OLATA, olat)
        else:
            olat = self._read_reg(OLATB)
            if value:
                olat |= mask
            else:
                olat &= ~mask
            self._write_reg(OLATB, olat)

    def digital_read(self, pin) -> int:
        port, bit = self._pin_to_port_bit(pin)
        mask = 1 << bit

        if port == 0:
            gpio = self._read_reg(GPIOA)
        else:
            gpio = self._read_reg(GPIOB)

        return 1 if (gpio & mask) else 0

    def write_port(self, port, value):
        if port == 0:
            self._write_reg(OLATA, value)
        else:
            self._write_reg(OLATB, value)

    def read_port(self, port):
        if port == 0:
            return self._read_reg(GPIOA)
        else:
            return self._read_reg(GPIOB)

    def setup_interrupt_on_change_B(self, pin_bit=1):
        mask = 1 << pin_bit

        iocon = self._read_reg(IOCON)
        iocon &= ~(0x80 | 0x40 | 0x04 | 0x02)
        self._write_reg(IOCON, iocon)

        intconb = self._read_reg(INTCONB)
        intconb &= ~mask
        self._write_reg(INTCONB, intconb)

        gpintenb = self._read_reg(GPINTENB)
        gpintenb |= mask
        self._write_reg(GPINTENB, gpintenb)
        _ = self._read_reg(INTFB)
        _ = self._read_reg(INTCAPB)

    def get_interrupt_source_B(self):
        intf = self._read_reg(INTFB)
        intcap = self._read_reg(INTCAPB)
        return intf, intcap

    def setup_interrupt_on_change_A(self, pin_bit=1):
        mask = 1 << pin_bit

        iocon = self._read_reg(IOCON)
        iocon &= ~(0x80 | 0x40 | 0x04 | 0x02)
        self._write_reg(IOCON, iocon)

        intcona = self._read_reg(INTCONA)
        intcona &= ~mask
        self._write_reg(INTCONA, intcona)

        gpintena = self._read_reg(GPINTENA)
        gpintena |= mask
        self._write_reg(GPINTENA, gpintena)
        _ = self._read_reg(INTFA)
        _ = self._read_reg(INTCAPA)

    def get_interrupt_source_A(self):
        intf = self._read_reg(INTFA)
        intcap = self._read_reg(INTCAPA)
        return intf, intcap

    def is_present(self) -> bool:
        try:
            _ = self._read_reg(IODIRA)
            return True
        except OSError:
            return False
