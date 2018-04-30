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
		self.subParsers = {}r
	
	def initSubParsers(self, *args, **kwargs):
		self._subparsers = self.parser.add_subparsers(*args, **kwargs)
		
	def parse(self):
		return self.parser.parse_args()
	
	def addSubParser(self, *args, **kwargs):
		if self._subparsers is None:
			self._subparsers = self.parser.add_subparsers()
		subParser = self._subparsers.add_parser(*args, **kwargs)
		if len(args):
			name = args[0]
		else:
			name = kwargs["name"]
		self.subParsers[name] = subParser
		return subParser
	
	def showFullHelp(self):
		# Show main parser help.
		print("#============================")
		print("# Help")
		print("#============================\n")
		self.parser.print_help()
		# Show help for all subparsers, too.
		if len(self.subParsers.keys()):
			print("\n#============================")
			print("# Actions")
			print("#============================\n")
			for name, subParser in self.subParsers.items():
				print("#==============")
				print("#", name)
				print("#==============\n")
				subParser.print_help()

class ParserSetup(object):
	
	#=============================
	"""Takes a parser for configuration.
	This serves the purpose of helping to organize argument setup code a little more.
	
	Takes:
		- parser (ArgumentParser)
			Gets saved to self.parser for reference from .setUp()
	
	Override .setUp() with calls to self.parser."""
	#=============================
	
	def __init__(self, parser):
		self.parser = parser
		self._makeSetup()
		
		return self._parser
		
	def _makeSetup(self):
		
		"""Runs through all .setUp methods in the class hierarchy
		
		Override to alter that behaviour.
		
		@MODIFIER@: Only use in this class and subclasses, no from-outside calls."""
		
		self.setUpUpstream()
		self.setUp()
		
	def setUp(self):
		"""Make calls to self.parser to configure command line parameters."""
		pass#OVERRIDE
	
	def setUpUpstream(self):
		"""Go through all base classes and call .setUp."""
		try:
			for Base in self.__class__.__bases__:
				try:
					super(Base, self).setUp()
				except AttributeError:
					# 'Guess someone mixed in a non-ParserSetup class as a parent.
					pass
		except AttributeError:
			# It's us: Our parent class doesn't have .setUp. ;)
			pass

class ArgumentSetup(object):
	
	#=============================
	"""Override .setUp to create the command line argument setup using
	self.parser.<argparse functionality of your choice>.
	
	The ArgumentParser used is based off of CommandLine, which is a singleton,
	thus self.parser will always return the same instance across subclasses."""
	#=============================
	
	def __init__(self):
		self.commandLine = CommandLine()
	
	@property
	def parser(self):
		return self.commandLine.parser
	
	@property
	def subParsers(self):
		return self.commandLine.subParsers
	
	def setUp(self):
		pass#OVERRIDE
	
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
