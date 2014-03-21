# Copyright cozybit, Inc 2010-2011
# All rights reserved

"""
Build and run/expect arduino apps
"""

import wtf.node.mesh as mesh
from wtf.util import *
import unittest
import wtf
import sys
import os

from shutil import rmtree
from subprocess import call
import threading
from random import randint

err = sys.stderr
wtfconfig = wtf.conf
sta = wtfconfig.mps

ref_clip = os.getenv("REF_CLIP")

# hmmm, hardcoded arduino ide path??
# TODO: FIXXX me
IDE = "/home/jacob/dev/arduino_project/MeshableMCU/arduino-1.5.6-r2"

def setUp(self):
	global cereal

	cereal = wtfconfig.comm.serial

class ArduinoTest(unittest.TestCase):
	""" Arduino test suite, builds, flashes, and expects. """
	def setUp(self):
		""" flush before every test to clear serial buffer """
		cereal.flushInput()
		cereal.flushOutput()

	def expect_string(self, string, test):
		read = cereal.read(len(string))
		self.failIf(read != string, "Expect string not found for test %s" % test)
		print "test %s passed" % test

	def build(self, build_path):
		# random build directory
		tmp_path = "/tmp/arduino_build" + str(randint(1, 1000))
		# remove if random dir already exists...
		if os.path.isdir(tmp_path):
			rmtree(tmp_path)
		os.mkdir(tmp_path)

		try:
			os.chdir(IDE)
		except OSError:
			self.failIf(1, "You do not have the correct arduino ide directory path set")
		
		ret = call(["sudo", "./arduino", "--verify", "--board", "cozybit:mc200:MC200", "--pref", "build.path=" + tmp_path, "-v", build_path])
		self.failIf(ret, "There was a problem while building %s a return value of %d was given" %
				(build_path, ret))

		return tmp_path


	def flash(self, flash_path):
		try:
			ret = call([IDE + "/hardware/cozybit/mc200/system/wmsdk/tools/mc200/OpenOCD/cozyinstall.sh", flash_path])
		except OSError:
			self.failIf(1, "Problem when trying to cozyinstall %s" % flash_path)

		self.failIf(ret, "Something went wrong with flashing %s a return value of %d was given" %
				(flash_path, ret))

	def test_string_addition_operators(self):
		to_build = "./examples/08.Strings/StringAdditionOperator/StringAdditionOperator.ino"
		flash_path = self.build(to_build)
		self.flash(flash_path)
		# the last two lines printed are not checked since they are non
		# deterministic, one is the sensor value, the other is milliseconds
		# since the program started
		expect_string("\n\nAdding strings together (concatenation):\n\r\n\rstringThree = 123\n\rstringThree = 123456789\n\rstringThree = A\n\rstringThree = abc\n\rstringThree = this string\n\r",
				"string_addition_operators")
