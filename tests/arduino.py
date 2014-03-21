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
		to = cereal.timeout
		cereal.setTimeout(1)
		cereal.readall()
		cereal.setTimeout(to)
		cereal.flushInput()
		cereal.flushOutput()
		cereal.flush()

	def expect_string(self, string):
		read = cereal.read(len(string))
		self.failIf(read != string, "Expect string not found \n\nfound\n%s\n\nlooking for\n%s" % (read, string))

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
		
		ret = call(["./arduino", "--verify", "--board", "cozybit:mc200:MC200", "--pref", "build.path=" + tmp_path, build_path])
		self.failIf(ret, "There was a problem while building %s a return value of %d was given" %
				(build_path, ret))

		return tmp_path + "/" + os.path.basename(build_path)[:-3] + "cpp.axf"


	def flash(self, flash_path):
		try:
			ret = call([IDE + "/hardware/cozybit/mc200/system/wmsdk/tools/mc200/OpenOCD/cozyinstall.sh", flash_path])
		except OSError:
			self.failIf(1, "Problem when trying to cozyinstall %s" % flash_path)

		self.failIf(ret, "Something went wrong with flashing %s a return value of %d was given" %
				(flash_path, ret))

	def test_1_string_addition_operators(self):
		to_build = "./examples/08.Strings/StringAdditionOperator/StringAdditionOperator.ino"
		expected_string = "\n\nAdding strings together (concatenation):\n\r\n\rstringThree = 123\n\rstringThree = 123456789\n\rstringThree = A\n\rstringThree = abc\n\rstringThree = this string\n\r"
		self.flash(self.build(to_build))

		# the last two lines printed are not checked since they are non
		# deterministic, one is the sensor value, the other is milliseconds
		# since the program started
		self.expect_string(expected_string)
	
	def test_2_string_replace(self):
		to_build = "./examples/08.Strings/StringReplace/StringReplace.ino"
		expected_string = "\n\nString  replace:\n\n\r\n\r<html><head><body>\n\rOriginal string: <html><head><body>\n\rModified string: </html></head></body>\n\rnormal: bookkeeper\n\rl33tspeak: b00kk33p3r\n\r"

		self.flash(self.build(to_build))
		self.expect_string(expected_string)

