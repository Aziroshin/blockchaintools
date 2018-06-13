#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Python
import argparse
import json

# Local
from lib.datatypes import Singleton
#from lib.debugging import dprint #NOTE: DEBUG

#=======================================================================================
# Library
#=======================================================================================

#==========================================================
# Action Classes
#==========================================================

class ActionReturnValue(object):
	
	#=============================
	"""Every action returns an object of either this or a subclass of this.
	
	The return value as provided by the action gets stored in self.raw.
	Various other forms may be available, such as self.json or self.string,
	whereas string is expected to be optimized for terminal output first
	and foremost.
	
	In case the subclass in question doesn't have customzed behaviour
	for those additional forms, this class will provide basic default
	behaviour, trying to deduce from self.raw."""
	#=============================
	
	def __init__(self, raw):
		self.raw = raw
	
	@property
	def json(self):
		
		# NOTE: Custom decorators subclasses could use to declare methods
		# that process this might be a good idea.
		# Should also look at JSONEncoders.
		
		"""Override to provide custom json output. Will guess otherwise.
		
		Default attitude is to return null if it can't guess."""
		
		output = None
		if hasattr(self.raw, "_repr_json_"):
			output = self.raw._repr_json_
		elif type(self.raw) in [str, int, float, tuple, list, dict, type(None)]:
			output = self.raw
		return json.dumps(output)
	
	@property
	def string(self):
		if hasattr(self.raw, "_repr_str_"):
			output = self.raw._repr_str_
		elif type(self.raw) == dict:
			output = self._listToString(["{key}: {value}".format(key=key, value=value)\
				for key, value in self.raw.items()])
		elif type(self.raw) == list:
			output = self._listToString(self.raw)
		elif type(self.raw) == tuple:
			output = self._listToString([item for item in self.raw])
		else:
			output = str(self.raw)
		return output
	
	@property
	def terminalString(self):
		if hasattr(self.raw, "_repr_str_terminal_"):
			output = self.raw._repr_str_terminal_
		else:
			output = self.string
		return output
	
	def _listToString(self, listToTransform):
		"""Turn a list into a user facing terminal friendly string."""
		return "\n".join(listToTransform)
	

class ActionReturnValueAggregateList(list):
	
	@property
	def _repr_str_(self):
		return "".join([returnValue._repr_str_ for returnValue in self])
	
	@property
	def _repr_str_terminal_(self):
		return "".join([returnValue._repr_str_terminal_ for returnValue in self])
	
class ActionReturnValueAggregate(ActionReturnValue):
	
	#=============================
	"""Takes multiple ActionReturnValue objects and provides aggregated access.
	
	Currently, only _repr_str_ is implemented, which will return a concatenation
	of all ActionReturnValue objects' _repr_str_ values.
	
	_repr_json_ has to be implemented specifically
	in appropriate subclasses for now if required."""
	#=============================
	
	def __init__(self, returnValues=ActionReturnValueAggregateList()):
		self.raw = returnValues
		
	def addReturnValue(self, returnValue):
		self.raw.append(returnValue)
		
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
		#OVERRIDE
		return ActionReturnValue(None)

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
		self.setUpUninheritable()
	
	def setUp(self):
		pass#OVERRIDE
	
	def setUpUninheritable(self):
		pass#OVERRIDE
	
	def add(self, handle, action):
		self[handle] = action
	
	def get(self, handle):
		return self[handle]
