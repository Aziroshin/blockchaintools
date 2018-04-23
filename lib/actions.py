#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

import argparse
from lib.datatypes import Singleton

#=======================================================================================
# Library
#=======================================================================================

class Action(object):
	
	def __init__(self, handle, args):
		self.handle = handle
		self.args = args

class Actions(dict):
	
	def add(self, handle, action):
		self[handle] = action
	
	def run(self, handle, args):
		self[handle](handle, args).run()