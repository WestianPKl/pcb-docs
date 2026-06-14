# PCB Manager — Board Collection

A collection of custom PCB designs created in **KiCAD**, centered around the **Raspberry Pi Pico (RP2040)** platform. Each board is a standalone module that connects to the Main Board and extends its functionality via I2C, SPI, or UART.

**Author:** Piotr Kłyś  
**Tool:** KiCAD 8.x  
**Firmware:** MicroPython (Pico boards), AVR-GCC (ATmega boards)

---

## Boards Overview

| Board | Version | Interface | IC / Description |
|---|---|---|---|
| [Main_Board](#main_board) | 1.0 / 1.1 / 1.2a | — | Raspberry Pi Pico test & integration board |
| [CAN_Board](#can_board) | 1.0 | SPI | MCP2515 — CAN bus controller |
| [EEPROM_Board](#eeprom_board) | 1.0 | I2C | M24C32 — 32 Kbit EEPROM |
| [GPIO_Board](#gpio_board) | 1.0 | I2C | MCP23017 — 16-bit GPIO expander |
| [INA_Board](#ina_board) | 1.0 | I2C | INA226 — voltage / current / power monitor |
| [RTC_Board](#rtc_board) | 1.0 | I2C | PCF8563T — real-time clock |
| [Relay_Board](#relay_board) | 1.0 | GPIO | 2-channel relay module |
| [Modbus_Board](#modbus_board) | 1.0 | UART | RS-485 / Modbus RTU |
| [Power_Board](#power_board) | 1.0 | — | DC power supply module |
| [MOSFET_Board](#mosfet_board) | 1.0 | GPIO | High-side / low-side MOSFET switch |
| [Amplifier_Board](#amplifier_board) | — | Analog | Signal amplifier |
| [ATMega_Board](#atmega_board) | 1.0 | — | ATmega (through-hole) development board |
| [ATMegaSMD_Board](#atmegasmd_board) | 1.0 | — | ATmega (SMD) development board |
| [Tree_Board](#tree_board) | — | — | AVR LED Christmas tree |
| [IoT_Logger_B_1.0](#iot_logger_b) | 1.0 | — | IoT data logger revision B |
| [IoT_Logger_C_1.0](#iot_logger_c) | 1.0 | — | IoT data logger revision C |
| [Pico_TH_Logger_SMD_PCF8563T_2.1](#pico_th_logger) | 2.1 | I2C | Pico temp/humidity logger with RTC |
| [Pico_TH_Logger_Relay_SMD_PCF8563T_2.1](#pico_th_logger_relay) | 2.1 | I2C | Pico temp/humidity logger with RTC + relay |

---

## Board Details

### Main_Board

The central development and integration board built around the **Raspberry Pi Pico**. Used to test all peripheral modules in the collection.

**Features:**
- RGB LED (PWM)
- 2× status LEDs (PWM)
- Buzzer (PWM)
- 2× push buttons
- ADC input with 100 kΩ / 200 kΩ voltage divider
- Connectors for all expansion boards (I2C, SPI, CAN, EEPROM, GPIO, INA, RTC, Relay)
- Optional multi-threaded test runner (`_thread`)

**Firmware:** `Main_Board/Code/main.py`

---

### CAN_Board

CAN bus communication module using the **MCP2515** controller over SPI.

**Features:**
- SPI interface to Pico
- Standard CAN 2.0 frame support
- Loopback, sniffer, and master/slave test scripts

**Firmware:** `CAN_Board/Code/`
- `can_mcp2515.py` — low-level MCP2515 driver
- `can_communication.py` — higher-level protocol
- `hello.py`, `loopback.py`, `sniffer.py`, `can_slave.py`, `can_test.py` — examples

---

### EEPROM_Board

Non-volatile storage expansion using the **M24C32** (32 Kbit / 4 KB) I2C EEPROM.

**Firmware:** `EEPROM_Board/Code/eeprom_m24c32.py`

---

### GPIO_Board

16-bit I2C GPIO expander using the **MCP23017**, providing two 8-bit ports (Port A / Port B) with interrupt support.

**Firmware:** `GPIO_Board/Code/expander_mpc23017.py`

---

### INA_Board

High-side power monitoring using the **INA226** — measures bus voltage, shunt voltage, current, and power via I2C.

**Default configuration:**
- Shunt resistor: 100 mΩ
- Max current: 3.2 A
- Alert pin supported

**Firmware:** `INA_Board/Code/measurement_ina226.py`

---

### RTC_Board

Real-time clock module using the **PCF8563T** via I2C. Provides timekeeping, alarm, and 1 Hz clock output.

**Features:**
- Date / time read and write
- Alarm support
- 1 Hz CLKOUT output
- Battery backup pin

**Firmware:** `RTC_Board/Code/rtc_pcf8563.py`

---

### Relay_Board

2-channel relay board controlled via GPIO from the Pico.

---

### Modbus_Board

RS-485 transceiver board enabling **Modbus RTU** communication over UART.

---

### Power_Board

DC power supply module — voltage regulation and distribution for the board ecosystem.

---

### MOSFET_Board

MOSFET-based switching board for controlling higher-power loads from Pico GPIO.

---

### Amplifier_Board

Analog signal amplifier module.

---

### ATMega_Board

Through-hole **ATmega** development board — classic DIP package, ISP programming header.

---

### ATMegaSMD_Board

SMD variant of the ATmega development board — compact form factor.

---

### Tree_Board

AVR-based LED Christmas tree — decorative board with animated LED patterns.

**Firmware:** `Tree_Board/TreeCode/main.c` (AVR-GCC)  
**Gerbers / renders:** `Tree_Board/PROD/`

---

### IoT_Logger_B

IoT data logger — revision B.

---

### IoT_Logger_C

IoT data logger — revision C. Improved layout over revision B.

---

### Pico_TH_Logger_SMD_PCF8563T_2.1

Compact SMD temperature and humidity logger based on Raspberry Pi Pico with a **PCF8563T** RTC for timestamped logging.

---

### Pico_TH_Logger_Relay_SMD_PCF8563T_2.1

Extended version of the TH Logger adding a **relay output** for threshold-based control (e.g. ventilation, heating).

---

## Repository Structure

```
pcb-docs/
├── <BoardName>/
│   ├── <BoardName>.kicad_pro      # KiCAD project
│   ├── <BoardName>.kicad_sch      # Schematic
│   ├── <BoardName>.kicad_pcb      # PCB layout
│   ├── Code/                      # MicroPython / C firmware
│   └── PROD/                      # Gerbers, renders, BOM exports
├── Boards_BOM.ods                 # Combined Bill of Materials
└── README.md
```

Each board may contain multiple revision subdirectories (e.g. `1.0/`, `1.1/`).

---

## Getting Started

### Requirements

- **KiCAD 8.x** — to open schematics and PCB layouts
- **Thonny** or **mpremote** — to flash MicroPython firmware to Pico
- **AVR-GCC + avrdude** — for Tree_Board / ATmega boards

### Running firmware on Pico

1. Flash [MicroPython](https://micropython.org/download/RPI_PICO/) to your Raspberry Pi Pico.
2. Copy the relevant driver file(s) from `<BoardName>/Code/` to the Pico filesystem.
3. Run or import the module from the REPL or `main.py`.

```python
# Example — INA226 power monitor
from machine import I2C, Pin
from measurement_ina226 import MEASUREMENT_INA226

i2c = I2C(0, sda=Pin(4), scl=Pin(5))
ina = MEASUREMENT_INA226(i2c, r_shunt_ohm=0.1, max_current=3.2)
print(ina.read_voltage(), ina.read_current(), ina.read_power())
```

---

## Bill of Materials

A combined BOM for all boards is available in [`Boards_BOM.ods`](Boards_BOM.ods) (OpenDocument Spreadsheet).

---

## License

This project is licensed under the [CERN Open Hardware Licence v2 - Permissive (CERN-OHL-P)](https://ohwr.org/cern_ohl_p_v2.txt).

You are free to use, modify, and manufacture these designs. Attribution appreciated.
