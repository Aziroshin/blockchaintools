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
from lib.actions import ActionData, Actions
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
		
		# Prepare, get and run requested action.
		if not self.args.action is None:
			
			data = ActionData()
			# We're passing the command line arguments to the plugin because each
			# action may have its own subparser configuration, depending on
			# how the plugin defines its command line parameters.
			data.args = self.args
			# The reason why the config is specified on this level and not just
			# used directly in the module it's defined:
			#     "Actions" contains all actions defined through the plugins the
			#     plugin in question depends on, which means we might be calling
			#     actions from plugins up in the dependency chain. If that action
			#     directly referenced the corresponding Config internally, it'd
			#     be using that parent plugin's Config. That's why we have to pass
			#     it the Config that corresponds to the plugin we're working with
			#     here.
			data.Config = self.plugin.module.Config
			
			# Get requested action.
			Action = self.plugin.module.Actions().get(self.args.action)
			action = Action(handle=self.args.action, data=data)
			
			# Run action.
			print(action.run().terminalString, end="")
			
		else:
			self.commandLine.showFullHelp()