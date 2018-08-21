#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Builtins
import os
import shutil
import time
from pathlib import Path

# Local
from lib.currencies import CurrencyConfig, Wallet, WalletError
from lib.arguments import ArgumentSetup, ParserSetup
from lib.actions import Action, Actions, ActionReturnValue, ActionReturnValueAggregate
from lib.filesystem import BatchPathExistenceCheck
from lib.processing import Process, ProcessList
#from lib.debugging import dprint #NOTE: DEBUG

# Debug
from lib.debugging import dprint

#=======================================================================================
# Library
#=======================================================================================



#==========================================================
# Wallet Classes
#==========================================================

#==========================================================
class BitcoinConfig(CurrencyConfig):
	
	#=============================
	"""Holds and deduces basic data required to manage and communicate with the wallet.
	Takes:
		basePaths: (list)
			List of paths to check for cliBinName and daemonBinName.
		cliBinName: (string)
			Name of the cli binary.
		daemonBinName: (string)
			Name of the daemon binary.
		dataDirName: (string)
			Name of the datadir.
		dataDirBaseDirPath: (string)
			Path to the directory the datadir is expected to reside in.
		dataDirPath: (string)
			The datadir path directly
	
	Regarding paths, determine which base path contains the cli and daemon bin.
	We also try to locate at least the default datadir directory.
	
	The intent is to use an object of this class to pass the appropriate
	values to Wallet when instantiated. This basically moves hopefully
	common initialization code out of the execution level module, whilst
	still retaining the option to make changes at that level."""
	#=============================
	
	#=============================
	# Defaults
	#=============================
	# CONVENTION: Use strings whenever feasible and typecast later.
	# Rationale: If derivative or later code gets these values from
	# somewhere else, they might end up being strings anyway.
	# Agreeing on a basic datatype makes things easier for everyone.
	defaultBasePaths = ["/usr/local/bin"]
	defaultFileBaseName = "bitcoin"
	defaultCliBinName = "{0}-cli".format(defaultFileBaseName)
	defaultDaemonBinName = "{0}d".format(defaultFileBaseName)
	defaultTxBinName = "{0}-tx".format(defaultFileBaseName)
	defaultQtBinName = "{0}-qt".format(defaultFileBaseName)
	defaultDataDirName = ".{0}".format(defaultFileBaseName)
	defaultDataDirBaseDirPath = os.path.expanduser("~")
	defaultConfigFileName = "{0}.conf".format(defaultFileBaseName)
	defaultRpcHost = "localhost"
	defaultRpcPort = "8332" # Example of string usage when it could have been int.
	#=============================
	
	def __init__(self, basePaths=defaultBasePaths, cliBinName=defaultCliBinName,\
		daemonBinName=defaultDaemonBinName, dataDirName=defaultDataDirName,\
		dataDirBaseDirPath=defaultDataDirBaseDirPath, dataDirPath=None,\
		configFileName=defaultConfigFileName, txBinName=defaultTxBinName,\
		qtBinName=defaultQtBinName, host=defaultRpcHost, port=defaultRpcPort):
		
		self.basePaths = basePaths
		self.dataDirBaseDirPath = dataDirBaseDirPath
		self.cliBinName = cliBinName
		self.daemonBinName = daemonBinName
		self.txBinName = txBinName
		self.qtBinName = qtBinName
		self.dataDirName = dataDirName
		self.configFileName = configFileName
		self.rpcHost = host
		self.rpcPort = port
		
		if dataDirPath:
			self.dataDirBaseDirPath = dataDirBaseDirPath
			self.dataDirName = dataDirName
			self.dataDirPath = dataDirPath
		else:
			dataDirPathObject = Path(self.dataDirBaseDirPath, self.dataDirName)
			self.dataDirBaseDirPath = dataDirPathObject.parent
			self.dataDirName = dataDirPathObject.name
			self.dataDirPath = str(dataDirPathObject)
	
	@property
	def cliBinPath(self):
		return self.findFile(self.cliBinName)
	
	@property
	def daemonBinPath(self):
		return self.findFile(self.daemonBinName)

	@property
	def configFilePath(self):
		return self.findFile(self.configFileName)

	def findFile(self, fileName):
		"""Locate a file given the fileName.
		Iterates through the basePaths to find the binary, otherwise uses shutil.which."""
		filePath = None
		for path in self.basePaths:
			if os.path.exists(path):
				for prospectiveFileName in os.listdir():
					if prospectiveFileName == fileName:
						filePath = os.path.join(path, fileName)
						break
		if filePath == None:
			return shutil.which(fileName)
		return filePath

