#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

import argparse
from lib.datatypes import Singleton

#=======================================================================================
# Library
#=======================================================================================

class ActionData(argparse.Namespace): pass

class Action(object):
	
	#=============================
	"""Subclass this in order to write the various actions you want your program to perform.
	
	Takes:
		- handle (string)
			The handle by which this action is referenced. Useful for error messaging.
		- data (None or ActionData)
			Object containing all necessary data as attributes. Theoretically, this can
			be any type of object, but error reporting measures won't be optimized around,
			say, passing a dict, list, int or some wild object.
	
	This is essentially a container for business logic that does all the end-point things
	based on the core lib and whatever else you want to pull in. This is expected to be
	the unit that user-facing interfaces use to do the user's bidding.
	
	Example: A command line driven interface may enable the user to specify certain
	actions they want performed (e.g. run another program and return its output or
	install something). That interface could then delegate to the Action subclass
	that does just that and run it.
	"""
	#=============================
	
	def __init__(self, handle, data):
		self.handle = handle
		self.data = data
		
	def run(self):
		pass#OVERRIDE

class Actions(dict):
	
	#=============================
	"""Keeps track of Action objects registered with it.
	
	Register them using .add(), run them using .run().
	.setUp() provides a place to to stuff various .add() calls in subclasses.
	
	IMPORTANT: If you want the .setUp() of the parent class to be run,
	you'll have to make that call in .setUp(), it won't be done
	automagically."""
	#=============================
	
	def __init__(self):
		self.setUp()
	
	def setUp(self):
		pass#OVERRIDE
	
	def add(self, handle, action):
		self[handle] = action
	
	def run(self, handle, args):
		self[handle](handle, args).run()
