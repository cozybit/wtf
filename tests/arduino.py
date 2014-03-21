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
COZYINSTALL = IDE + "/hardware/cozybit/mc200/system/wmsdk/tools/mc200/OpenOCD/cozyinstall.sh"

def setUp(self):
	global cereal
	global display
	global old_display

	cereal = wtfconfig.comm.serial
	# set up a fake X server for a computer without one...
	old_display = display = os.environ["DISPLAY"]
	if display == '':
		display = ':' + str(randint(10, 99))
		call(["Xvfb", display])
	os.environ["DISPLAY"] = display

def tearDown(self):
	# if we had to change the display, set it back and kill fake x server
	if old_display != display:
		call(["pkill", "Xvfb"])
		os.environ["DISPLAY"] = old_display

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
		# debugg option? TODO: take out this ugly long message?
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
		
		ret = call(["./arduino", "--verify", "--board",
			"cozybit:mc200:MC200", "-v", "--pref",
			"build.path=" + tmp_path, build_path])
		self.failIf(ret, "There was a problem while building %s a return value of %d was given" %
				(build_path, ret))

		# break off the ino extension and add cpp.axf in it's place
		return tmp_path + "/" + os.path.basename(build_path)[:-3] + "cpp.axf"


	def flash(self, flash_path):
		try:
			ret = call([COZYINSTALL, flash_path])
		except OSError:
			self.failIf(1, "Problem when trying to cozyinstall %s" % flash_path)

		self.failIf(ret, "Something went wrong with flashing %s a return value of %d was given" %
				(flash_path, ret))

	def test_1_string_addition_operators(self):
		self.flash(self.build(test_strings[self._testMethodName][0]))
		self.expect_string(test_strings[self._testMethodName][1])
	
	def test_2_string_replace(self):
		self.flash(self.build(test_strings[self._testMethodName][0]))
		self.expect_string(test_strings[self._testMethodName][1])

	def test_3_ascii_table(self):
		self.flash(self.build(test_strings[self._testMethodName][0]))
		self.expect_string(test_strings[self._testMethodName][1])


