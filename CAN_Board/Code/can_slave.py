import utime
from machine import Pin, PWM, ADC, SPI
from can_mcp2515 import CAN_MCP2515
from can_communication import (
    CANCommunication,
    CMD_SERIAL_NUMBER,
    CMD_READ_SENSOR,
    CMD_READ_ANALOG,
    CMD_READ_DIGITAL,
    CMD_SET_OUTPUT,
    CMD_SET_PWM,
    REQ_ID,
)

SERIAL_NUMBER = 12604

PWM_OUTPUTS = [1, 9, 8, 10, 15]
OUTPUTS = [2, 3]
ANALOG_INPUTS = [27]
DIGITAL_INPUTS = [22]


can = None
can_on = Pin(21, Pin.OUT)
can_int = Pin(20, Pin.IN, Pin.PULL_UP)

msg_pending = False


def on_can_irq(pin):
    global msg_pending
    msg_pending = True


def handle_frame(can_id, data):
    if can_id != REQ_ID:
        return

    comm = CANCommunication(can, data)
    request = comm.handle_request()
    if request is None:
        return

    cmd = request["cmd"]

    if cmd == CMD_SERIAL_NUMBER:
        comm.send_response(CMD_SERIAL_NUMBER, value=SERIAL_NUMBER)

    elif cmd == CMD_READ_SENSOR:
        temperature = 2500
        humidity = 5000
        pressure = 10132
        comm.send_response(
            CMD_READ_SENSOR,
            value=(temperature, humidity, pressure),
        )

    elif cmd == CMD_READ_ANALOG:
        idx = request["idx"]
        if idx in ANALOG_INPUTS:
            adc = ADC(Pin(idx))
            analog_value = adc.read_u16()
            comm.send_response(CMD_READ_ANALOG, idx=idx, value=analog_value)
        else:
            comm.error_response(reason_code=0x02)

    elif cmd == CMD_READ_DIGITAL:
        idx = request["idx"]
        if idx in DIGITAL_INPUTS:
            din = Pin(idx, Pin.IN)
            digital_value = din.value()
            comm.send_response(CMD_READ_DIGITAL, idx=idx, value=digital_value)
        else:
            comm.error_response(reason_code=0x02)

    elif cmd == CMD_SET_OUTPUT:
        idx = request["idx"]
        value = request["value"]
        if idx in OUTPUTS:
            out = Pin(idx, Pin.OUT)
            out.value(1 if value else 0)
            comm.send_response(CMD_SET_OUTPUT, idx=idx, value=value)
        else:
            comm.error_response(reason_code=0x02)

    elif cmd == CMD_SET_PWM:
        idx = request["idx"]
        duty = request["value"]
        if idx in PWM_OUTPUTS:
            pwm = PWM(Pin(idx))
            pwm.freq(1000)
            pwm.duty_u16(duty)
            comm.send_response(CMD_SET_PWM, idx=idx, value=duty)
        else:
            comm.error_response(reason_code=0x02)


def slave_loop():
    global can, msg_pending
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
    can.set_mode(0x00)
    can_int.irq(trigger=Pin.IRQ_FALLING, handler=on_can_irq)

    while True:
        if msg_pending:
            msg_pending = False
            while True:
                msg = can.recv_std()
                if msg is None:
                    break
                can_id, data = msg
                handle_frame(can_id, data)
        utime.sleep_ms(1)


if __name__ == "__main__":
    slave_loop()
