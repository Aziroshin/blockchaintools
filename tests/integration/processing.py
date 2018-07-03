#=======================================================================================
# Imports
#=======================================================================================

from subprocess import Popen, PIPE
import os
import unittest
import random
import string
import tempfile
import stat
from pathlib import Path

import lib.filesystem
from lib.processing import ExternalProcess, ProcessList

# DEBUG
from lib.debugging import dprint
import time

#=======================================================================================
# Tests
#=======================================================================================

class ProcessingTestCase(unittest.TestCase):
	
	prefix = "blockchaintools_test"
	
	@property
	def testProcessIdentifier(self):
		
		"""A 64 digit random string to nearly-uniquely identify the process we'll test against.
		The string will be generated on first call. All subsequent calls will return
		the same string for the lifetime of the object.
		
		The motivation is to make process name collisions and the like unlikely.
		Such collisions could trip up the test and are something to watch out for.
		That's why executing these tests would be best done in a dedicated environment.
		"""
		
		if not hasattr(self, "_testProcessIdentifier"):
			self._testProcessIdentifier = "".join(random.SystemRandom().choice(\
				string.ascii_uppercase+string.ascii_lowercase+string.digits)\
					for i in range(0,64))
		return self._testProcessIdentifier
	
	@property
	def tempDir(self):
		"""Will hold the executable for the process we'll test against."""
		if not hasattr(self, "_tempDir"):
			self._tempDir = tempfile.TemporaryDirectory()
		return self._tempDir
	
	@property
	def testProcessName(self):
		"""Name of the process we're testing against."""
		return "{prefix}_name_{identifier}"\
			.format(prefix=type(self).prefix, identifier=self.testProcessIdentifier)
	
	@property
	def testProcessExecPath(self):
		"""Path to the executable of the process we'll test against."""
		return str(Path(self.tempDir.name, self.testProcessName))
	
	@property
	def testProcessSourcePath(self):
		"""Path to the source code for the executable of the process well test against.
		This just adds ".c" to .testProcessExecPath."""
		return "{0}.c".format(self.testProcessExecPath)
	
	@property
	def testProcessArgParam(self):
		"""Parameter name of the test-argument of the process we're testing against."""
		return "--{prefix}_param_{identifier}"\
			.format(prefix=type(self).prefix, identifier=self.testProcessIdentifier)
	
	@property
	def testProcessArgValue(self):
		"""Value of the test-argument of the process we're testing against."""
		return "{prefix}_value_{identifier}"\
			.format(prefix=type(self).prefix, identifier=self.testProcessIdentifier)
	
	@property
	def testProcessEnvVarName(self):
		return "{prefix}_envVarName_{identifier}"\
			.format(prefix=type(self).prefix, identifier=self.testProcessIdentifier)
	
	@property
	def testProcessEnvVarValue(self):
		return "{prefix}_envVarValue_{identifier}"\
			.format(prefix=type(self).prefix, identifier=self.testProcessIdentifier)
	
	@property
	def testProcess(self):
		"""The process we'll be testing against."""
		envDict = dict(os.environ)
		envDict[self.testProcessEnvVarName] = self.testProcessEnvVarValue
		if not hasattr(self, "_testProcess"):
			self._testProcess = Popen(\
			# We're simulating a somewhat complex command line here, with some blind arguments.
			[self.testProcessExecPath, self.testProcessArgParam, self.testProcessArgValue],\
			env=dict(os.environ),\
			shell=False,\
			stdout=PIPE)
		return self._testProcess
	
	def setUp(self):
		
		# Write test process source code.
		with open(self.testProcessSourcePath, "wt") as testProcessExec:
			testProcessExec.write("void main() {while(1==1) {}}")
		
		# Compile it.
		# TODO: Make sure doesn't hang and error properly on failure.
		Popen(["gcc", self.testProcessSourcePath, "-o", self.testProcessExecPath],\
			stdout=PIPE).communicate()
		
		# Set appropriate permissions for the compiled executable.
		Path(self.testProcessExecPath).chmod(0o700)
		
		# Start test.
		self.testProcess
	
	def tearDown(self):
		# Kill process.
		self.testProcess.kill()
		self.testProcess.communicate()
		# Remove directory
		self.tempDir.cleanup()

class ProcessListTestCase(ProcessingTestCase):
	
	@property
	def partialTestProcessArgValue(self):
		"""This is .testProcessArgValue[4:-3]"""
		return self.testProcessArgValue[4:-3]
	
	def test_byArgPart(self):
		#"""[Test: ProcessList.byArgPart]"""
		matchedProcess = ProcessList().byArgPart(self.partialTestProcessArgValue)[0]
		self.assertEqual(matchedProcess.getPid(), self.testProcess.pid)
		
	def test_byArg(self):
		matchedProcess = ProcessList().byArg(self.testProcessArgParam)[0]
		self.assertEqual(matchedProcess.getPid(), self.testProcess.pid)

class ExternalLinuxProcessTestCase(ProcessingTestCase):
	def test_getEnvDict(self):
		process = ProcessList().byName(self.testProcessName)[0]
		envDict = process.getEnvDict()
		self.assertIn(self.testProcessEnvVarName, envDict.keys)
		self.assertIn(self.testProcessEnvVarValue, envDict.values)


# This class gets instantiated by the "testing" script right after importing this module.
class Testing(object):
	def run(self):
		ProcessListTestCase()
		suite = unittest.TestSuite([ProcessListTestCase()])
		runner = unittest.TextTestRunner()
		runner.run(suite)
		
if __name__ == "__main__":
	unittest.main()
