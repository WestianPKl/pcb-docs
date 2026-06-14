import machine
import utime, time
from machine import Pin, PWM, ADC, I2C, SPI
from rtc_pcf8563 import RTC_PCF8563
from eeprom_m24c32 import EEPROM_M24C32
from expander_mpc23017 import EXPANDER_MCP23017
from measurement_ina226 import MEASUREMENT_INA226
from can_mcp2515 import CAN_MCP2515
import _thread

relay = 0
rtc = 0
eeprom = 0
gpio = 0
ina_state = 0
can_module = 0

if relay != 1:

    buzzer = PWM(Pin(15))
    buzzer.freq(1000)
else:
    relay1 = Pin(14, Pin.OUT)
    relay2 = Pin(15, Pin.OUT)

if rtc == 1:
    adc_rtc = ADC(Pin(26))
    rtc_on = Pin(11, Pin.OUT)
    rtc_int = Pin(12, Pin.IN)
    rtc_clk = Pin(13, Pin.IN)

if eeprom == 1:
    eeprom_on = Pin(11, Pin.OUT)

if gpio == 1:
    gpio_on = Pin(11, Pin.OUT)
    gpio_inta = Pin(12, Pin.IN, Pin.PULL_UP)
    gpio_intb = Pin(13, Pin.IN, Pin.PULL_UP)

if ina_state == 1:
    ina_on = Pin(11, Pin.OUT)
    ina_alert = Pin(13, Pin.IN, Pin.PULL_UP)

if can_module == 1:
    can_on = Pin(21, Pin.OUT)
    can_int = Pin(20, Pin.IN)
else:
    button1 = Pin(21, Pin.IN, Pin.PULL_UP)
    button2 = Pin(22, Pin.IN, Pin.PULL_UP)

led_red = PWM(Pin(9))
led_green = PWM(Pin(10))
led_blue = PWM(Pin(8))

led_red.freq(1000)
led_green.freq(1000)
led_blue.freq(1000)

led_on_off_1 = PWM(Pin(2))
led_on_off_2 = PWM(Pin(3))
led_on_off_1.freq(1000)
led_on_off_2.freq(1000)

adc = ADC(Pin(27))

test_running = True


def read_voltage():
    """Read voltage from 100k/200k divider"""
    adc_value = adc.read_u16()
    voltage_adc = (adc_value / 65535) * 3.3
    voltage_input = voltage_adc * 1.5
    return voltage_input, voltage_adc, adc_value


def test_buzzer():
    """Buzzer test - basic + scale"""
    print("=== BUZZER TEST (GPIO15) ===")
    print("Basic test:")
    buzzer.duty_u16(32768)
    print("Buzzer ON (1 s)")
    utime.sleep(1)
    buzzer.duty_u16(0)
    print("Buzzer OFF")
    utime.sleep(0.5)
    print("C-major scale:")
    notes = [
        (262, "C"),
        (294, "D"),
        (330, "E"),
        (349, "F"),
        (392, "G"),
        (440, "A"),
        (494, "B"),
        (523, "C"),
    ]

    for freq, note in notes:
        print(f"Note {note} ({freq}Hz)")
        buzzer.freq(freq)
        buzzer.duty_u16(32768)
        utime.sleep(0.5)
        buzzer.duty_u16(0)
        utime.sleep(0.1)

    buzzer.duty_u16(0)
    print("Buzzer test finished\n")


def test_rgb_led():
    """RGB LED test with basic colors"""
    print("=== RGB LED TEST (GPIO8=blue, GPIO9=red, GPIO10=green) ===")

    colors = [
        ("Red", 65535, 0, 0),
        ("Green", 0, 65535, 0),
        ("Blue", 0, 0, 65535),
        ("Yellow", 65535, 65535, 0),
        ("Magenta", 65535, 0, 65535),
        ("Cyan", 0, 65535, 65535),
        ("White", 65535, 65535, 65535),
    ]

    for color_name, r, g, b in colors:
        print(f"Color: {color_name}")
        led_red.duty_u16(r)
        led_green.duty_u16(g)
        led_blue.duty_u16(b)
        utime.sleep(1)
    led_red.duty_u16(0)
    led_green.duty_u16(0)
    led_blue.duty_u16(0)
    print("RGB LED test finished\n")


