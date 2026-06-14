import time

PCF8563_I2C_ADDR = 0x51
REG_CTRL1 = 0x00
REG_CTRL2 = 0x01
REG_SECONDS = 0x02
REG_MINUTES = 0x03
REG_HOURS = 0x04
REG_DAY = 0x05
REG_WEEKDAY = 0x06
REG_MONTH = 0x07
REG_YEAR = 0x08
REG_ALRM_MIN = 0x09
REG_ALRM_HOUR = 0x0A
REG_ALRM_DAY = 0x0B
REG_ALRM_WDAY = 0x0C
REG_CLKOUT = 0x0D


class RTC_PCF8563:
    def __init__(self, i2c):
        if i2c is None:
            raise ValueError("No I2C argument!")
        self.__i2c = i2c
        try:
            self.__i2c.writeto_mem(PCF8563_I2C_ADDR, REG_CTRL1, bytes([0x00]))
            self.__i2c.writeto_mem(PCF8563_I2C_ADDR, REG_CTRL2, bytes([0x00]))
            self.set_clockout_1hz(True)
        except Exception as e:
            print(f"RTC initialization error: {e}")
            raise

    def __bcd2dec(self, val):
        return ((val >> 4) * 10) + (val & 0x0F)

    def __dec2bcd(self, val):
        return ((val // 10) << 4) | (val % 10)

    def set_clockout_1hz(self, state):
        val = (0x80 | 0x03) if state else 0x00
        try:
            self.__i2c.writeto_mem(PCF8563_I2C_ADDR, REG_CLKOUT, bytes([val]))
        except Exception as e:
            print("Clock output setting error:", e)

    def set_time(self, datetime=None):
        try:
            if datetime is None:
                raise ValueError("No datetime argument!")
            if len(datetime) < 7:
                raise ValueError(
                    "Invalid datetime argument! Expected (year, month, day, weekday, hour, minute, second)"
                )

            year, month, day, weekday, hour, minute, second = datetime

            if year < 2000 or year > 2099:
                raise ValueError("Year out of range (2000-2099)")
            if month < 1 or month > 12:
                raise ValueError("Month out of range (1-12)")
            if day < 1 or day > 31:
                raise ValueError("Day out of range (1-31)")
            if weekday < 0 or weekday > 6:
                raise ValueError("Weekday out of range (0-6)")
            if hour < 0 or hour > 23:
                raise ValueError("Hour out of range (0-23)")
            if minute < 0 or minute > 59:
                raise ValueError("Minute out of range (0-59)")
            if second < 0 or second > 59:
                raise ValueError("Second out of range (0-59)")
            year_bcd = year - 2000
            data = bytearray(7)
            data[0] = self.__dec2bcd(second) & 0x7F
            data[1] = self.__dec2bcd(minute) & 0x7F
            data[2] = self.__dec2bcd(hour) & 0x3F
            data[3] = self.__dec2bcd(day) & 0x3F
            data[4] = weekday & 0x07
            data[5] = self.__dec2bcd(month) & 0x1F

            year2 = year
            if year2 >= 2000:
                year2 -= 2000
            else:
                data[5] |= 0x80
                year2 = (year2 >= 1900) if year2 - 1900 else 0
            data[6] = self.__dec2bcd(year2)
            self.__i2c.writeto_mem(PCF8563_I2C_ADDR, REG_SECONDS, data)
        except Exception as e:
            raise

    def read_time(self):
        try:
            raw = self.__i2c.readfrom_mem(PCF8563_I2C_ADDR, REG_SECONDS, 7)
            second = self.__bcd2dec(raw[0] & 0x7F)
            minute = self.__bcd2dec(raw[1] & 0x7F)
            hour = self.__bcd2dec(raw[2] & 0x3F)
            day = self.__bcd2dec(raw[3] & 0x3F)
            weekday = self.__bcd2dec(raw[4] & 0x07)
            month = self.__bcd2dec(raw[5] & 0x1F)
            if raw[5] & 0x80:
                year = self.__bcd2dec(raw[6]) + 1900
            else:
                year = self.__bcd2dec(raw[6]) + 2000
            return (year, month, day, hour, minute, second)
        except Exception as e:
            print(f"Time reading error: {e}")
            return (2000, 1, 1, 0, 0, 0)

    def is_clock_valid(self):
        try:
            raw = self.__i2c.readfrom_mem(PCF8563_I2C_ADDR, REG_SECONDS, 1)
            return not bool(raw[0] & 0x80)
        except Exception as e:
            print(f"Clock validity check error: {e}")
            return False

    def get_formatted_time(self):
        try:
            t = self.read_time()
            if len(t) < 6:
                return "Invalid time"
            year, month, day, hour, minute, second = t[:6]
            return (
                f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            )
        except Exception as e:
            print(f"Time formatting error: {e}")
            return "Invalid time"

    def is_present(self) -> bool:
        try:
            _ = self.__i2c.readfrom_mem(PCF8563_I2C_ADDR, REG_CTRL1, 1)
            return True
        except Exception:
            return False
