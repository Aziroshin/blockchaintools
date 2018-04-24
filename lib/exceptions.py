#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Builtin
import os

# Local
from lib.datatypes import Namespace

#=======================================================================================
# Library
#=======================================================================================

#==========================================================
class ErrorCodes(Namespace):
	
	#=============================
	"""Namespace class to configure error codes for execeptions."""
	#=============================
	
	pass

#==========================================================
class FancyErrorMessage(object):

	#=============================
	# """Provides error messages that are a bit better formatted and visible for the end user."""
	#=============================

	def __init__(self, message, title=""):
		decorTop = "[BEGIN: BLOCKCHAINTOOLS ERROR]{title}".format(title=title)
		decorBottom = "[END: BLOCKCHAINTOOLS ERROR]"
		self.string = "{eol}{decorTop}{eol}{message}{eol}{decorBottom}"\
			.format(eol=os.linesep, decorTop=decorTop, message=message, decorBottom=decorBottom)
		__repr__ = self.string

#==========================================================
class Error(Exception):
	
	#=============================
	"""Exception with a fancy error message."""
	#=============================
	
	def __init__(self, message):
		super().__init__(FancyErrorMessage(message).string)

class ErrorCodeError(Error):
	pass

#==========================================================
class ErrorWithCodes(Error):
	
	#=============================
	"""Error with an error code for the 'errno' constructor parameter.
	The possible error numbers are to be configured as class variables of the
	appropriate subclass. Upon raising the error, one of these constants is
	supposed to be passed to 'errno'. During error handling, checks are
	supposed to use these constants as well. Never use the actual integer
	value anywhere except when defining the class variable referencing it.
	The convention is to use all upper case variable names for these."""
	#=============================
	
	codes = ErrorCodes()
	
	def __init__(self, message, code):
		self.code = code
		super().__init__(message)
	
	@property
	def codeNames(self):
		"""Returns a list of all code names associated with this error."""
		return self.__dict__.keys()
	
	@property
	def codeName(self):
		"""The code name for this error."""
		self.getNameByCode(self.code)
		raise ErrorCodeError(\
			"The following error code couldn't be resolved: \"{code}\". Available error codes:\n{codeList}"\
			.format(code=code, codeList=self.codeNames))
	
	def getCodeByName(self, name):
		"""Return the error code that matches the specified code name."""
		return self.codes.__dict__[name]
	
	def getNameByCode(self, code):
		"""Takes an error code and returns its (variable) name.
		This is a reverse dictionary lookup by the code for the name of the codes namespace object.
		We expect every error code to only exist once. Break that and it'll explode in your face. :p"""
		for name in self.codes.codeNames:
			if code == self.getCodeByName(name):
				return name