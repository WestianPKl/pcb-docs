from machine import Pin, SPI
import utime
from can_mcp2515 import CAN_MCP2515

can_on = Pin(21, Pin.OUT)
MODE_LOOPBACK = 0x40

def main():
    print("=== TEST CAN MCP2515 – LOOPBACK (ten moduł) ===")

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

    can = CAN_MCP2515(spi, cs_pin)
    can.set_mode(MODE_LOOPBACK)

    test_id = 0x123
    test_data = b"Hello"

    print("Wysyłam ramkę ID=0x{:03X}, data={}".format(test_id, [hex(b) for b in test_data]))
    can.send_std(test_id, test_data)

    received = None
    t0 = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t0) < 500:
        msg = can.recv_std()
        if msg is not None:
            received = msg
            break
        utime.sleep_ms(10)

    if received is None:
        print("⚠ LOOPBACK: brak ramki – ten moduł coś ma z odbiorem")
    else:
        rid, rdata = received
        print("✓ LOOPBACK OK na tym module:")
        print("  ID   = 0x{:03X}".format(rid))
        print("  data =", [hex(b) for b in rdata])
        print("  tekst =", rdata.decode("ascii"))

    can_on.value(0)
    print("CAN: zasilanie wyłączone\n")
    
if __name__ == "__main__":
    main()