class Daemons(ProcessList):
	"""A snapshot of all running wallet daemons associated with our currency.
	The format used is ProcessList.
	
	Takes:
		- nameToMatch (str): Executable name for all daemons we want to match."""
	
	def __init__(self, nameToMatch, dataDirToMatch, homeDirToMatch):
		super(self).__init__()
		self.nameToMatch = name
		self.dataDirToMatch = dataDirToMatch
		self.homeDirToMatch = homeDirToMatch
		
	@property
	def all(self):
		"""Get all daemon processes for currently running wallets for our currency."""
		if not hasattr(self, "_all"):
			self._all = type(self)(raw=False, splitArgs=True).byName(self.nameToMatch)
		return self._all
	
	@property
	def byDataDirAsArg(self):
		"""Narrow down by -datadir arg."""
	
	@property
	def byHomeDir(self):
		"""Narrow down by home dir."""
		pass#TODO

#==========================================================
# TODO: One day, this class will need to be redone. It's baggage from
# an older time with hacks all over the place. It kind of worked for mnchecker,
# but will prove to be unfit once it has to carry considerably more weight.
class BitcoinWallet(Wallet):
	
	#=============================
	"""Represents everything this script needs related to a bitcoin derived wallet."""
	#=============================
	
	#=============================
	# Wallet Strings
	# These serve to detect wallet states from stdin/stderr output of the cli executable.
	
	# This is for detecting whether the executable cli can connect to the daemon.
	# TODO: This is a hack and just BAD, especially if we should ever encounter
	# a wallet with translated error strings.
	rpcFailureMessageFragments = [\
		"error: Could not locate RPC credentials",\
		"error: couldn't connect to server"\
	]
	
	def __init__(self, config):
		
		self.config = config
		
		#=============================
		# Check path sanity.
		batchPathExistenceCheck = BatchPathExistenceCheck()
		# cliBinPath
		batchPathExistenceCheck.addPath(self.config.cliBinPath,\
			"cli-bin path: {path} (search paths: {searchPaths})"\
			.format(path=self.config.cliBinPath, searchPaths=\
				[os.path.join(path, self.config.cliBinName) for path in self.config.basePaths]))
		# daemonBinPath
		batchPathExistenceCheck.addPath(self.config.daemonBinPath,\
			"daemon-bin path: {path} (search paths: {searchPaths})"\
			.format(path=self.config.daemonBinPath, searchPaths=\
				[os.path.join(path, self.config.daemonBinName) for path in self.config.basePaths]))
		# dataDirPath
		batchPathExistenceCheck.addPath(self.config.dataDirPath,\
			"datadir path: {path}"\
				.format(path=self.config.dataDirPath))
		# configFilePath
		if not self.config.configFilePath == None:
			# A conf file path got specified; check too.
			batchPathExistenceCheck.addPath(self.config.configFilePath, "conf-file path: {path}"\
				.format(path=self.config.configFilePath))
		# Check all the paths we've specified for checking above.
		batchPathExistenceCheck.checkAll()
		# All paths are dandy, nice!
		#=============================

	@property
	def daemonRunning(self):
		
		"""Returns True if the daemon is running, False if it's not."""
		
		#TODO: This is a hacky way to determine whether the daemon is running.
		# Being reluctant to introduce third party dependencies like psutil,
		# this will have to do for now, but even this solution will need
		# an improvement in the robustness department eventually.
		
		try:
			self.runCliSafe("getblockcount")
		except WalletError as error:
			if error.code == type(error).codes.RPC_CONNECTION_FAILED:
				return False
		return True
		
	def getDaemon(self):
		"""Returns an ExternalProcess object of the daemon process.
		Returns None if no process is found."""
		#processList = ProcessList(raw=False).byName(self.config.cliBinPath).byArg("-datadir")\
			#.byArg(self.config.dataDirPath)
		
		# TODO A: Recognize datadir of process started without -datadir option.
		# Will probably need detection of HOME variable for process, just to be sure.
		#dprint(self.config.dataDirPath)
		# TODO B: What to do when multiple instances with the same datadir exist?
		# This could happen in a botched attempt to start the daemon, either by an
		# external script, manual intervention or a bug of our own.
		# TODO C: What to do if there are to instances with the same datadir, whereas
		# one has it specified through -datadir and one considers it the home dir.
		
		# NOTE: Working on these todos won't just include raising an error, but
		# providing means of resolving the problem, lest the user be left hanging
		# with a deranged setup, with no way to fix it without ripping away at the wires.
		
		# Get daemon landscape.
		# NOTE: Trash code ahead.
		daemons = self.getAllDaemonProcesses()
		daemonsWithDatadirByArg = daemons.byArgvPart(["-datadir", self.config.dataDirPath])
		if len(daemonWithDatadirByArg) == 0:
			pass#TODO
		elif len(daemonWithDatadirByArg) == 1:
			
		else:
			pass#TODO B
		
		#daemonWithDatadirbyHome = 
		
		#if len(daemonWithDatadirByArg) > 1 or len(daemonWithDatadirbyHome) > 1:
			#TODO B
		#if daemonWithDatadirByArg and daemonWithDatadirbyHome:
			#TODO C
		if daemonWithDatadirByArg:
			return daemonWithDatadirByArg
		else:
			pass#TODO
		# Debug
		dprint("env has home", "HOME" in process.env.keys())
		dprint("bitcoind name:", process.name)
		dprint("data dir path:", self.config.dataDirPath)
		dprint("process argv:", process.getArgv())
		
		return None

	def runCli(self, commandLine):
		"""Run the command line version of the wallet with a list of command line arguments."""
		if not self.config.configFilePath == None:
			return Process([self.config.cliBinPath,\
				"-datadir={datadir}".format(datadir=self.config.dataDirPath),\
				"-conf={configFilePath}".format(configFilePath=self.config.configFilePath)] + commandLine)
		else:
			return Process([self.config.cliBinPath,\
				"-datadir={datadir}".format(datadir=self.config.dataDirPath)] + commandLine)

	def runDaemon(self, commandLine):
		"""Run the daemon. Takes a list for command line arguments to it."""
		if not self.config.configFilePath == None:
			return Process([self.config.daemonBinPath,\
				"-daemon",\
				"-datadir={datadir}".format(datadir=self.config.dataDirPath),\
				"-conf={configFilePath}".format(configFilePath=self.config.configFilePath)] +commandLine)
		else:
			return Process([self.config.daemonBinPath,\
				"-daemon",\
				"-datadir={datadir}".format(datadir=self.config.dataDirPath)] +commandLine)

	def runCliSafe(self, commandLine, _retrying=False):
		
		"""A version of .runCli that checks for the wallet tripping up and responds accordingly."""
		
		process = self.runCli(commandLine)
		stdoutString, stderrString = process.waitAndGetOutput()
		
		# Catch the wallet taking the way out because the daemon isn't running.
		if any([stderrString.decode().strip().startswith(fragment)\
			for fragment in type(self).rpcFailureMessageFragments]):
			print("[DEBUG Wallet.runCliSafe WalletError: ]", WalletError.__dict__)
			raise WalletError(\
				"Command line wallet can't connect to the daemon. Is the daemon running?\n{info}"\
				.format(info="Wallet paths:\n\tcli: {cli}\n\tdaemon: {daemon}\n\tdatadir: {datadir}"\
					.format(cli=self.config.cliBinPath, daemon=self.config.daemonBinPath, datadir=self.config.dataDirPath)),\
				WalletError.codes.RPC_CONNECTION_FAILED)
		
		# Catch issues caused by the wallet connecting to the daemon right after the daemon started.
		# As this involves retrying, we have to make sure we don't get stuck retrying forever.
		if "error code: -28" in stdoutString.decode()\
			or "error code: -28" in stderrString.decode()\
			and not _retrying:
			# Rerun this method in intervals until it works, or we decide to give up.
			for retry in range(1,16):
				time.sleep(5)
				retriedProcess = self.runCliSafe(commandLine, _retrying=True)
				retriedStdoutString, retriedStderrString = retriedProcess.waitAndGetOutput()
				if "error code: -28" in retriedStdoutString.decode()\
					or "error code: -28" in retriedStderrString.decode():
					continue
				else:
					return retriedProcess
			raise WalletError("Daemon stuck at error -28.", WalletError.codes.DAEMON_STUCK)
		
		return process

	def runDaemonSafe(self, commandLine):
		"""A version of .runDaemon that checks for the daemon tripping up and responds accordingly."""
		process = self.runDaemon(commandLine)
		stdoutString, stderrString = process.waitAndGetOutput()
		#TODO: Make running the daemon safer and failures more verbose with some checks & exceptions.
		return process

	def startDaemon(self, commandLine=[]):
		"""Start the daemon. Takes a list for command line arguments."""
		return self.runDaemon(commandLine)

	def stopDaemon(self, waitTimeout):
		"""Stop the daemon.
		The parameter 'waitTimeout' determines for how long we will wait and poll
		for stop confirmation, in seconds."""
		process = self.runCliSafe(["stop"])
		# Wait and poll every second for daemon shutdown completion.
		# Return once daemon shut down is confirmed.
		if not waitTimeout == None:
			for second in range(1,waitTimeout):
				try:
					self.getBlockCount() # We could use anything. This will do.
				except WalletError as error:
					if error.code == WalletError.codes.RPC_CONNECTION_FAILED:
						break # The client is finally erroring out on the connection. Success.
				time.sleep(1)
		return process

	def deleteBlockchainData(self):
		for fileName in ["blocks", "chainstate", "database", "mncache.dat", "peers.dat",\
			"mnpayments.dat", "banlist.dat"]:
			filePath = os.path.join(self.config.dataDirPath, fileName)
			try:
				if os.path.exists(filePath):
					if os.path.isdir(filePath):
						shutil.rmtree(filePath)
					else:
						os.remove(filePath)
			except OSError:
				pass

	def getBlockCount(self):
		stdout, stderr = self.runCliSafe(["getblockcount"]).waitAndGetOutput(timeout=8)
		blockCount = stdout.decode()
		if not stderr.decode() == "":
			print("stderr ", stderr.decode(), "||", stdout.decode())
			raise WalletError(\
				"The wallet produced an error when running \"getblockcount\":\n {error}"\
					.format(error=stderr.decode()), WalletError.codes.CLI_ERROR)
		return int(blockCount)

