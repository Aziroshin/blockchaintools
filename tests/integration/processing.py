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

# Local
import lib.filesystem
from lib.processing import ExternalProcess, ProcessList
from tests.lib.mocking import DummyProcess

# DEBUG
#from lib.debugging import dprint
#import time

#=======================================================================================
# Tests
#=======================================================================================

class ProcessingDummyProcess(DummyProcess):
	
	@property
	def defaultArgs(self):
		return [self.argParam, self.argValue]

class ProcessingTestCase(unittest.TestCase):
	
	@property
	def TestProcess(self):
		return ProcessingDummyProcess
	
	@property
	def prefix(self):
		return "blockchaintools_test"
	
	@property
	def testProcess(self):
		if not hasattr(self, "_testProcess"):
			self._testProcess = self.makeDefaultTestProcess()
		return self._testProcess
	
	def makeDefaultTestProcess(self):
		"""Instantiate test process and return the instance."""
		return self.TestProcess(prefix=self.prefix)
	
	def setUp(self):
		# Start test.
		self.testProcess.start()
	
	def tearDown(self):
		self.testProcess.stop()

class ProcessListTestCase(ProcessingTestCase):
	
	@property
	def partialTestProcessArgValue(self):
		"""This is .testProcessArgValue[4:-3]"""
		return self.testProcess.argValue[4:-3]
	
	def test_byPid(self):
		matchedProcess = ProcessList().byPid(self.testProcess.pid)
		self.assertEqual(self.testProcess.pid, matchedProcess[0].pid)
	
	def test_byName(self):
		matchedProcess = ProcessList().byName(self.testProcess.name)[0]
		self.assertEqual(matchedProcess.getPid(), self.testProcess.pid)
	
	def test_byPath(self):
		matchedProcess = ProcessList().byPath(self.testProcess.execPath)[0]
		self.assertEqual(self.testProcess.execPath, matchedProcess.path)
	
	def test_byArgPart(self):
		#"""[Test: ProcessList.byArgPart]"""
		matchedProcess = ProcessList().byArgPart(self.partialTestProcessArgValue)[0]
		self.assertEqual(matchedProcess.getPid(), self.testProcess.pid)
		
	def test_byArg(self):
		matchedProcess = ProcessList().byArg(self.testProcess.argParam)[0]
		self.assertEqual(matchedProcess.getPid(), self.testProcess.pid)

class ExternalLinuxProcessTestCase(ProcessingTestCase):
	
	def test_name(self):
		process = ProcessList().byPid(self.testProcess.pid)[0]
		self.assertEqual(self.testProcess.name, process.name)
	
	def test_path(self):
		process = ProcessList().byPid(self.testProcess.pid)[0]
		self.assertEqual(self.testProcess.execPath, process.path)
	
	def test_getEnvDict(self):
		process = ProcessList().byName(self.testProcess.name)[0]
		envDict = process.env
		self.assertIn(self.testProcess.envVarName, envDict.keys())
		self.assertIn(self.testProcess.envVarValue, envDict.values())
		
	def test_hasEnvVar(self):
		process = ProcessList().byPid(self.testProcess.pid)[0]
		self.assertTrue(process.hasEnvVar(self.testProcess.envVarName))

class ProcessingMultiArgTestCase(ProcessingTestCase):
	
	"""Base class for test cases needing multiple dummy processs arguments to test against."""
	
	@property
	def testArgs(self):
		"""A dict containing the arguments for testing in a convenient key-value association."""
		return dict({"param1": "value1", "param2": "value2", "param3": "value3", "param4": "value4"})
	
	@property
	def testArgsToPass(self):
		"""Arguments passed to the test process."""
		return ["param1", "value1", "param2", "value2", "param3", "value3", "param4", "value4"]
	
	@property
	def testArgsToCheck(self):
		"""Arguments subclassed tests might want to use to test subsets."""
		return ["param2", "value2", "param3", "value3"]

	@property
	def uniqueTestArgsToCheck(self):
		return [self.testProcess.makeUnique(a) for a in self.testArgsToCheck]
	
	def makeDefaultTestProcess(self):
		return self.TestProcess(prefix=self.prefix,\
			args=self.testArgsToPass, makeArgsUnique=True)

class ExternalLinuxProcessMultiArgTestCase(ProcessingMultiArgTestCase):
	
	def test_inArgv(self):
		process = ProcessList().byPid(self.testProcess.pid)[0]
		self.assertTrue(process.inArgv(self.uniqueTestArgsToCheck))
	
	def test_byArgvPart(self):
		matchedProcess = ProcessList().byArgvPart(self.uniqueTestArgsToCheck)[0]
		self.assertEqual(self.testProcess.pid, matchedProcess.pid)
	

## This class gets instantiated by the "testing" script right after importing this module.
#class Testing(object):
	#def run(self):
		#ProcessListTestCase()
		#suite = unittest.TestSuite([ProcessListTestCase()])
		#runner = unittest.TextTestRunner()
		#runner.run(suite)
		
if __name__ == "__main__":
	unittest.main()