def test_rgb_fade():
    """RGB fade test"""
    print("=== RGB FADE TEST ===")
    print("Red fade...")
    for duty in range(0, 65536, 2000):
        led_red.duty_u16(duty)
        utime.sleep_ms(30)
    for duty in range(65535, -1, -2000):
        led_red.duty_u16(duty)
        utime.sleep_ms(30)
    print("Green fade...")
    for duty in range(0, 65536, 2000):
        led_green.duty_u16(duty)
        utime.sleep_ms(30)
    for duty in range(65535, -1, -2000):
        led_green.duty_u16(duty)
        utime.sleep_ms(30)
    print("Blue fade...")
    for duty in range(0, 65536, 2000):
        led_blue.duty_u16(duty)
        utime.sleep_ms(30)
    for duty in range(65535, -1, -2000):
        led_blue.duty_u16(duty)
        utime.sleep_ms(30)

    led_red.duty_u16(0)
    led_green.duty_u16(0)
    led_blue.duty_u16(0)

    print("RGB fade test finished\n")


def test_simple_leds():
    """Simple LEDs test on GPIO2 and GPIO3"""
    print("=== TEST LEDs GPIO2 and GPIO3 ===")
    print("ON/OFF test:")
    print("LED GPIO2 ON")
    led_on_off_1.duty_u16(65535)
    utime.sleep(1)
    print("LED GPIO2 OFF")
    led_on_off_1.duty_u16(0)
    utime.sleep(0.5)
    print("LED GPIO3 ON")
    led_on_off_2.duty_u16(65535)
    utime.sleep(1)
    print("LED GPIO3 OFF")
    led_on_off_2.duty_u16(0)
    utime.sleep(0.5)
    print("Both LEDs ON")
    led_on_off_1.duty_u16(65535)
    led_on_off_2.duty_u16(65535)
    utime.sleep(1)
    print("Both LEDs OFF")
    led_on_off_1.duty_u16(0)
    led_on_off_2.duty_u16(0)
    utime.sleep(0.5)
    print("Simple LEDs test finished\n")


def test_simple_leds_fade():
    """Simple LEDs fade test"""
    print("=== SIMPLE LEDs FADE TEST (GPIO2/3) ===")
    print("Fade LED GPIO2...")
    for duty in range(0, 65536, 2000):
        led_on_off_1.duty_u16(duty)
        utime.sleep_ms(20)
    for duty in range(65535, -1, -2000):
        led_on_off_1.duty_u16(duty)
        utime.sleep_ms(20)
    utime.sleep(0.3)
    print("Fade LED GPIO3...")
    for duty in range(0, 65536, 2000):
        led_on_off_2.duty_u16(duty)
        utime.sleep_ms(20)
    for duty in range(65535, -1, -2000):
        led_on_off_2.duty_u16(duty)
        utime.sleep_ms(20)
    utime.sleep(0.3)
    print("Synchronous fade...")
    for duty in range(0, 65536, 1000):
        led_on_off_1.duty_u16(duty)
        led_on_off_2.duty_u16(duty)
        utime.sleep_ms(15)
    for duty in range(65535, -1, -1000):
        led_on_off_1.duty_u16(duty)
        led_on_off_2.duty_u16(duty)
        utime.sleep_ms(15)
    led_on_off_1.duty_u16(0)
    led_on_off_2.duty_u16(0)
    print("Simple LEDs fade test finished\n")


def test_adc():
    """ADC read test - 100k/200k divider, expected 5V"""
    print("=== ADC TEST (GPIO27) ===")
    print("Voltage divider 100k/200k")
    print("Expected input voltage: ~5V")
    print()

    measurements = []
    for i in range(5):
        voltage_input, voltage_adc, adc_raw = read_voltage()
        print(
            f"Measurement {i+1}: ADC={adc_raw:5d}, Vadc={voltage_adc:.3f}V, Vin={voltage_input:.3f}V"
        )
        measurements.append(voltage_input)
        utime.sleep(0.5)

    avg_voltage = sum(measurements) / len(measurements)
    print(f"\nAverage input voltage: {avg_voltage:.3f}V")

    if 4.5 <= avg_voltage <= 5.5:
        print("✓ Voltage in range (4.5V - 5.5V)")
    else:
        print("⚠ Voltage out of range")

    print("ADC test finished\n")


def test_relay1():
    """Relay 1 activation test"""
    print("=== RELAY 1 TEST (GPIO14) ===")
    print("Expected activation of relay 1")
    print()
    relay1.value(1)
    utime.sleep(2)
    relay1.value(0)
    utime.sleep(2)