#=======================================================================================
# Actions
#=======================================================================================

#==========================================================
#BEGIN# Action: info

#=============================
class InfoAction(Action):
	
	#=============================
	"""Provides various details about the setup."""
	#=============================
	
	def run(self):
		return ActionReturnValue(self.data.Config())
	
#END#
#==========================================================

#==========================================================
#BEGIN# Action: cli

class CliActionReturnValue(ActionReturnValue):
	@property
	def _repr_str_(self):
		return "{stdout}{stderr}"\
			.format(stdout=self.raw.stdout.decode(), stderr=self.raw.stderr.decode())

class CliAction(Action):
	
	#=============================
	"""Takes command line arguments for the wallet executable and runs it with them."""
	#=============================
	
	def run(self):
		wallet = Wallet(self.data.Config())
		return CliActionReturnValue(wallet.runCliSafe(\
			self.data.args.args).waitAndGetOutput(timeout=180))
#END#
#==========================================================


#==========================================================
#BEGIN# Actions: Daemon related

class DaemonActionReturnValue(CliActionReturnValue): pass

class StartDaemonAction(Action):
	#=============================
	"""Start the Daemon."""
	#=============================
	
	def run(self):
		wallet = Wallet(self.data.Config())
		return DaemonActionReturnValue(wallet.startDaemon(\
			self.data.args.args).waitAndGetOutput(timeout=180))

