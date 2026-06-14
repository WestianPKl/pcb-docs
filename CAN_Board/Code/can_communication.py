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


class CANCommunication:
    def __init__(self, can_bus: CAN_MCP2515, data: bytes = None):
        self.can_bus = can_bus
        self.data = data

    def error_response(self, reason_code: int = 0x01):
        data = bytearray(8)
        data[0] = DEVICE_ADDR
        data[1] = 0x7F
        data[2] = reason_code & 0xFF
        self.can_bus.send_std(RESP_ID, bytes(data))

    def handle_request(self):

        if self.data is None or len(self.data) < 2:
            return None

        addr = self.data[0]
        cmd = self.data[1]
        idx = self.data[2] if len(self.data) > 2 else 0
        p_hi = self.data[3] if len(self.data) > 3 else 0
        p_lo = self.data[4] if len(self.data) > 4 else 0
        param = (p_hi << 8) | p_lo

        if addr != DEVICE_ADDR:
            return None

        if cmd == CMD_SERIAL_NUMBER:
            return {"cmd": CMD_SERIAL_NUMBER}
        elif cmd == CMD_READ_SENSOR:
            return {"cmd": CMD_READ_SENSOR}
        elif cmd == CMD_READ_ANALOG:
            return {"cmd": CMD_READ_ANALOG, "idx": idx}
        elif cmd == CMD_READ_DIGITAL:
            return {"cmd": CMD_READ_DIGITAL, "idx": idx}
        elif cmd == CMD_SET_OUTPUT:
            return {"cmd": CMD_SET_OUTPUT, "idx": idx, "value": param}
        elif cmd == CMD_SET_PWM:
            duty_cycle = param
            return {"cmd": CMD_SET_PWM, "idx": idx, "value": duty_cycle}
        else:
            self.error_response(reason_code=0x01)
            return None

    def send_response(self, cmd: int, idx: int = None, value: int | list = None):
        data = bytearray(8)
        data[0] = DEVICE_ADDR
        data[1] = cmd | 0x40

        if cmd == CMD_SERIAL_NUMBER:
            if isinstance(value, int):
                data[2] = (value >> 8) & 0xFF
                data[3] = value & 0xFF
        elif cmd == CMD_READ_SENSOR:
            t, h, p = value
            data[2] = (t >> 8) & 0xFF
            data[3] = t & 0xFF
            data[4] = (h >> 8) & 0xFF
            data[5] = h & 0xFF
            data[6] = (p >> 8) & 0xFF
            data[7] = p & 0xFF
        elif cmd == CMD_READ_ANALOG:
            if isinstance(value, int):
                data[2] = (value >> 8) & 0xFF
                data[3] = value & 0xFF
        elif cmd == CMD_READ_DIGITAL:
            state = 1 if value else 0
            data[2] = state & 0xFF
        elif cmd == CMD_SET_OUTPUT:
            if idx is not None:
                data[2] = idx & 0xFF
        elif cmd == CMD_SET_PWM:
            if idx is not None:
                data[2] = idx & 0xFF
        else:
            return self.error_response(reason_code=0x02)

        self.can_bus.send_std(RESP_ID, bytes(data))
