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
	
	prefix = "blockchaintools_test"
	
	def __init__(self, methodName="runTest"):
		super().__init__(methodName)
		self.testProcess = ProcessingDummyProcess(prefix="blockchaintools_test")
	
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


## This class gets instantiated by the "testing" script right after importing this module.
#class Testing(object):
	#def run(self):
		#ProcessListTestCase()
		#suite = unittest.TestSuite([ProcessListTestCase()])
		#runner = unittest.TextTestRunner()
		#runner.run(suite)
		
if __name__ == "__main__":
	unittest.main()
