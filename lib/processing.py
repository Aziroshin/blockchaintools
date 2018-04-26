#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Python.
from collections import namedtuple
from subprocess import Popen, PIPE

#=======================================================================================
# Datatypes
#=======================================================================================

ProcessOutput = namedtuple("ProcessOutput", ["stdout", "stderr"], verbose=False, rename=False)

#=======================================================================================
# Library
#=======================================================================================

#==========================================================
class Process(object):

	#=============================
	"""Represents a system process started by this script.
	Note: Refrain from calling .communicate() directly on the process from outside of this object."""
	#=============================

	def __init__(self, commandLine, run=True):
		self.commandLine = commandLine
		if run == True:
			self.run()
		self._communicated = False
		self._stdout = None
		self._stderr = None

	def run(self):
		self.process = Popen(self.commandLine, stdout=PIPE, stderr=PIPE)
		return self.process

	def waitAndGetOutput(self, timeout=None):
		if not self._communicated:
			self._stdout, self._stderr = self.process.communicate(timeout=timeout)
			self._communicated = True
		return ProcessOutput(self._stdout, self._stderr)

	def waitAndGetStdout(self, timeout=None):
		return self.waitAndGetOutput(timeout).stdout

	def waitAndGetStderr(self, timeout=None):
		return self.waitAndGetOutput(timeout).stderr