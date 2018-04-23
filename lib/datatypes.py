#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

import argparse

#=======================================================================================
# Library
#=======================================================================================

#==========================================================
class Namespace(argparse.Namespace):
	
	#=============================
	"""Pure namespace class.
	Basically serves as a dot-notation oriented dict.
	In its current implementation, this is a simple subclass of 'argparse.Namespace'"""
	#=============================

	pass

#==========================================================
class Singleton(type):

	#=============================
	# """Classe of this class will always return the same instance upon instantiation."""
	#=============================

	def __init__(singletonClass, className, parentClasses, classDict):
		singletonClass.singletonObject = None
	def __call__(self, *args, **kwargs):
		if self.singletonObject is None:
			self.singletonObject = type.__call__(self, *args, **kwargs)
		return self.singletonObject