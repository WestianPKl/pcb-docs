import utime
from machine import Pin, SPI
from can_mcp2515 import CAN_MCP2515

REQ_ID = 0x700
RESP_ID = 0x701

DEVICE_ADDR = 0x50

CMD_SERIAL_NUMBER = 0x10
CMD_READ_SENSOR = 0x12
CMD_READ_ANALOG = 0x20
CMD_READ_DIGITAL = 0x21
CMD_SET_OUTPUT = 0x30
CMD_SET_PWM = 0x31

can_on = Pin(21, Pin.OUT)
can_int = Pin(20, Pin.IN)


def build_request(addr, cmd, idx=0, param=None):
    addr &= 0xFF
    cmd &= 0xFF
    idx &= 0xFF

    if param is None:
        p_hi = 0
        p_lo = 0
    else:
        p = param & 0xFFFF
        p_hi = (p >> 8) & 0xFF
        p_lo = p & 0xFF

    data = bytearray(8)
    data[0] = addr
    data[1] = cmd
    data[2] = idx
    data[3] = p_hi
    data[4] = p_lo
    return bytes(data)


def wait_for_response(can, req_cmd, timeout_ms=500):
    expected_cmd = (req_cmd | 0x40) & 0xFF
    t0 = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t0) < timeout_ms:
        msg = can.recv_std()
        if msg is None:
            utime.sleep_ms(5)
            continue

        can_id, data = msg
        if can_id != RESP_ID:
            continue
        if data[0] != DEVICE_ADDR:
            continue

        if data[1] == 0x7F:
            print(data)
            return None

        if data[1] != expected_cmd:
            continue

        return data
    return None


def test_serial_number(can):
    print("_________________________________")
    print("Serial number")
    frame = build_request(DEVICE_ADDR, CMD_SERIAL_NUMBER, idx=0, param=None)
    can.send_std(REQ_ID, frame)
    resp = wait_for_response(can, CMD_SERIAL_NUMBER)
    if resp is None:
        print("No response")
        return
    serial = (resp[2] << 8) | resp[3]
    print(resp)
    print(serial)
    print(f"0x{serial:04X}")
    print("_________________________________")


def test_sensor(can):
    print("_________________________________")
    print("Sensor data (T, rH, P)")
    frame = build_request(DEVICE_ADDR, CMD_READ_SENSOR, idx=0, param=None)
    can.send_std(REQ_ID, frame)
    resp = wait_for_response(can, CMD_READ_SENSOR)
    if resp is None:
        print("No response")
        return

    t_raw = (resp[2] << 8) | resp[3]
    h_raw = (resp[4] << 8) | resp[5]
    p_raw = (resp[6] << 8) | resp[7]

    temp_c = t_raw / 100.0
    hum_rh = h_raw / 100.0
    press_hp = p_raw / 10.0

    print(resp)
    print(f"Raw data: T={t_raw}, H={h_raw}, P={p_raw}")
    print(
        f"Sensor readings: T = {temp_c:.2f} °C, RH = {hum_rh:.2f} %, P = {press_hp:.1f} hPa"
    )
    print("_________________________________")


def u16_be(hi, lo):
    return ((hi & 0xFF) << 8) | (lo & 0xFF)


def adc_voltage(raw, vref=3.3, r_top=100000, r_bottom=100000, width=16):
    max_code = (1 << width) - 1
    raw = 0 if raw < 0 else (max_code if raw > max_code else raw)
    vadc = (raw / float(max_code)) * vref
    if r_bottom and r_bottom > 0:
        r_top = 0 if not r_top else r_top
        scale = (r_top + r_bottom) / float(r_bottom)
        vin = vadc * scale
    else:
        vin = vadc
    return vin, vadc


def test_analog(can, idx=0, vref=3.3, r1=100000, r2=100000):
    print("_________________________________")
    print(f"Analog data (idx={idx})")
    frame = build_request(DEVICE_ADDR, CMD_READ_ANALOG, idx=idx, param=None)
    can.send_std(REQ_ID, frame)
    resp = wait_for_response(can, CMD_READ_ANALOG)
    if resp is None:
        print("No response")
        return

    raw = u16_be(resp[2], resp[3])
    vin, vadc = adc_voltage(raw, vref=vref, r_top=r1, r_bottom=r2, width=16)
    print(resp)
    print(f"Raw ADC value: {raw}")
    print(
        f"Calculated voltage: U~ = {vin:.3f} / {vadc:.3f} V (vref={vref}, r1={r1}, r2={r2})"
    )
    print("_________________________________")


def test_digital(can, idx=0):
    print("_________________________________")
    print(f"Digital data (idx={idx})")
    frame = build_request(DEVICE_ADDR, CMD_READ_DIGITAL, idx=idx, param=None)
    can.send_std(REQ_ID, frame)
    resp = wait_for_response(can, CMD_READ_DIGITAL)
    if resp is None:
        print("No response")
        return
    state = 1 if resp[2] else 0
    print(resp)
    print(f"Raw digital value: {resp[2]}")
    print(f'State of {idx} = {state} ({"HIGH" if state else "LOW"})')
    print("_________________________________")


def test_set_output(can, idx=0, value=1):
    print("_________________________________")
    print(f"Digital output (idx={idx}), value:{value}")
    param = 1 if value else 0
    frame = build_request(DEVICE_ADDR, CMD_SET_OUTPUT, idx=idx, param=param)
    can.send_std(REQ_ID, frame)
    resp = wait_for_response(can, CMD_SET_OUTPUT)
    if resp is None:
        print("No response")
        return
    print(resp)
    print("_________________________________")


def test_set_pwm(can, idx=0, duty=32768):
    print("_________________________________")
    print(f"Digital PWM (idx={idx}), duty:{duty}")
    frame = build_request(DEVICE_ADDR, CMD_SET_PWM, idx=idx, param=duty)
    can.send_std(REQ_ID, frame)
    resp = wait_for_response(can, CMD_SET_PWM)
    if resp is None:
        print("No response")
        return
    print(resp)
    print("_________________________________")


def main():
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
    cs_pin = Pin(17, Pin.OUT)

    can = CAN_MCP2515(spi, cs_pin)

    utime.sleep(0.5)

    test_serial_number(can)
    test_sensor(can)
    test_analog(can, idx=27)
    test_digital(can, idx=22)

    test_set_output(can, idx=2, value=1)
    utime.sleep(2)
    test_set_output(can, idx=2, value=0)

    test_set_pwm(can, idx=1, duty=65535)
    utime.sleep(2)
    test_set_pwm(can, idx=1, duty=49151)
    utime.sleep(2)
    test_set_pwm(can, idx=1, duty=32768)
    utime.sleep(2)
    test_set_pwm(can, idx=1, duty=16384)
    utime.sleep(2)
    test_set_pwm(can, idx=1, duty=0)

    can_on.value(0)


if __name__ == "__main__":
    main()
