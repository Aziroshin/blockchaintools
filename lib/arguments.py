#-*- coding: utf-8 -*-

# NOTE: This module implicitely depends on actions.py

#=======================================================================================
# Imports
#=======================================================================================

import argparse
from lib.datatypes import Singleton

#=======================================================================================
# Library
#=======================================================================================

class CommandLine(object, metaclass=Singleton):
	
	#=============================
	"""Represents the command line the program was started with as a resource.
	Currently only features .parser, which points to an ArgumentParser
	object.
	As the command line is a limited resource, this is a Singleton, which
	means it always returns the same instance."""
	#=============================
	
	def __init__(self):
		self.parser = argparse.ArgumentParser()
		self._subparsers = None
		self.subParsers = []
		
	def initSubParsers(self, *args, **kwargs):
		self._subparsers = self.parser.add_subparsers(*args, **kwargs)
		
	def parse(self):
		return self.parser.parse_args()
	
	def addSubParser(self, *args, **kwargs):
		if self._subparsers is None:
			self._subparsers = self.parser.add_subparsers()
		subParser = self._subparsers.add_parser(*args, **kwargs)
		self.subParsers.append(subParser)
		return subParser
	
	def showFullHelp(self):
		# Show main parser help.
		self.parser.print_help()
		# Show help for all subparsers, too.
		for subParser in self.subParsers:
			subParser.show_help()

class ArgumentSetup(object):
	
	#=============================
	"""Argument setup that doesn't consider the class parent's .setUp method.
	Override .setUp to create the command line argument setup using
	self.parser.<argparse functionality of your choice>.
	
	The ArgumentParser used is based off of CommandLine, which is a singleton,
	thus self.parser will always return the same instance across subclasses."""
	#=============================
	
	def __init__(self):
		self.commandLine = CommandLine()
	
	def setUp(self):
		pass#OVERRIDE
	
	@property
	def parser(self):
		return self.commandLine.parser
	
	@property
	def subParsers(self):
		return self.commandLine.subParsers
	
	@property
	def addSubParser(self, *args, **kwargs):
		return self.commandLine.addSubParser(*args, **kwargs)
		
	
class Arguments(object):
	
	#=============================
	"""Takes a list of ArgumentSetup objects and provides a method to get the arguments."""
	#=============================
	
	def __init__(self, setups=[]):
		self.setups = setups
	
	def get(self):
		"""Iterate through the setups and get the arguments as argparse.Namespace."""
		for setup in self.setups:
			setup.setUp()
		return CommandLine().parse()