def test_relay2():
    """Relay 2 activation test"""
    print("=== RELAY 2 TEST (GPIO15) ===")
    print("Expected activation of relay 2")
    print()
    relay2.value(1)
    utime.sleep(2)
    relay2.value(0)
    utime.sleep(2)


def test_rtc():
    """RTC test"""
    print("=== RTC PCF8563 TEST ===")
    print("• GPIO11: RTC power switch")
    print("• GPIO26 (ADC2): Battery voltage measurement")
    print("• GPIO12: RTC interrupt")
    print("• GPIO13: 1 Hz clock output")
    print("• I2C1: SDA=GPIO6, SCL=GPIO7")
    print()

    try:
        print("Powering RTC module...")
        rtc_on.value(1)
        utime.sleep(0.1)

        i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)
        clock = RTC_PCF8563(i2c)
        if hasattr(clock, "is_present") and not clock.is_present():
            print("⚠ RTC not present (register probe failed)")
            return

        print("I2C communication test with PCF8563...")
        devices = i2c.scan()
        if 0x51 in devices:
            print("✓ PCF8563 found at 0x51")
        else:
            print("⚠ PCF8563 not responding!")
            print(f"Found I2C devices: {[hex(addr) for addr in devices]}")

        print("Setting current time...")
        current_time = (2025, 1, 15, 3, 14, 30, 0)
        clock.set_time(current_time)

        print("Reading set time...")
        read_time = clock.read_time()
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            read_time[0],
            read_time[1],
            read_time[2],
            read_time[3],
            read_time[4],
            read_time[5],
        )
        print(f"RTC time: {formatted_time}")

        print("Measuring battery voltage...")
        batt_raw = adc_rtc.read_u16()
        conversion_factor = 3.3 / 65535
        gain = (100000 + 100000) / 100000
        batt_v = batt_raw * conversion_factor * gain
        print(f"Battery ADC: {batt_raw}, Voltage: {batt_v:.3f}V")

        if batt_v > 2.5:
            print("✓ Battery voltage OK")
        else:
            print("⚠ Battery voltage low")

        print("RTC signals test (5 seconds)...")
        for i in range(25):
            int_state = rtc_int.value()
            clk_state = rtc_clk.value()
            print(f"INT: {int_state}, CLK: {clk_state}", end="\r")
            utime.sleep_ms(200)
        print()

        print("✓ RTC test finished")

    except Exception as e:
        print(f"⚠ RTC test error: {e}")
    finally:
        rtc_on.value(0)
        print("RTC power off")
    print()


def test_eeprom():
    """EEPROM test"""
    print("=== EEPROM M24C32 TEST ===")
    print("• GPIO11: EEPROM power switch")
    print("• I2C1: SDA=GPIO6, SCL=GPIO7")
    print()

    try:
        print("Powering EEPROM module...")
        eeprom_on.value(1)
        utime.sleep(0.1)

        i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)

        print("I2C communication test with M24C32...")
        devices = i2c.scan()
        if 0x50 in devices:
            print("✓ M24C32 found at 0x50")
        else:
            print("⚠ M24C32 not responding!")
            print(f"Found I2C devices: {[hex(addr) for addr in devices]}")
            return
        eeprom = EEPROM_M24C32(i2c)
        if hasattr(eeprom, "is_ready") and not eeprom.is_ready():
            print("⚠ EEPROM not ready (ACK polling failed)")
            return

        test_value = 0x5A
        print(f"Byte write/read test: write {test_value:#04x} to address 0x0010")
        eeprom.write_byte(0x0010, test_value)

        read_value = eeprom.read_byte(0x0010)
        print(f"Read value {read_value:#04x} from address 0x0010")

        if read_value == test_value:
            print("✓ Byte write/read test passed")
        else:
            print("⚠ Byte write/read failed")
            return

        block_value = b"\x01\x02\x03\x04\x05"
        print(f"Block write/read test: write {block_value} to address 0x0020")

        eeprom.write_block(0x0020, block_value)
        read_block = eeprom.read_block(0x0020, len(block_value))
        print(f"Read block {read_block} from address 0x0020")

        if read_block == block_value:
            print("✓ Block write/read test passed")
        else:
            print("⚠ Block write/read failed")
            return

        string_value = "Check EEPROM!"
        print(f"String write/read test: write '{string_value}' to address 0x0030")

        eeprom.write_string(0x0030, string_value)
        read_string = eeprom.read_string(0x0030, len(string_value))
        print(f"Read string '{read_string}' from address 0x0030")

        if read_string == string_value:
            print("✓ String write/read test passed")
        else:
            print("⚠ String write/read failed")
            return
    except Exception as e:
        print(f"⚠ EEPROM test error: {e}")
    finally:
        eeprom_on.value(0)
        print("EEPROM power off")
    print()


