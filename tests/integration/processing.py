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
from lib.debugging import dprint
import time

#=======================================================================================
# Tests
#=======================================================================================

class ProcessingDummyProcess(DummyProcess):
	
	@property
	def defaultArgs(self):
		return [self.argParam, self.argValue]

class ProcessingTestCase(unittest.TestCase):
	
	#=============================
	# BEGIN: COMMON
	# Often used functionality in
	# this test module.
	#=============================
	@property
	def externalProcess(self):
		"""The external, already started test process found by PID."""
		if not hasattr(self, "_externalProcess"):
			self._externalProcess = ProcessList().byPid(self.process.pid)[0]
		return self._externalProcess
	# END: COMMON
	#=============================
	
	@property
	def TestProcess(self):
		return ProcessingDummyProcess
	
	@property
	def prefix(self):
		return "blockchaintools_test"
	
	@property
	def process(self):
		if not hasattr(self, "_process"):
			self._process = self.makeDefaultTestProcess()
		return self._process
	
	def makeDefaultTestProcess(self):
		"""Instantiate test process and return the instance."""
		return self.TestProcess(prefix=self.prefix)
	
	def setUp(self):
		# Start test.
		self.process.start()
	
	def tearDown(self):
		self.process.stop()

class ProcessListTestCase(ProcessingTestCase):
	
	@property
	def partialTestProcessArgValue(self):
		"""This is .processArgValue[4:-3]"""
		return self.process.argValue[4:-3]
	
	def test_byPid(self):
		matchedProcess = ProcessList().byPid(self.process.pid)
		self.assertEqual(self.process.pid, matchedProcess[0].pid)
	
	def test_byName(self):
		matchedProcess = ProcessList().byName(self.process.name)[0]
		self.assertEqual(matchedProcess.getPid(), self.process.pid)
	
	def test_byPath(self):
		matchedProcess = ProcessList().byPath(self.process.execPath)[0]
		self.assertEqual(self.process.execPath, matchedProcess.path)
	
	def test_byArgPart(self):
		#"""[Test: ProcessList.byArgPart]"""
		matchedProcess = ProcessList().byArgPart(self.partialTestProcessArgValue)[0]
		self.assertEqual(matchedProcess.getPid(), self.process.pid)
		
	def test_byArg(self):
		matchedProcess = ProcessList().byArg(self.process.argParam)[0]
		self.assertEqual(matchedProcess.getPid(), self.process.pid)

class ExternalLinuxProcessTestCase(ProcessingTestCase):
	
	def test_name(self):
		self.assertEqual(self.process.name, self.externalProcess.name)
	
	def test_path(self):
		self.assertEqual(self.process.execPath, self.externalProcess.path)
	
	def test_getEnvDict(self):
		process = ProcessList().byName(self.process.name)[0]
		envDict = process.env
		self.assertIn(self.process.envVarName, envDict.keys())
		self.assertIn(self.process.envVarValue, envDict.values())
		
	def test_hasEnvVar(self):
		self.assertTrue(self.externalProcess.hasEnvVar(self.process.envVarName))
		
	def test_hasEnvPair(self):
		self.assertTrue(self.externalProcess.hasEnvPair(self.process.envVarName, self.process.envVarValue))
		
	def test_status(self):
		dprint(self.externalProcess.status)
		self.assertEqual(self.externalProcess.status["Pid"], self.process.pid)
		

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
		return [self.process.makeUnique(a) for a in self.testArgsToCheck]
	
	def makeDefaultTestProcess(self):
		return self.TestProcess(prefix=self.prefix,\
			args=self.testArgsToPass, makeArgsUnique=True)

class ExternalLinuxProcessMultiArgTestCase(ProcessingMultiArgTestCase):
	
	def test_inArgv(self):
		process = self.externalProcess
		self.assertTrue(process.inArgv(self.uniqueTestArgsToCheck))
	
	def test_byArgvPart(self):
		matchedProcess = ProcessList().byArgvPart(self.uniqueTestArgsToCheck)[0]
		self.assertEqual(self.process.pid, matchedProcess.pid)
	

## This class gets instantiated by the "testing" script right after importing this module.
#class Testing(object):
	#def run(self):
		#ProcessListTestCase()
		#suite = unittest.TestSuite([ProcessListTestCase()])
		#runner = unittest.TextTestRunner()
		#runner.run(suite)
		
if __name__ == "__main__":
	unittest.main()
