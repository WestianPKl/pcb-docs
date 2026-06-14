from machine import Pin, SPI
import utime
from can_mcp2515 import CAN_MCP2515

can_on  = Pin(21, Pin.OUT)
can_int = Pin(20, Pin.IN, Pin.PULL_UP)
MODE_NORMAL = 0x00

def main():
    print("=== SNIFFER: moduł, który był nadajnikiem ===")
    can_on.value(1)
    utime.sleep(0.5)

    spi = SPI(
        0,
        baudrate=1_000_000,
        polarity=0,
        phase=0,
        sck=Pin(18),
        mosi=Pin(19),
        miso=Pin(16),
    )
    cs_pin = Pin(17, Pin.OUT, value=1)

    can = CAN_MCP2515(spi, cs_pin, can_int)
    can.set_mode(MODE_NORMAL)

    print("Czekam na jakiekolwiek ramki...")

    while True:
        msg = can.recv_std()
        if msg is not None:
            rid, rdata = msg
            print("RX: ID=0x{:03X}, data={}".format(rid, [hex(b) for b in rdata]))
            try:
                print("    tekst =", rdata.decode("ascii"))
            except:
                pass
        utime.sleep_ms(10)
        
if __name__ == "__main__":
    main()