class StopDaemonAction(Action):
	
	#=============================
	"""Stops the daemon."""
	#=============================
	
	def run(self):
		wallet = Wallet(self.data.Config())
		return DaemonActionReturnValue(wallet.stopDaemon(\
			self.data.args.stopDaemonTimeout)\
			.waitAndGetOutput(timeout=self.data.args.stopDaemonTimeout))

class ReindexAction(Action):
	
	#=============================
	"""Runs the wallet with -reindex.
	
	Wraps around StopDaemonAction and CliAction and returns accordingly."""
	#=============================
	
	def run(self):
		
		returnValues = ActionReturnValueAggregate()
		
		# Try to stop wallet.
		# TODO: This is extremely crude. A proper check for whether the wallet
		# is running or not needs to be established.
		# For example, this would likely fail if the RPC details were changed in
		# the wallet's config during daemon runtime: The cli client would use the
		# new details, but the daemon would still be initialized with the old
		# ones. Result: RPC connection failure.
		try:
			returnValues.addReturnValue(StopDaemonAction(handle=self.handle, data=self.data).run())
		except WalletError:
			pass
	
		# Spoof -reindex into the args Namespace for the StartDaemonAction
		# to start the daemon with -reindex.
		modifiedData = self.data
		modifiedData.args.args.insert(0, "-reindex")
		returnValues.addReturnValue(StartDaemonAction(handle=self.handle,\
			data=modifiedData).run())
		
		return returnValues
	
