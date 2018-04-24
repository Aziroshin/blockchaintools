#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

import os
import shutil

from lib.exceptions import Error

#=======================================================================================
# Library
#=======================================================================================

#==========================================================
# Exceptions
#==========================================================

#==========================================================
class PathNotFoundError(Error):
	pass

#==========================================================
# Filesystem related classes
#==========================================================

#==========================================================
class BatchPathExistenceCheckPath(object):
	
	#=============================
	"""Pairs a path with an existence-check and an error message to use if it doesn't exist."""
	#=============================
	
	def __init__(self, path, errorMessage):
		self.path = path
		self.errorMessage = errorMessage

	def exists(self):
		"""Checks whether the path exists; returns 'True' if it does, 'False' if it doesn't.
		This also considers executable availability through $PATH, in case the specified
		'path' is not actually a path per se, but the name of an executable available through
		$PATH."""
		if self.path is None:
			return False
		if os.path.exists(self.path):
			return True
		else:
			if shutil.which(self.path):
				return True
			else:
				return False

#==========================================================
class BatchPathExistenceCheck(object):
	
	#=============================
	"""Takes path+errorMessage pairs and checks whether they exist, with an optional error raised.
	Raising the optional error is the default behaviour and needs to be disabled if
	that is undesired."""
	#=============================
	
	def __init__(self):
		self.paths = []
		self.batchErrorMessage = ""
		self.nonExistentPathCount = 0
	
	def addPath(self, path, errorMessage):
		self.paths.append(BatchPathExistenceCheckPath(path, errorMessage))
	
	def checkAll(self, autoRaiseError=True):
		for path in self.paths:
			if not path.exists():
				self.nonExistentPathCount += 1
				self.batchErrorMessage\
					= "{batchErrorMessage}\n{errorMessage}".format(\
					batchErrorMessage=self.batchErrorMessage, errorMessage=path.errorMessage)
		if autoRaiseError:
			self.raiseErrorIfNonExistentPathFound()
	
	def raiseErrorIfNonExistentPathFound(self):
		if self.nonExistentPathCount > 0:
			self.raiseError()
	
	def raiseError(self):
		if self.batchErrorMessage == "":
			raise PathNotFoundError("Error: No non-existent paths found, but error was raised anyway.")
		elif self.nonExistentPathCount == 1:
			raise PathNotFoundError(\
				"Error: The following path doesn't exist: {batchErrorMessage}".format(\
					batchErrorMessage=self.batchErrorMessage))
		elif self.nonExistentPathCount > 1:
			raise PathNotFoundError(\
				"Error: The following paths don't exist: {batchErrorMessage}".format(\
					batchErrorMessage=self.batchErrorMessage))