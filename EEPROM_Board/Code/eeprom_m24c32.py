from machine import I2C
import time


def _ticks_ms():
    try:
        return time.ticks_ms()
    except AttributeError:
        return int(time.time() * 1000)


def _ticks_diff(a, b):
    try:
        return time.ticks_diff(a, b)
    except AttributeError:
        return a - b


class EEPROM_M24C32:
    PAGE_SIZE = 32
    MEM_SIZE = 4096
    WRITE_CYCLE_MS = 5
    READY_TIMEOUT_MS = 50
    MAX_RETRIES = 5
    RETRY_DELAY_MS = 2

    def __init__(self, i2c: I2C, addr: int = 0x50):
        self.i2c = i2c
        self.addr = addr

    def _split_addr(self, mem_addr: int):
        if not (0 <= mem_addr < self.MEM_SIZE):
            raise ValueError("mem_addr out of range 0..4095")
        return (mem_addr >> 8) & 0xFF, mem_addr & 0xFF

    def _wait_write(self):
        start = _ticks_ms()
        while True:
            if self.is_ready():
                return True
            if _ticks_diff(_ticks_ms(), start) > self.READY_TIMEOUT_MS:
                return False
            time.sleep_ms(self.RETRY_DELAY_MS)

    def _safe_writeto(self, addr, buf, stop=True):
        last_err = None
        for _ in range(self.MAX_RETRIES):
            try:
                (
                    self.i2c.writeto(addr, buf, stop)
                    if hasattr(self.i2c, "writeto")
                    else self.i2c.write(buf)
                )
                return True
            except OSError as e:
                last_err = e
                time.sleep_ms(self.RETRY_DELAY_MS)
        raise OSError(
            f"EEPROM writeto failed after {self.MAX_RETRIES} retries: {last_err}"
        )

    def _safe_readfrom(self, addr, nbytes):
        last_err = None
        for _ in range(self.MAX_RETRIES):
            try:
                return self.i2c.readfrom(addr, nbytes)
            except OSError as e:
                last_err = e
                time.sleep_ms(self.RETRY_DELAY_MS)
        raise OSError(
            f"EEPROM readfrom failed after {self.MAX_RETRIES} retries: {last_err}"
        )

    def write_byte(self, mem_addr: int, value: int):
        ah, al = self._split_addr(mem_addr)
        value &= 0xFF
        buf = bytes([ah, al, value])
        self._safe_writeto(self.addr, buf)
        if not self._wait_write():
            raise OSError("EEPROM write timeout waiting for ready")

    def read_byte(self, mem_addr: int) -> int:
        ah, al = self._split_addr(mem_addr)

        self._safe_writeto(self.addr, bytes([ah, al]), False)
        return self._safe_readfrom(self.addr, 1)[0]

    def write_block(self, mem_addr: int, data: bytes):
        if not data:
            return

        pos = 0
        length = len(data)

        while pos < length:
            current_addr = mem_addr + pos
            if current_addr >= self.MEM_SIZE:
                raise ValueError("Attempted write beyond end of EEPROM")

            ah, al = self._split_addr(current_addr)

            page_offset = current_addr % self.PAGE_SIZE
            space_in_page = self.PAGE_SIZE - page_offset

            chunk_len = min(space_in_page, length - pos)
            chunk = data[pos : pos + chunk_len]

            buf = bytes([ah, al]) + chunk
            self._safe_writeto(self.addr, buf)
            if not self._wait_write():
                raise OSError("EEPROM write timeout waiting for ready")

            pos += chunk_len

    def read_block(self, mem_addr: int, length: int) -> bytes:
        if length <= 0:
            return b""
        if mem_addr + length > self.MEM_SIZE:
            raise ValueError("Attempted read beyond end of EEPROM")

        ah, al = self._split_addr(mem_addr)
        self._safe_writeto(self.addr, bytes([ah, al]), False)
        return self._safe_readfrom(self.addr, length)

    def write_string(self, mem_addr: int, text: str, add_zero=True):
        data = text.encode("utf-8")
        if add_zero:
            data += b"\x00"
        self.write_block(mem_addr, data)

    def read_string(self, mem_addr: int, max_len=64) -> str:
        raw = self.read_block(mem_addr, max_len)
        if b"\x00" in raw:
            raw = raw.split(b"\x00", 1)[0]
        return raw.decode("utf-8")

    def is_ready(self) -> bool:
        try:
            self.i2c.writeto(self.addr, b"\x00\x00")
            return True
        except OSError:
            return False

    def erase_full(self, fill: int = 0xFF):
        fill &= 0xFF
        page_data = bytes([fill]) * self.PAGE_SIZE

        addr = 0
        while addr < self.MEM_SIZE:
            self.write_block(addr, page_data)
            addr += self.PAGE_SIZE
