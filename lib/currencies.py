#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Python.
from collections import OrderedDict, namedtuple
import json
import inspect

# Local.
from lib.exceptions import Error, ErrorWithCodes, ErrorCodes

#=======================================================================================
# Library
#=======================================================================================

#==========================================================
# Datatypes
#==========================================================

AttributeTuple = namedtuple("DefaultValueAttribute", ["name", "value"],\
	verbose=False, rename=False)

#==========================================================
# Exceptions
#==========================================================

#==========================================================
class WalletError(ErrorWithCodes):
	codes = ErrorCodes()
	codes.CLI_ERROR = 0
	codes.RPC_CONNECTION_FAILED = 21

#==========================================================
class DaemonStuckError(Error):
	pass

#==========================================================
# Wallet Classes
#==========================================================

#==========================================================
class Wallet(object): pass

#==========================================================
class CurrencyConfig(object):
	
	#=============================
	"""Represents the configuration for handling a currency.
	Intended to be used with Actions and Wallets in plugins.
	
	Is expected to have class attributes starting with "default" in their
	variable name, which are then passed as defaults to __init__ for the
	corresponding keyword argument, which is expected to have a
	lower-case-starting variable name minus the "default" prefix.
	
	Any member variable that is assigned in the end is supposed to
	follow the naming convention as laid out for the corresonding
	keyword argument whenever applicable.
	
	Numbers are also expected to be strings by default, to keep
	things consistent across various types of sources for config
	values that might not always preserve datatypes throughout
	whatever means they take to reach our object.
	
	Example of the above described convention:
	
		class SomeConfig(<OurClassName>):
			defaultMushroom = "shiitake"
			defaultNumber = "32"
			def __init__(self, mushroom=defaultMushroom, number=defaultNumber):
				self.mushroom = mushroom
				self.number = number
		
	In the above example, default values can then easily be
	overriden upon instantiation:
		SomeConfig(mushroom="lingzhi", number="1053")
	"""
	#=============================
	
	@classmethod
	def getClassAttributes(self):
		attributes = {}
		for parentClass in inspect.getmro(self):
			attributes.update(parentClass.__dict__)
		attributes.update(self.__dict__)
		return attributes
	
	@property
	def _defaults_(self):
		
		"""Return all attributes that are defaults (start with "default")."""
		
		defaults = []
		for attributeName, attributeValue in self.__class__.getClassAttributes().items():
			if attributeName.startswith("default"):
				defaults.append(AttributeTuple(\
					name=attributeName, value=attributeValue))
		return defaults
	
	@property
	def _config_(self):
		
		"""Return all attributes that aren't defaults or __attributes__."""
		
		config = []
		for attributeName, attributeValue in self.__dict__.items():
			if\
			not attributeName.startswith("__")\
			and not attributeName.startswith("default")\
			and not attributeName.endswith("__"):
				config.append(AttributeTuple\
					(name=attributeName, value=attributeValue))
		return config
		
	@property
	def _repr_dict_(self):
		return OrderedDict([\
			("Defaults", self._defaults_),\
			("Config", self._config_),\
		])
	
	@property
	def _repr_json_(self):
		"""A json object representing the attributes of this object."""
		return json.puts(self._repr_dict_)
	
	@property
	def _repr_str_terminal_(self):
		
		"""A string representing the attributes of this object.
		
		For every category, the attributes are formatted to be each on
		a new line and inset using one \t, with the attribute variable
		name and the corresponding value being formatted like this:
			name: value
		
		Example output:
		
			Defaults:
				defaultMushroom: shiitake
				defaultNumber: 32
			Config:
				mushroom: lingzhi
				number: 1053
			
		"""
		
		string = ""
		categoryStrings = []
		for category, attributes in self._repr_dict_.items():
			# Get all the attribute key/value pairs for this category lined up
			# into individual per-line strings stored in a list.
			attributeStrings = []
			for attribute in attributes:
				attributeStrings.append("{name}: {value}"\
					.format(name=attribute.name, value=attribute.value))
			# Join our list using \n\t and slap the category name at the top.
			categoryStrings.append("{category}:\n\t{attributes}"\
				.format(category=category, attributes="\n\t".join(attributeStrings)))
		# Finally, join all of this together into one huge terminal noodle salad. :p
		return "\n".join(categoryStrings)