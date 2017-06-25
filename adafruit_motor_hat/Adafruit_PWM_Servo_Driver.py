# -*- coding: utf-8 -*-
import logging
import math
import time

logger = logging.getLogger(__name__)


# This code is from https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library
# It is licensed under MIT, please see the licence docs

def get_i2c_device(address, i2c, i2c_bus):
	"""
	Helper method to get a device at the specified address from the I2C bus.
	If no i2c bus is specified (i2c param is None) then the default I2C bus
	for the platform will be used.

	:param address:
		i2c address to get the handle for
	:type address:
		hex
	:param i2c:
		GPIO i2c class, None to use the Adafruit_GPIO.I2C class
	:param i2c_bus:
		i2c bus number, passed to busnum, none to autodetect
	:return:
		i2c Address
	"""
	if i2c is not None:
		return i2c.get_i2c_device(address)
	else:
		import Adafruit_GPIO.I2C as I2C
		if i2c_bus is None:
			return I2C.get_i2c_device(address)
		else:
			return I2C.get_i2c_device(address, busnum=i2c_bus)


class PWM(object):
	"""
	Adafruit PCA9685 16-Channel PWM Servo Driver
	"""

	# Registers/etc.
	__MODE1 = 0x00
	__MODE2 = 0x01
	__SUBADR1 = 0x02
	__SUBADR2 = 0x03
	__SUBADR3 = 0x04
	__PRESCALE = 0xFE
	__LED0_ON_L = 0x06
	__LED0_ON_H = 0x07
	__LED0_OFF_L = 0x08
	__LED0_OFF_H = 0x09
	__ALL_LED_ON_L = 0xFA
	__ALL_LED_ON_H = 0xFB
	__ALL_LED_OFF_L = 0xFC
	__ALL_LED_OFF_H = 0xFD

	# Bits
	__RESTART = 0x80
	__SLEEP = 0x10
	__ALLCALL = 0x01
	__INVRT = 0x10
	__OUTDRV = 0x04

	@classmethod
	def softwareReset(cls, i2c=None, i2c_bus=None):
		"""Sends a software reset (SWRST) command to all the servo drivers on the bus
		"""
		general_call_i2c = get_i2c_device(0x00, i2c, i2c_bus)
		general_call_i2c.writeRaw8(0x06)  # SWRST

	def __init__(self, address=0x40, debug=False, i2c=None, i2c_bus=None):
		"""
		Initialize a new PWM object
		"""
		self.i2c = get_i2c_device(address, i2c, i2c_bus)
		logger.debug("Resetting PCA9685 MODE1 (without SLEEP) and MODE2")
		self.setAllPWM(0, 0)
		self.i2c.write8(self.__MODE2, self.__OUTDRV)
		self.i2c.write8(self.__MODE1, self.__ALLCALL)
		time.sleep(0.005)  # wait for oscillator
		mode1 = self.i2c.readU8(self.__MODE1)
		mode1 = mode1 & ~self.__SLEEP  # wake up (reset sleep)
		self.i2c.write8(self.__MODE1, mode1)
		time.sleep(0.005)  # wait for oscillator

	def setPWMFreq(self, freq):
		"""
		Set the PWM frequency in Hz

		:param freq:
			frequency in Hz
		:type freq:
			int
		:return:
			None
		"""
		prescaleval = 25000000.0  # 25MHz
		prescaleval /= 4096.0  # 12-bit
		prescaleval /= float(freq)
		prescaleval -= 1.0
		logger.debug("Setting PWM frequency to %d Hz" % freq)
		logger.debug("Estimated pre-scale: %d" % prescaleval)
		prescale = math.floor(prescaleval + 0.5)
		logger.debug("Final pre-scale: %d" % prescale)
		oldmode = self.i2c.readU8(self.__MODE1)
		newmode = (oldmode & 0x7F) | 0x10  # sleep
		self.i2c.write8(self.__MODE1, newmode)  # go to sleep
		self.i2c.write8(self.__PRESCALE, int(math.floor(prescale)))
		self.i2c.write8(self.__MODE1, oldmode)
		time.sleep(0.005)
		self.i2c.write8(self.__MODE1, oldmode | 0x80)

	def setPWM(self, channel, on, off):
		"""
		Set a single pwm channel

		:param channel:
			the channel number from 0-15 inclusive
		:param on:
			the portion of the PWM period in 1/4096ths of a
			period (0 corresponds to the start, 4096 corresponds to the end)
			to wait before the signal turns on
		:param off:
			the portion of the PWM period in 1/4096ths of a
			period (0 corresponds to the start, 4096 corresponds to the end)
			to wait before the signal turns off
		:return:
			None
		"""
		self.i2c.write8(self.__LED0_ON_L + 4 * channel, on & 0xFF)
		self.i2c.write8(self.__LED0_ON_H + 4 * channel, on >> 8)
		self.i2c.write8(self.__LED0_OFF_L + 4 * channel, off & 0xFF)
		self.i2c.write8(self.__LED0_OFF_H + 4 * channel, off >> 8)

	def setAllPWM(self, on, off):
		"""
		Sets all the pwm outputs to the corresponding outputs

		:param on:
			the portion of the PWM period in 1/4096ths of a
			period (0 corresponds to the start, 4096 corresponds to the end)
			to wait before the signal turns on
		:param off:
			the portion of the PWM period in 1/4096ths of a
			period (0 corresponds to the start, 4096 corresponds to the end)
			to wait before the signal turns off
		:return:
			None
		"""
		self.i2c.write8(self.__ALL_LED_ON_L, on & 0xFF)
		self.i2c.write8(self.__ALL_LED_ON_H, on >> 8)
		self.i2c.write8(self.__ALL_LED_OFF_L, off & 0xFF)
		self.i2c.write8(self.__ALL_LED_OFF_H, off >> 8)