expander_irq = None
irq_events = 0
_last_irq_ms = 0


def gpio_irq_handler(pin):
    global expander_irq, irq_events, _last_irq_ms

    if expander_irq is None:
        return

    now = utime.ticks_ms()
    if utime.ticks_diff(now, _last_irq_ms) < 120:
        return
    _last_irq_ms = now

    intf, intcap = expander_irq.get_interrupt_source_B()

    if intf & (1 << 1):
        irq_events += 1
        btn_val = (intcap >> 1) & 1
        print("→ IRQ (debounced): click #", irq_events, "btn_val =", btn_val)


def test_gpio():
    """GPIO expander test"""
    print("=== MCP23017 GPIO EXPANDER TEST ===")
    print("• GPIO11: Expander power switch")
    print("• GPIO12: Expander interrupt A")
    print("• GPIO13: Expander interrupt B")
    print("• I2C1: SDA=GPIO6, SCL=GPIO7")
    print()

    try:
        print("Powering GPIO Expander...")
        gpio_on.value(1)
        utime.sleep(0.1)

        i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)

        print("I2C communication test with MCP23017...")
        devices = i2c.scan()
        if 0x20 in devices:
            print("✓ MCP23017 found at 0x20")
        else:
            print("⚠ MCP23017 not responding!")
            print(f"Found I2C devices: {[hex(addr) for addr in devices]}")

        expander_gpio = EXPANDER_MCP23017(i2c)
        if hasattr(expander_gpio, "is_present") and not expander_gpio.is_present():
            print("⚠ MCP23017 not present (register probe failed)")
            return

        LED_PIN = 8
        BTN_PIN = 9

        expander_gpio.pin_mode(LED_PIN, EXPANDER_MCP23017.OUT)
        expander_gpio.pin_mode(BTN_PIN, EXPANDER_MCP23017.IN)
        expander_gpio.set_pullup(BTN_PIN, True)
        expander_gpio.digital_write(LED_PIN, 0)

        print("Blink LED on expander pin 8 (3 times)...")
        for _ in range(3):
            expander_gpio.digital_write(LED_PIN, 1)
            utime.sleep(0.5)
            expander_gpio.digital_write(LED_PIN, 0)
            utime.sleep(0.5)

        print("Manual button test (2 presses)...")
        for i in range(2):
            while expander_gpio.digital_read(BTN_PIN) == 1:
                utime.sleep_ms(20)
            print(f"✓ Button press ({i+1}/2)")
            while expander_gpio.digital_read(BTN_PIN) == 0:
                utime.sleep_ms(20)
        utime.sleep(0.2)
        print("✓ Manual button test finished")

        print("Interrupt test via INTB (10 seconds)...")

        expander_gpio.setup_interrupt_on_change_B(pin_bit=1)
        global expander_irq, irq_events
        expander_irq = expander_gpio
        irq_events = 0
        gpio_intb.irq(trigger=Pin.IRQ_FALLING, handler=gpio_irq_handler)
        start = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), start) < 10000:
            utime.sleep_ms(100)
        print(f"✓ Received {irq_events} interrupts from INTB")

        print("✓ GPIO Expander test successful")

    except Exception as e:
        print(f"⚠ GPIO Expander test error: {e}")
    finally:
        gpio_on.value(0)
        print("GPIO Expander power off")
    print()


ina226 = None
alert_count = 0


def ina_alert_irq(pin):
    global ina226, alert_count
    if ina226 is None:
        return

    alert_count += 1
    try:
        ina226.clear_alert()
    except Exception as e:
        pass
    print("→ ALERT from INA226! Count:", alert_count)


