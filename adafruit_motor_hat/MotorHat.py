# -*- coding: utf-8 -*-
from __future__ import division

import time

from Adafruit_PWM_Servo_Driver import PWM


# This code is from https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library
# It is licensed under MIT, please see the licence docs


class AdafruitStepperMotor(object):
	MICROSTEPS = 8
	MICROSTEP_CURVE = [0, 50, 98, 142, 180, 212, 236, 250, 255]

	# MICROSTEPS = 16
	# a sinusoidal curve NOT LINEAR!
	# MICROSTEP_CURVE = [0, 25, 50, 74, 98, 120, 141, 162, 180, 197, 212, 225, 236, 244, 250, 253, 255]

	def __init__(self, controller, num, steps=200):
		"""
		Initialize the Stepper Motor object

		:param controller:
		:param num:
		:param steps:
			the number of steps corresponding to a full rotation of the stepper
		"""
		self.pwm_a = 255
		self.pwm_b = 255
		self.MC = controller
		self.revsteps = steps
		self.motornum = num
		self.sec_per_step = 0.1
		self.stepping_counter = 0
		self.currentstep = 0

		num -= 1

		if num == 0:
			self.PWMA = 8
			self.AIN2 = 9
			self.AIN1 = 10
			self.PWMB = 13
			self.BIN2 = 12
			self.BIN1 = 11
		elif num == 1:
			self.PWMA = 2
			self.AIN2 = 3
			self.AIN1 = 4
			self.PWMB = 7
			self.BIN2 = 6
			self.BIN1 = 5
		else:
			raise ValueError('MotorHAT Stepper must be between 1 and 2 inclusive')

	def setSpeed(self, rpm):
		"""
		Set the target motor speed in rpm, motor step count is used to calculate the step delay
		:param rpm:
			Target RPM
		:type rpm:
			float
		:return:
			None
		"""
		self.sec_per_step = 60.0 / (self.revsteps * rpm)
		self.stepping_counter = 0

	def _step(self, microstep=False):
		"""
		Internal step execution function
		:param microstep:
			Is this cleaning up for a microstep?
		:type microstep:
			Bool
		:return:
			The current step
		"""
		# go to next 'step' and wrap around
		self.currentstep += self.MICROSTEPS * 4
		self.currentstep %= self.MICROSTEPS * 4

		# only really used for microstepping, otherwise always on!
		self.MC._pwm.setPWM(self.PWMA, 0, self.pwm_a * 16)
		self.MC._pwm.setPWM(self.PWMB, 0, self.pwm_b * 16)

		# set up coil energizing!
		coils = [0, 0, 0, 0]

		if microstep:
			if (self.currentstep >= 0) and (self.currentstep < self.MICROSTEPS):
				coils = [1, 1, 0, 0]
			elif (self.currentstep >= self.MICROSTEPS) and (self.currentstep < self.MICROSTEPS * 2):
				coils = [0, 1, 1, 0]
			elif (self.currentstep >= self.MICROSTEPS * 2) and (self.currentstep < self.MICROSTEPS * 3):
				coils = [0, 0, 1, 1]
			elif (self.currentstep >= self.MICROSTEPS * 3) and (self.currentstep < self.MICROSTEPS * 4):
				coils = [1, 0, 0, 1]
		else:
			step2coils = [
				[1, 0, 0, 0],
				[1, 1, 0, 0],
				[0, 1, 0, 0],
				[0, 1, 1, 0],
				[0, 0, 1, 0],
				[0, 0, 1, 1],
				[0, 0, 0, 1],
				[1, 0, 0, 1]
			]
			coils = step2coils[self.currentstep // (self.MICROSTEPS // 2)]

		self.MC.set_pin(self.AIN2, coils[0])
		self.MC.set_pin(self.BIN1, coils[1])
		self.MC.set_pin(self.AIN1, coils[2])
		self.MC.set_pin(self.BIN2, coils[3])

		return self.currentstep

	def step(self, steps=1, reverse=False):
		"""
		Simple single step
		:param steps:
			The number of steps to execute
		:type steps:
			int
		:param reverse:
			step in reverse
		:type reverse:
			Bool
		:return:
			None
		"""
		s_per_s = self.sec_per_step
		self.pwm_a = 255
		self.pwm_b = 255

		for _ in range(steps):
			if (self.currentstep // (self.MICROSTEPS // 2)) % 2:
				# we're at an odd step, weird
				if reverse:
					self.currentstep -= self.MICROSTEPS // 2
				else:
					self.currentstep += self.MICROSTEPS // 2
			else:
				# go to next even step
				if reverse:
					self.currentstep -= self.MICROSTEPS
				else:
					self.currentstep += self.MICROSTEPS
			self._step()
			time.sleep(s_per_s)

	def double_step(self, steps=1, reverse=False):
		"""
		Double stepping, 2 coils at once
		:param steps:
			The number of steps to execute
		:type steps:
			int
		:param reverse:
			step in reverse
		:type reverse:
			Bool
		:return:
			None
		"""
		s_per_s = self.sec_per_step
		self.pwm_a = 255
		self.pwm_b = 255

		for _ in range(steps):
			if not (self.currentstep // (self.MICROSTEPS // 2) % 2):
				# we're at an even step, weird
				if reverse:
					self.currentstep -= self.MICROSTEPS // 2
				else:
					self.currentstep += self.MICROSTEPS // 2
			else:
				# go to next odd step
				if reverse:
					self.currentstep -= self.MICROSTEPS
				else:
					self.currentstep += self.MICROSTEPS
			self._step()
			time.sleep(s_per_s)

	def interleaved_step(self, steps=1, reverse=False):
		"""
		Interleaved stepping, single stepping and interleaved stepping
		:param steps:
			The number of steps to execute
		:type steps:
			int
		:param reverse:
			step in reverse
		:type reverse:
			Bool
		:return:
			None
		"""
		s_per_s = self.sec_per_step / 2.0
		self.pwm_a = 255
		self.pwm_b = 255

		for _ in range(steps):
			if reverse:
				self.currentstep -= self.MICROSTEPS // 2
			else:
				self.currentstep += self.MICROSTEPS // 2
			self._step()
			time.sleep(s_per_s)

	def micro_step(self, steps=1, reverse=False):
		"""
		Microstepping
		:param steps:
			The number of steps to execute
		:type steps:
			int
		:param reverse:
			step in reverse
		:type reverse:
			Bool
		:return:
			None
		"""
		s_per_s = self.sec_per_step / self.MICROSTEPS
		steps *= self.MICROSTEPS
		for i in range(steps):
			if reverse:
				self.currentstep -= 1
				# go to next 'step' and wrap around
				self.currentstep += self.MICROSTEPS * 4
				self.currentstep %= self.MICROSTEPS * 4
			else:
				self.currentstep += 1

			self.pwm_a = 0
			self.pwm_b = 0
			if (self.currentstep >= 0) and (self.currentstep < self.MICROSTEPS):
				self.pwm_a = self.MICROSTEP_CURVE[self.MICROSTEPS - self.currentstep]
				self.pwm_b = self.MICROSTEP_CURVE[self.currentstep]
			elif (self.currentstep >= self.MICROSTEPS) and (self.currentstep < self.MICROSTEPS * 2):
				self.pwm_a = self.MICROSTEP_CURVE[self.currentstep - self.MICROSTEPS]
				self.pwm_b = self.MICROSTEP_CURVE[self.MICROSTEPS * 2 - self.currentstep]
			elif (self.currentstep >= self.MICROSTEPS * 2) and (self.currentstep < self.MICROSTEPS * 3):
				self.pwm_a = self.MICROSTEP_CURVE[self.MICROSTEPS * 3 - self.currentstep]
				self.pwm_b = self.MICROSTEP_CURVE[self.currentstep - self.MICROSTEPS * 2]
			elif (self.currentstep >= self.MICROSTEPS * 3) and (self.currentstep < self.MICROSTEPS * 4):
				self.pwm_a = self.MICROSTEP_CURVE[self.currentstep - self.MICROSTEPS * 3]
				self.pwm_b = self.MICROSTEP_CURVE[self.MICROSTEPS * 4 - self.currentstep]
			self._step(microstep=True)
			time.sleep(s_per_s)

	def align_step(self, reverse=False):
		while (self.currentstep != 0) and (self.currentstep != self.MICROSTEPS):
			self.micro_step(reverse=reverse)


class AdafruitDCMotor(object):
	def __init__(self, controller, num):
		self.MC = controller
		self.motornum = num - 1

		if self.motornum == 0:
			pwm = 8
			in2 = 9
			in1 = 10
		elif self.motornum == 1:
			pwm = 13
			in2 = 12
			in1 = 11
		elif self.motornum == 2:
			pwm = 2
			in2 = 3
			in1 = 4
		elif self.motornum == 3:
			pwm = 7
			in2 = 6
			in1 = 5
		else:
			raise ValueError('MotorHAT Motor must be between 1 and 4 inclusive')
		self.PWMpin = pwm
		self.IN1pin = in1
		self.IN2pin = in2

	def run(self, command):
		if not self.MC:
			return
		if command == AdafruitMotorHAT.FORWARD:
			self.MC.set_pin(self.IN2pin, 0)
			self.MC.set_pin(self.IN1pin, 1)
		if command == AdafruitMotorHAT.BACKWARD:
			self.MC.set_pin(self.IN1pin, 0)
			self.MC.set_pin(self.IN2pin, 1)
		if command == AdafruitMotorHAT.RELEASE:
			self.MC.set_pin(self.IN1pin, 0)
			self.MC.set_pin(self.IN2pin, 0)

	def setSpeed(self, speed):
		if speed < 0:
			speed = 0
		if speed > 255:
			speed = 255
		self.MC._pwm.setPWM(self.PWMpin, 0, speed * 16)


class AdafruitMotorHAT(object):
	FORWARD = 1
	BACKWARD = 2
	RELEASE = 3

	def __init__(self, addr=0x60, freq=1600, i2c=None, i2c_bus=None):
		self._frequency = freq
		self.motors = [AdafruitDCMotor(self, m) for m in range(4)]
		self.steppers = [AdafruitStepperMotor(self, 1), AdafruitStepperMotor(self, 2)]
		self._pwm = PWM(addr, debug=False, i2c=i2c, i2c_bus=i2c_bus)
		self._pwm.setPWMFreq(self._frequency)

	def set_pin(self, pin, value):
		if pin not in range(16):
			raise ValueError('PWM pin must be between 0 and 15 inclusive')
		if value not in [0, 1]:
			raise ValueError('Pin value must be 0 or 1!')
		if value == 0:
			self._pwm.setPWM(pin, 0, 4096)
		if value == 1:
			self._pwm.setPWM(pin, 4096, 0)

	def get_stepper(self, num):
		if num not in [1, 2]:
			raise ValueError('MotorHAT Stepper must be between 1 and 2 inclusive')
		return self.steppers[num - 1]

	def get_motor(self, num):
		if num not in [1, 2, 3, 4]:
			raise ValueError('MotorHAT Motor must be between 1 and 4 inclusive')
		return self.motors[num - 1]