test_strings = {}
test_strings["test_1_string_addition_operators"] = ["./examples/08.Strings/StringAdditionOperator/StringAdditionOperator.ino", "\n\nAdding strings together (concatenation):\n\r\n\rstringThree = 123\n\rstringThree = 123456789\n\rstringThree = A\n\rstringThree = abc\n\rstringThree = this string\n\r"]
test_strings["test_2_string_replace"] = ["./examples/08.Strings/StringReplace/StringReplace.ino", "\n\nString  replace:\n\n\r\n\r<html><head><body>\n\rOriginal string: <html><head><body>\n\rModified string: </html></head></body>\n\rnormal: bookkeeper\n\rl33tspeak: b00kk33p3r\n\r"]
test_strings["test_3_ascii_table"] = ["./examples/04.Communication/ASCIITable/ASCIITable.ino", """ASCII Table ~ Character Map\n\r!, dec: 33, hex: 21, oct: 41, bin: 100001\n\r", dec: 34, hex: 22, oct: 42, bin: 100010\n\r#, dec: 35, hex: 23, oct: 43, bin: 100011\n\r$, dec: 36, hex: 24, oct: 44, bin: 100100\n\r%, dec: 37, hex: 25, oct: 45, bin: 100101\n\r&, dec: 38, hex: 26, oct: 46, bin: 100110\n\r\', dec: 39, hex: 27, oct: 47, bin: 100111\n\r(, dec: 40, hex: 28, oct: 50, bin: 101000\n\r), dec: 41, hex: 29, oct: 51, bin: 101001\n\r*, dec: 42, hex: 2A, oct: 52, bin: 101010\n\r+, dec: 43, hex: 2B, oct: 53, bin: 101011\n\r,, dec: 44, hex: 2C, oct: 54, bin: 101100\n\r-, dec: 45, hex: 2D, oct: 55, bin: 101101\n\r., dec: 46, hex: 2E, oct: 56, bin: 101110\n\r/, dec: 47, hex: 2F, oct: 57, bin: 101111\n\r0, dec: 48, hex: 30, oct: 60, bin: 110000\n\r1, dec: 49, hex: 31, oct: 61, bin: 110001\n\r2, dec: 50, hex: 32, oct: 62, bin: 110010\n\r3, dec: 51, hex: 33, oct: 63, bin: 110011\n\r4, dec: 52, hex: 34, oct: 64, bin: 110100\n\r5, dec: 53, hex: 35, oct: 65, bin: 110101\n\r6, dec: 54, hex: 36, oct: 66, bin: 110110\n\r7, dec: 55, hex: 37, oct: 67, bin: 110111\n\r8, dec: 56, hex: 38, oct: 70, bin: 111000\n\r9, dec: 57, hex: 39, oct: 71, bin: 111001\n\r:, dec: 58, hex: 3A, oct: 72, bin: 111010\n\r;, dec: 59, hex: 3B, oct: 73, bin: 111011\n\r<, dec: 60, hex: 3C, oct: 74, bin: 111100\n\r=, dec: 61, hex: 3D, oct: 75, bin: 111101\n\r>, dec: 62, hex: 3E, oct: 76, bin: 111110\n\r?, dec: 63, hex: 3F, oct: 77, bin: 111111\n\r@, dec: 64, hex: 40, oct: 100, bin: 1000000\n\rA, dec: 65, hex: 41, oct: 101, bin: 1000001\n\rB, dec: 66, hex: 42, oct: 102, bin: 1000010\n\rC, dec: 67, hex: 43, oct: 103, bin: 1000011\n\rD, dec: 68, hex: 44, oct: 104, bin: 1000100\n\rE, dec: 69, hex: 45, oct: 105, bin: 1000101\n\rF, dec: 70, hex: 46, oct: 106, bin: 1000110\n\rG, dec: 71, hex: 47, oct: 107, bin: 1000111\n\rH, dec: 72, hex: 48, oct: 110, bin: 1001000\n\rI, dec: 73, hex: 49, oct: 111, bin: 1001001\n\rJ, dec: 74, hex: 4A, oct: 112, bin: 1001010\n\rK, dec: 75, hex: 4B, oct: 113, bin: 1001011\n\rL, dec: 76, hex: 4C, oct: 114, bin: 1001100\n\rM, dec: 77, hex: 4D, oct: 115, bin: 1001101\n\rN, dec: 78, hex: 4E, oct: 116, bin: 1001110\n\rO, dec: 79, hex: 4F, oct: 117, bin: 1001111\n\rP, dec: 80, hex: 50, oct: 120, bin: 1010000\n\rQ, dec: 81, hex: 51, oct: 121, bin: 1010001\n\rR, dec: 82, hex: 52, oct: 122, bin: 1010010\n\rS, dec: 83, hex: 53, oct: 123, bin: 1010011\n\rT, dec: 84, hex: 54, oct: 124, bin: 1010100\n\rU, dec: 85, hex: 55, oct: 125, bin: 1010101\n\rV, dec: 86, hex: 56, oct: 126, bin: 1010110\n\rW, dec: 87, hex: 57, oct: 127, bin: 1010111\n\rX, dec: 88, hex: 58, oct: 130, bin: 1011000\n\rY, dec: 89, hex: 59, oct: 131, bin: 1011001\n\rZ, dec: 90, hex: 5A, oct: 132, bin: 1011010\n\r[, dec: 91, hex: 5B, oct: 133, bin: 1011011\n\r\\, dec: 92, hex: 5C, oct: 134, bin: 1011100\n\r], dec: 93, hex: 5D, oct: 135, bin: 1011101\n\r^, dec: 94, hex: 5E, oct: 136, bin: 1011110\n\r_, dec: 95, hex: 5F, oct: 137, bin: 1011111\n\r`, dec: 96, hex: 60, oct: 140, bin: 1100000\n\ra, dec: 97, hex: 61, oct: 141, bin: 1100001\n\rb, dec: 98, hex: 62, oct: 142, bin: 1100010\n\rc, dec: 99, hex: 63, oct: 143, bin: 1100011\n\rd, dec: 100, hex: 64, oct: 144, bin: 1100100\n\re, dec: 101, hex: 65, oct: 145, bin: 1100101\n\rf, dec: 102, hex: 66, oct: 146, bin: 1100110\n\rg, dec: 103, hex: 67, oct: 147, bin: 1100111\n\rh, dec: 104, hex: 68, oct: 150, bin: 1101000\n\ri, dec: 105, hex: 69, oct: 151, bin: 1101001\n\rj, dec: 106, hex: 6A, oct: 152, bin: 1101010\n\rk, dec: 107, hex: 6B, oct: 153, bin: 1101011\n\rl, dec: 108, hex: 6C, oct: 154, bin: 1101100\n\rm, dec: 109, hex: 6D, oct: 155, bin: 1101101\n\rn, dec: 110, hex: 6E, oct: 156, bin: 1101110\n\ro, dec: 111, hex: 6F, oct: 157, bin: 1101111\n\rp, dec: 112, hex: 70, oct: 160, bin: 1110000\n\rq, dec: 113, hex: 71, oct: 161, bin: 1110001\n\rr, dec: 114, hex: 72, oct: 162, bin: 1110010\n\rs, dec: 115, hex: 73, oct: 163, bin: 1110011\n\rt, dec: 116, hex: 74, oct: 164, bin: 1110100\n\ru, dec: 117, hex: 75, oct: 165, bin: 1110101\n\rv, dec: 118, hex: 76, oct: 166, bin: 1110110\n\rw, dec: 119, hex: 77, oct: 167, bin: 1110111\n\rx, dec: 120, hex: 78, oct: 170, bin: 1111000\n\ry, dec: 121, hex: 79, oct: 171, bin: 1111001\n\rz, dec: 122, hex: 7A, oct: 172, bin: 1111010\n\r{, dec: 123, hex: 7B, oct: 173, bin: 1111011\n\r|, dec: 124, hex: 7C, oct: 174, bin: 1111100\n\r}, dec: 125, hex: 7D, oct: 175, bin: 1111101\n\r~, dec: 126, hex: 7E, oct: 176, bin: 1111110\n\r"""]