def test_ina():
    global ina226, alert_count
    """INA226 test"""
    print("=== INA226 POWER MONITOR TEST ===")
    print("• GPIO11: Power monitor power switch")
    print("• GPIO13: Power monitor alert")
    print("• I2C1: SDA=GPIO6, SCL=GPIO7")
    print("• GPIO0: PWM for bulb")
    print()

    try:
        print("Powering power monitor...")
        ina_on.value(1)
        utime.sleep(0.1)

        bulb_pwm = PWM(Pin(0))
        bulb_pwm.freq(1000)
        i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)

        print("I2C communication test with INA226...")
        devices = i2c.scan()
        if 0x40 in devices:
            print("✓ INA226 found at 0x40")
        else:
            print("⚠ INA226 not responding!")
            print(f"Found I2C devices: {[hex(addr) for addr in devices]}")

        ina226 = MEASUREMENT_INA226(i2c, r_shunt_ohm=0.01, max_current=3.2)
        if hasattr(ina226, "is_present") and not ina226.is_present():
            print("⚠ INA226 not present (register probe failed)")
            return
        v = ina226.bus_voltage_V()
        i = ina226.current_A()
        p = ina226.power_W()
        print("Bus voltage:  {:.3f} V".format(v))
        print("Current:      {:.3f} A".format(i))
        print("Power:        {:.3f} W".format(p))

        limit_A = 1.5
        print(f"Setting ALERT for current > {limit_A:.3f} A")
        ina226.set_overcurrent_alert(limit_A)

        ina_alert.irq(trigger=Pin.IRQ_FALLING, handler=ina_alert_irq)

        alert_count = 0

        def set_duty(percent):
            bulb_pwm.duty_u16(int(65535 * percent / 100))

        def measure(duty):
            v = ina226.bus_voltage_V()
            i = ina226.current_A()
            p = ina226.power_W()
            print("___________________________________")
            print("Duty cycle: {:d}".format(duty))
            print("Bus voltage:  {:.3f} V".format(v))
            print("Current:      {:.3f} A".format(i))
            print("Power:        {:.3f} W".format(p))
            print("___________________________________")

        set_duty(100)
        time.sleep(3)
        measure(100)
        time.sleep(1)

        set_duty(75)
        time.sleep(3)
        measure(75)
        time.sleep(1)

        set_duty(50)
        time.sleep(3)
        measure(50)
        time.sleep(1)

        set_duty(25)
        time.sleep(3)
        measure(25)
        time.sleep(1)

        set_duty(0)
        time.sleep(3)
        measure(0)
        time.sleep(1)
    except Exception as e:
        print(f"⚠ INA226 test error: {e}")
    finally:
        ina_on.value(0)
        print("Power monitor off")
    print()


def test_can():
    """Test CAN module"""
    print("=== CAN TEST ===")
    print("• GPIO21: CAN power switch")
    print("• GPIO20: CAN alert")
    print("• SPI: MOSI=GPIO19, MISO=GPIO16, SCK=GPIO18, CS=GPIO17")
    print()

    try:
        print("Powering CAN module...")
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
        print("Initializing CAN module via SPI...")
        can = CAN_MCP2515(spi, cs_pin)
        if not can.set_mode(0x40):
            print("⚠ Failed to enter LOOPBACK mode")
            return

        test_id = 0x123
        test_data = b"Hello"

        print(
            "Sending frame ID=0x{:03X}, data={}".format(
                test_id, [hex(b) for b in test_data]
            )
        )
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
            print("⚠ LOOPBACK: no frame received — this module may have RX issue")
        else:
            rid, rdata = received
            print("✓ LOOPBACK OK on this module:")
            print("  ID   = 0x{:03X}".format(rid))
            print("  data =", [hex(b) for b in rdata])
            print("  text =", rdata.decode("ascii"))

    except Exception as e:
        print(f"⚠ CAN test error: {e}")
    finally:
        can_on.value(0)
        print("CAN power off")
    print()


def button_monitor():
    """Buttons monitor"""
    global test_running

    last_button1_state = True
    last_button2_state = True

    while test_running:
        button1_state = button1.value()
        if last_button1_state and not button1_state:
            print(">>> BUTTON 1 (GPIO21) PRESSED! <<<")
        last_button1_state = button1_state
        button2_state = button2.value()
        if last_button2_state and not button2_state:
            print(">>> BUTTON 2 (GPIO22) PRESSED! <<<")
        last_button2_state = button2_state

        utime.sleep_ms(50)


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print(" RASPBERRY PI PICO - BASIC FUNCTIONAL TEST")
    print("=" * 50)

    if relay != 1:
        test_buzzer()
    test_rgb_led()
    test_rgb_fade()
    test_simple_leds()
    test_simple_leds_fade()
    test_adc()
    if relay == 1:
        test_relay1()
        test_relay2()
    if rtc == 1:
        test_rtc()
    if eeprom == 1:
        test_eeprom()
    if gpio == 1:
        test_gpio()
    if ina_state == 1:
        test_ina()
    if can_module == 1:
        test_can()
    print("=" * 40)
    print(" ALL TESTS FINISHED")
    print("=" * 40)


