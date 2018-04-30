#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Builtins
import os
import shutil
import time

# Local
from lib.currencies import CurrencyConfig, Wallet, WalletError, DaemonStuckError
from lib.arguments import ArgumentSetup, ParserSetup
from lib.actions import Action, Actions, ActionReturnValue
from lib.filesystem import BatchPathExistenceCheck
from lib.processing import Process

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
	defaultConfigFileName = "{0}.conf".format(defaultFileBaseName)
	defaultRpcHost = "localhost"
	defaultRpcPort = "8332" # Example of string usage when it could have been int.
	#=============================
	
	def __init__(self, basePaths=defaultBasePaths, cliBinName=defaultCliBinName,\
		daemonBinName=defaultDaemonBinName, dataDirName=defaultDataDirName,\
		configFileName=defaultConfigFileName, txBinName=defaultTxBinName,\
		qtBinName=defaultQtBinName, host=defaultRpcHost, port=defaultRpcPort):
		self.basePaths = basePaths
		self.cliBinName = cliBinName
		self.daemonBinName = daemonBinName
		self.txBinName = txBinName
		self.qtBinName = qtBinName
		self.dataDirName = dataDirName
		self.configFileName = configFileName
		self.rpcHost = host
		self.rpcPort = port
	
	@property
	def cliBinPath(self):
		return self.findFile(self.cliBinName)
	
	@property
	def daemonBinPath(self):
		return self.findFile(self.daemonBinName)

	@property
	def configFilePath(self):
		return self.findFile(self.configFileName)

	@property
	def dataDirPath(self):
		return os.path.join(os.path.expanduser("~"), self.dataDirName)

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

#==========================================================
class BitcoinWallet(Wallet):
	
	#=============================
	"""Represents everything this script needs related to a bitcoin derived wallet."""
	#=============================
	
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
		if stderrString.decode().strip() == "error: couldn't connect to server":
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
			raise DaemonStuckError("Daemon stuck at error -28.")
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
	def string(self):
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
#BEGIN# Action: cli

class StopAction(Action):
	
	#=============================
	"""Stops the daemon."""
	#=============================
	
	def run(self):
		wallet = Wallet(self.data.Config())
		return CliActionReturnValue(wallet.stopDaemon(\
			self.data.args.stopDaemonTimeout)\
			.waitAndGetOutput(timeout=self.data.args.stopDaemonTimeout))

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

class ReindexAction(Action):
	
	#=============================
	"""Runs the wallet with -reindex.
	
	Wraps around StopAction and CliAction and returns accordingly."""
	#=============================
	
	def run(self):
		stopReturnValue = StopAction(handle=self.handle, data=self.data).run()
		modifiedData = self.data
		modifiedData.args.args.insert(0, "-reindex")
		startReturnValue = StartDaemonAction(handle=self.handle, data=modifiedData).run()
		return CliActionReturnValue("\n".join([stopReturnValue.raw, startReturnValue.raw]))
		#TODO: Use ActionReturnValueAggregate instead of the above.
		

##END#
##==========================================================

#==========================================================
# Register of all above defined actions.
#==========================================================
class BitcoinActions(Actions):
	def setUp(self):
		super().setUp()
		self.add("cli", CliAction)
		self.add("stop", StopAction)
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