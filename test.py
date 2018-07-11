#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Runs testing modules from the testing directory. Not to confuse with unit tests."""
# Convention: "tests" like these will be called "testings" throughout the codebase.
# "testings" are everything test related that doesn't fit the unit test paradigm,
# typically geared towards analyzing what's appening in the application for development
# and debugging purposes.

#=======================================================================================
# Imports
#=======================================================================================
#==========================================================
#=============================

import unittest
from pathlib import Path
import argparse
import os
import sys
from collections import UserDict, UserList

# Debug
#from lib.debugging import dprint

#=======================================================================================
# Configuration
#=======================================================================================

TESTS_DIR = str(Path(Path(__file__).absolute().parent, "tests"))

#=======================================================================================
# Library
#=======================================================================================

#=============================
# Arguments
#=============================

class Arguments(object):
	
	#=============================
	"""A basic class for the setup for the arguments we take. Override .setUp() to implement."""
	#=============================
	
	def __init__(self):
		self.parser = argparse.ArgumentParser()
		self.setUp()
		
	def setUp(self):
		"""Override this with your particular argument configuration."""
		pass
	
	def get(self):
		"""Get the initialized argparse.Namespace object for our arguments."""
		return self.parser.parse_args()

#=============================
# Testing
#=============================

class TestDirModuleList(UserList):
	
	def __init__(self, dirPath):
		self.data = []
		for fileName in os.listdir(str(Path(dirPath))):
			if self.isTestModule(Path(dirPath, fileName)):
				self.append(Path(fileName).stem)
		
	def isTestModule(self, path):
		"""Returns True if path seems to point to a python test module, False otherwise."""
		if not path.name == "__init__.py":
			return True
		else:
			return False

class Tests(UserDict):
	
	def __init__(self, path):
		self.data = {}
		# Test types.
		for testType in [item for item in os.listdir(path) if Path(path, item).is_dir()]:
			self[testType] = [test for test in TestDirModuleList(Path(path, testType))]
			
	@property
	def types(self):
		return self.keys()

def runModule(module):
	chosenModule = __import__(name="tests.{testType}.{moduleName}"\
		.format(moduleName=module, testType=args.type),\
			globals=globals(), locals=locals(), fromlist=[module], level=0)
	#chosenModule.Testing().run()
	suite = unittest.defaultTestLoader.loadTestsFromModule(chosenModule)
	unittest.TextTestRunner(verbosity=2).run(suite)

def runModules(moduleList):
	for module in moduleList:
		runModule(module)

class TestingArguments(Arguments):
	
	#=============================
	"""A basic class for the setup for the arguments we take. Override .setUp() to implement."""
	#=============================
	
	def setUp(self):
		
		""" We take a single argument besides argparse's defaults: Name of the testing module to load.
		Upon calling --help, we'll also list all the available modules from the testing directory."""
		
		self.parser.add_argument("-a", "--all", action="store_false",help="Run all tests")
		self.parser.add_argument("type", default=None, help="Type of test {unit, integration}")
		self.parser.add_argument(\
			"module", default=None, help="Name of the testing module to run. Consult contents of the"
			" testing dir for options: {dirContents}".format(dirContents=Tests)
			)

#=======================================================================================
# Action
#=======================================================================================

if __name__ == "__main__":
	
	args = TestingArguments().get()
	if not (args.type == "unit" or args.type == "integration" or args.type == None):
		print("You have to specify either \"unit\" or \"integration\" as the test type. Exiting.")
		sys.exit(1)
	import vivo
	
	if args.all:
		tests = Tests(TESTS_DIR)
		if args.type is None:
			for testType in tests.types:
				runModules(tests[testType])
		else:
			runModules(Tests(TESTS_DIR)[args.type])
			
	else:
		runModule(args.module)
