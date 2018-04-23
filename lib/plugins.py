#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

import sys

#=======================================================================================
# Library
#=======================================================================================

class Plugin(object):
	
	#=============================
	"""Represents a python module intended to be inserted from an arbitrary location.
	The structure of the module itself isn't defined or checked here. That's up to
	the caller."""
	#=============================
	
	def __init__(self, parentDirPath, modulePath):
		self.parentDirPath = parentDirPath
		self.modulePath = modulePath
		
	def load(self):
		sys.path.insert(1, self.parentDirPath)
		self.module = __import__(name=self.modulePath, globals=globals(),\
			locals=locals(), fromlist=[self.modulePath.rpartition(".")[2]], level=0)
		