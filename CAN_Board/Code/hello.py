from machine import Pin, SPI
import utime
from can_mcp2515 import CAN_MCP2515

can_on = Pin(21, Pin.OUT)


def main():
    print("=== SIMPLE CAN TX ===")
    print("Wysyłam co 500 ms ramkę ID=0x100, data='Hello'")

    # Włącz moduł CAN
    can_on.value(1)
    utime.sleep(0.5)

    # SPI0
    spi = SPI(
        0,
        baudrate=1_000_000,
        polarity=0,
        phase=0,
        sck=Pin(18),
        mosi=Pin(19),
        miso=Pin(16),
    )
    cs = Pin(17, Pin.OUT, value=1)

    # MCP2515
    can = CAN_MCP2515(spi, cs)
    can.set_mode(0x00)  # MODE_NORMAL

    msg = b"Hello"

    while True:
        can.send_std(0x100, msg)
        print("TX: wysłano 'Hello'")
        utime.sleep_ms(500)


if __name__ == "__main__":
    main()