##END#
##==========================================================

#==========================================================
# Register of all above defined actions.
#==========================================================
class BitcoinActions(Actions):
	def setUp(self):
		super().setUp()
		self.add("cli", CliAction)
		self.add("stop", StopDaemonAction)
		self.add("info", InfoAction)
		self.add("reindex", ReindexAction)
		self.add("start", StartDaemonAction)
		
	def setUpUninheritable(self):
		pass

#=======================================================================================
# Arguments
#=======================================================================================

#==========================================================
# Argument Base Setups (for subclassing further below)
#==========================================================

#==========================================================
class NodeNameParserSetup(ParserSetup):
	
	#=============================
	"""Many actions will be specific to some node.
	That node is identified by its datadir."""
	#=============================
	
	def setUp(self):
		self.parser.add_argument("-i", "--identifier", dest="identifier", default=None,\
			help="Specify the node you'd like to operate on."
			"To do so, use the suffix for the appropriate datadir.",\
			metavar="DATADIR_SUFFIX")

#==========================================================
# Node-Independent arguments.
# (no dependency on NodeNameParserSetup)
#==========================================================

# -

#==========================================================
# NodeNameParserSetup dependent arguments.
#==========================================================

#==========================================================
class CliParserSetup(NodeNameParserSetup):
	
	#=============================
	"""ParserSetup for the "cli" Action."""
	#=============================
	
	@property
	def help(self):
		return "Arguments to the command line application."
	
	def setUp(self):
		self.parser.add_argument("args", nargs="*",\
			help=self.help)

#==========================================================
class StopParserSetup(NodeNameParserSetup):
	
	#=============================
	"""ParserSetup for the "stop" Action."""
	#=============================
	
	def setUp(self):
		defaultTimeout = 180
		self.parser.add_argument("--timeout", dest="stopDaemonTimeout",\
			help="For how many seconds to wait for the daemon to stop until we give up in "
			"case it hangs. Default: {0}".format(defaultTimeout), metavar="SECONDS",\
				default=defaultTimeout)

#==========================================================
class StartDaemonParserSetup(CliParserSetup):
	@property
	def help(self):
		return "Startup arguments to the daemon."
	
#==========================================================
class ReindexDaemonParserSetup(CliParserSetup, StopParserSetup):
	@property
	def help(self):
		return "Startup arguments to the daemon (besides -reindex)."

#==========================================================
class BitcoinArgumentSetup(ArgumentSetup):
	def setUp(self):
		super().setUp()
		CliParserSetup(self.addSubParser("cli"))
		StopParserSetup(self.addSubParser("stop"))
		StartDaemonParserSetup(self.addSubParser("start"))
		ReindexDaemonParserSetup(self.addSubParser("reindex"))
		self.addSubParser("info")

#=======================================================================================
# Exports
#=======================================================================================

Config = BitcoinConfig
Wallet = BitcoinWallet
ArgumentSetup = BitcoinArgumentSetup
Actions = BitcoinActions