def interactive_mode():
    """Interactive mode - simplified"""
    global test_running

    print("\n" + "=" * 50)
    print(" TEST MODE - SIMPLE")
    print("=" * 50)
    print("Available options:")
    if relay != 1:
        print("1 - Buzzer test + scale")
    print("2 - RGB LED test")
    print("3 - RGB fade test")
    print("4 - LEDs GPIO2/3 test")
    print("5 - LEDs GPIO2/3 fade test")
    print("6 - ADC test")
    print("7 - Run all tests")
    if relay == 1:
        print("8 - Relay 1 test")
        print("9 - Relay 2 test")
    if rtc == 1:
        print("10 - RTC test")
    if eeprom == 1:
        print("11 - EEPROM test")
    if gpio == 1:
        print("12 - GPIO Expander test")
    if ina_state == 1:
        print("13 - INA226 test")
    if can_module == 1:
        print("14 - CAN test")
    print("q - Quit")
    if can_module != 1:
        print("\nButtons GPIO21/22 monitored in background")
    print("=" * 50)
    if can_module != 1:
        _thread.start_new_thread(button_monitor, ())

    while True:
        try:
            command = input("\nChoose option (1-7) or 'q': ").strip()

            if command == "q":
                test_running = False
                print("Exiting...")
                break
            elif command == "1" and relay != 1:
                test_buzzer()
            elif command == "2":
                test_rgb_led()
            elif command == "3":
                test_rgb_fade()
            elif command == "4":
                test_simple_leds()
            elif command == "5":
                test_simple_leds_fade()
            elif command == "6":
                test_adc()
            elif command == "7":
                run_all_tests()
            elif command == "8" and relay == 1:
                test_relay1()
            elif command == "9" and relay == 1:
                test_relay2()
            elif command == "10" and rtc == 1:
                test_rtc()
            elif command == "11" and eeprom == 1:
                test_eeprom()
            elif command == "12" and gpio == 1:
                test_gpio()
            elif command == "13" and ina_state == 1:
                test_ina()
            elif command == "14" and can_module == 1:
                test_can()
            else:
                print("Invalid option!")

        except KeyboardInterrupt:
            test_running = False
            print("\nInterrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function - simplified"""
    print("Raspberry Pi Pico - Prototype board test")
    print("Configuration:")
    if relay != 1:
        print("• GPIO15: Buzzer PWM")
    print("• GPIO8: Blue LED, GPIO9: Red LED, GPIO10: Green LED")
    print("• GPIO2, GPIO3: ON/OFF LEDs with PWM")
    print("• GPIO27 (ADC1): 5V measurement (100k/200k divider)")
    print("• GPIO21, GPIO22: Buttons")
    if relay == 1:
        print("• GPIO14: Relay 1")
        print("• GPIO15: Relay 2")

    try:
        led_red.duty_u16(0)
        led_green.duty_u16(0)
        led_blue.duty_u16(0)
        led_on_off_1.duty_u16(0)
        led_on_off_2.duty_u16(0)
        if relay != 1:
            buzzer.duty_u16(0)
        if relay == 1:
            relay1.value(0)
            relay2.value(0)
        if rtc == 1:
            rtc_on.value(0)
        if eeprom == 1:
            eeprom_on.value(0)
        if gpio == 1:
            gpio_on.value(0)
        if ina_state == 1:
            ina_on.value(0)
        if can_module == 1:
            can_on.value(0)
        interactive_mode()

    except Exception as e:
        print(f"Main error: {e}")
    finally:
        test_running = False
        led_red.duty_u16(0)
        led_green.duty_u16(0)
        led_blue.duty_u16(0)
        led_on_off_1.duty_u16(0)
        led_on_off_2.duty_u16(0)
        if relay != 1:
            buzzer.duty_u16(0)
        if relay == 1:
            relay1.value(0)
            relay2.value(0)
        if rtc == 1:
            rtc_on.value(0)
        if eeprom == 1:
            eeprom_on.value(0)
        if gpio == 1:
            gpio_on.value(0)
        if ina_state == 1:
            ina_on.value(0)
        if can_module == 1:
            can_on.value(0)
        print("Program finished — all pins turned off")


if __name__ == "__main__":
    main()
