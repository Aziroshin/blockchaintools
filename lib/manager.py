#-*- coding: utf-8 -*-

#=======================================================================================
"""Contains instruments tying the core lib together to streamline various workflows.
Think of this as a module that contains reusable parts of what would otherwise directly
go into the top level executable, so they are easily shareable between similar
executables.

Example: SingleCurrencyManager, which can both be used for a command line as well as
a GUI or curses interface, for as long as it's single currency focused."""
#=======================================================================================

#=======================================================================================
# Imports
#=======================================================================================

# Builtins.
import shutil
from pathlib import Path
# Local.
from lib.arguments import CommandLine, Arguments, ArgumentSetup
from lib.actions import Action, Actions
from lib.plugins import Plugin

#=======================================================================================
# Library
#=======================================================================================

#==========================================================
# Arguments
#==========================================================

#==========================================================
# Mnmnager related classes
#==========================================================

#==========================================================
class ManagerArgumentSetup(ArgumentSetup):
	
	#=============================
	"""Setup for command line in a single currency workflow."""
	#=============================
	
	def __init__(self, actions={}):
		# Takes list of Action objects.
		super().__init__()
		#self.actions = actions
	#def setUp(self):
		##TODO: Needs proper helptext. Test only.
		#self.parser.add_argument("action", help=self.actions)

#==========================================================
class SingleCurrencyManager(object):
	
	#=============================
	"""Represents a workflow where operations are performed on one specified currency."""
	#=============================
	
	def __init__(self, argumentSetup, pluginName):
		
		self.commandLine = CommandLine()
		# Initialize command line: Is expected to be the first occurrence.
		CommandLine().initSubParsers(dest="action")
		
		# Load plugin.
		self.plugin = Plugin(str(Path(__file__).parent.absolute()),\
			"plugins.currencies.{0}".format(pluginName))
		self.plugin.load()
		
		# Get args.
		self.args = Arguments(setups=[\
			ManagerArgumentSetup(self.plugin.module.Actions),\
			self.plugin.module.ArgumentSetup()
			]).get()
		#self.args = self.plugin.module.ArgumentSetup().parser.parse_args()
		
		# Run requested action.
		if not self.args.action is None:
			self.plugin.module.Actions().run(self.args.action, self.args)
		else:
			self.commandLine.showFullHelp()