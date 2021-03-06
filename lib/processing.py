#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Python.
from collections import namedtuple, UserList, UserDict
from subprocess import Popen, PIPE
from pathlib import Path
from pwd import getpwuid
from grp import getgrgid
import os
import sys

# Debug
from lib.debugging import dprint #NOTE: DEBUG

#=======================================================================================
# Datatypes
#=======================================================================================

# collections.namedtuple changed from Python version 3.6 to 3.7:
# In 3.6, "verbose" can be directly passed to the constructor, in 3.7, that has
# to be done by means of the "defaults" argument. This is a hack-around to ensure
# compatibility with 3.6 and beyond.
if sys.version_info.minor <= 6:
	_dataTypesConfig = {"verbose": False, "rename": False}
else:
	_dataTypesConfig = {"defaults": {"verbose": False}, "rename": False}

TestTuple = namedtuple("TestTuple", "a b")
ProcessOutput = namedtuple("ProcessOutput", "stdout stderr")
# SplitPair
SplitPair = namedtuple("SplitPair", "key value")
UnsplitPair = namedtuple("UnsplitPair", "key")
# SplitVar
SplitVar = namedtuple("SplitVar", "var value")
UnsplitVar = namedtuple("UnsplitVar", "var value")
# SplitArg
SplitArg = namedtuple("SplitArg", "param value")
UnsplitArg = namedtuple("UnsplitArg", "param")
# Proc status
ProcStatus = namedtuple("ProcStatus", "name data")
# Proc status: UID & GUID
ProcStatusPerms = namedtuple("ProcStatusPerms", "real effective savedSet filesystem")

#=======================================================================================
# Library
#=======================================================================================

#=========================================================
# Errors
#=========================================================

class NoSuchProcessError(Exception): pass

#=========================================================
# Internal Processes
#=============================
# processes that we start
#=========================================================

#=========================================================
class Process(object):
	
	#=============================
	"""Represents a system process started by this script.
	Note: Refrain from calling .communicate() directly on the process from outside of this object."""
	#=============================
	
	def __init__(self, commandLine, run=True, env=None):
		
		self.commandLine = commandLine
		
		if run == True:
			self.run()
		self._communicated = False
		self._stdout = None
		self._stderr = None
		
		if not env is None:
			self.env = os.environ.copy()
			self.env.update(env)
		else:
			self.env = os.environ.copy()
			
	def run(self):
		self.process = Popen(self.commandLine, env=self.env, stdout=PIPE, stderr=PIPE)
		return self.process
	
	def waitAndGetOutput(self, timeout=None):
		if not self._communicated:
			self._stdout, self._stderr = self.process.communicate(timeout=timeout)
			self._communicated = True
		return ProcessOutput(self._stdout, self._stderr)
	
	def waitAndGetStdout(self, timeout=None):
		return self.waitAndGetOutput(timeout).stdout
	
	def waitAndGetStderr(self, timeout=None):
		return self.waitAndGetOutput(timeout).stderr

#=========================================================
# Internal Processes
#=============================
# Processes started by things outside our scope.
#=========================================================

#=========================================================
class LinuxProcessList(UserList):
	
	#=============================
	"""A handle to listing the processes running on a machine."""
	#=============================
	
	def __init__(self, processes=[], initWithAll=True, raw=False, splitArgs=False):
		# If you want to change raw and splitArgs defaults, you might also want to
		# change them in self.getAll and ExternalLinuxProcess.__init__.
		super().__init__(processes)
		self.initWithAll = initWithAll
		if not self and initWithAll:
			self.data = self.data+self.getAll(raw=raw, splitArgs=splitArgs)
		
	def getAllPids(self):
		"""Return the PIDs of all running processes as integers."""
		return [path.name for path in Path("/proc").iterdir() if str(path.name).isdigit()]
	
	def getAll(self, raw=False, splitArgs=False):
		"""Get a list of ExternalLinuxProcess objects for all running processes."""
		processes = []
		for pid in self.getAllPids():
			try:
				processes.append(ExternalLinuxProcess(pid, raw=raw, splitArgs=splitArgs))
			except NoSuchProcessError:
				pass
		return processes
	
	def byPid(self, pid):
		"""Returns the process matching the specified PID."""
		return type(self)(processes=\
			[p for p in self if p.pid == pid],\
			initWithAll=False)
	
	def byName(self, name, raw=None):
		"""Return type(self) object of all processes matching the specified name."""
		return type(self)(processes=\
			[p for p in self if p.getName(raw=raw) == name],\
			initWithAll=False)
	
	def byPath(self, path, raw=None):
		"""Return type(self) object of all processes matching the specified path.
		Path in this case refers to the path of the executable, represented
		as the first element of the processes' argv."""
		return type(self)(processes=\
			[p for p in self if p.getPath(raw=raw) == path],\
			initWithAll=False)
	
	def byArg(self, arg, raw=None, splitArgs=None):
		"""Return type(self) object of all processes having the specified argument."""
		return type(self)(processes=\
			[p for p in self if p.hasArg(arg, raw=raw, splitArgs=splitArgs)],\
			initWithAll=False)
			
	def byArgPart(self, argPart, raw=None):
		"""Return type(self) object of all processes with this substring in one of their args."""
		return type(self)(processes=\
			[p for p in self if p.inArg(argPart, raw=raw, splitArgs=True)],\
			initWithAll=False)
	
	def byArgvPart(self, argvPart, raw=None, splitArgs=None):
		"""Return type(self) object of all processes with the specified argv subset."""
		return type(self)(processes=\
			[p for p in self if p.inArgv(argvPart, raw=raw, splitArgs=splitArgs)],\
			initWithAll=False)
	
	def byHome(self, home):
		"""Return type(self) object of all processes with the specified home dir path."""
		return type(self)(processes=\
			[p for p in self if p.home == home],\
			initWithAll=False)

#TODO #NOTE: The list isn't live, but the processes are. This needs to change.

#=========================================================
class LinuxProcessInfo(object):
	
	#=============================
	"""A static representation of /proc process information for a process.
	Represents the state of the process found upon instantiation (not live).
	If the process is found to be dead during init, raises NoSuchProcessError.
	If permission issues are encountered during init, None for the fields
	in question.
	"""
	#=============================
	
	def __init__(self, pid):
		self.pid = pid
		# Get info from /proc.
		try:
			self.cmdline = self._readProc(["cmdline"])
			self.comm = self._readProc(["comm"])
			self.cwd = self._resolveSymlink(["cwd"])
			self.environ = self._readProc(["environ"])
			self.status = self._readProc(["status"])
		except FileNotFoundError:
			raise NoSuchProcessError("A process with the PID {0} doesn't exist (anymore?)."\
				.format(self.pid))
		
	def _readProc(self, pathElements):
		"""Read a /proc/<self.pid> process file by its name."""
		try:
			with Path("/proc", self.pid, *pathElements).open("rb") as procFile:
				return procFile.read()
		except PermissionError:
			return None
		
	def _resolveSymlink(self, pathElements):
		try:
			return os.path.realpath(Path("/proc", self.pid, *pathElements))
		except PermissionError:
			return None

#=========================================================
class Pair(object):
	
	"""Equal-sign separated key/value pair in its split and unsplit form.
	
	Takes:
		- value: Bytestring or string potentially containing an equal sign separated
		  key/value pair.
		- raw: True value is a bytestring, False for string.
		- unsplitFiller (None): If not None, .split uses the value specified here for
		  a substitute if value is either not an equal sign separated key/value pair
		  or doesn't contain an rvalue.
		  A KeyValueDataError is raised if the UnsplitType for this class
		  doesn't take at least two items."""
	#NOTE: Consider merging Pair into KeyValueData. Too much redundancy.
	
	def __init__(self, value, raw, SplitType, UnsplitType, unsplitFiller=None):
		self.value = value
		self.raw = raw
		self.SplitType = SplitType
		self.UnsplitType = UnsplitType
		self.unsplitFiller = unsplitFiller
		if self.raw:
			self.equalSign = b"="
		else:
			self.equalSign = "="
	
	@property
	def split(self):
		"""If applicable, splits the pair by equal sign and returns the specified SplitType.
		Otherwise, returns UnsplitType with the entire argument as its one value."""
		key, value = self.value.partition(self.equalSign)[0::2]
		if value:
			return self.SplitType(key, value)
		else:
			if self.unsplitFiller is None:
				return self.UnsplitType(self.value)
			else:
				try:
					return self.UnsplitType(self.value, self.unsplitFiller)
				except TypeError:
					raise KeyValueDataError(\
						"When unsplitFiller is specified, UnsplitType needs to have a size of 2."
						"Type that caused the error: {Type}".format(Type=self.UnsplitType.__name__))

#=========================================================
class KeyValueDataError(Exception): pass

#=========================================================
class KeyValueData(object):
	
	"""A set of equal-sign separated key/value pairs in their split and unsplit forms.
	.split returns a list of SplitPair(key, value) and UnsplitPair(key).
	
	There are two important class attributes you might want to consider when subclassing:
		- SplitType (SplitPair): A 2-tuple returned by .split for elements in the specified
		  data list that could be split.
		- UnsplitType (UnsplitPair): A tuple of either size 1 or 2. Size 2 is required when
		  unsplitFiller is specified. Is used for the return value of .split for
		  elements of the specified data list that couldn't be split.
	This class is designed with namedtuples in mind.
	
	Takes:
		- data: List potentally containing equal-sign separated key-value pairs.
		- raw: True if data is in bytestrings, False for strings.
		- unsplitFiller (None): If not None, substitutes the missing value of data elements
		  that either have no equal sign or no rvalue with what's specified for this
		  parameter. A KeyValueDataError is raised if the UnsplitType for this class
		  doesn't take at least two items."""
	
	SplitType = SplitPair
	UnsplitType = UnsplitPair
	
	def __init__(self, data, raw, unsplitFiller=None):
		self.data = data
		self.raw = raw
		self.unsplitFiller = unsplitFiller
		
	@property
	def unsplit(self):
		"""Get the unsplit data this object was initialized with."""
		return self.data
		
	@property
	def split(self):
		"""Returns a list with all key/value pairs split by equal sign, where applicable.
		Doesn't split if the left hand side includes non-alphanumeric characters, except
		dashes, in order not to mess with quoted strings, shell variables and subshells, etc."""
		data = []
		for pair in self.data:
			
			for element in\
			Pair(pair, self.raw, type(self).SplitType, type(self).UnsplitType,\
			unsplitFiller=self.unsplitFiller).split:
				
				data.append(element)
				
		return data

#=========================================================
class Argv(KeyValueData):
	
	"""The argv of a process, optionally with equal sign seperated args split.
	.split returns a list of splitArg(param, value) and UnsplitArg(param)."""
	
	SplitType = SplitArg
	UnsplitType = UnsplitArg
	
	def __init__(self, data, raw, withComm=True):
		if not withComm: data.pop(0)
		super().__init__(data, raw)
		
#=========================================================
class Env(KeyValueData):
	
	"""The environment vars of a process, optionally with equal sign separated vars split.
	.split returns a list of SplitVar(var, value) and UnsplitVar(var)."""
	
	SplitType = SplitVar
	UnsplitType = UnsplitVar
	
	def __init__(self, data, raw):
		super().__init__(data, raw, unsplitFiller="")

#=========================================================
class LinuxProcessStatus(UserDict):
	
	def __init__(self, procData, raw, multisAreLists=True):
		super().__init__(self)
		self.procData = procData
		self.raw = raw
		if multisAreLists:
			self.data = self.stringDictMultisAreLists
		else:
			if self.raw is True:
				self.data = self.rawDict
			elif self.raw is False:
				self.data = self.stringDict
	
	@property
	def dataLines(self):
		"""List of every line found in the status output."""
		return self.procData.split(b"\n")
		
	@property
	def dataPairs(self):
		"""List of key/value pairs per line."""
		return [ProcStatus(*line.partition(b":\t")[0::2]) for line in self.dataLines]
	
	@property
	def dataPairsAllAreLists(self):
		"""List of key/value pairs per line where lines with multiple values have them listed."""
		return [ProcStatus(pair[0], pair[1].strip(b"\x00").split(b"\t")) for pair in self.dataPairs]
	
	@property
	def dataPairsMultisAreLists(self):
		"""Like dataPairsAllTuples, but only status values with more than one item are listed."""
		pairs = []
		for pair in self.dataPairsAllAreLists:
			if len(pair[1]) > 1:
				pairs.append(pair)
			else:
				pairs.append(ProcStatus(pair[0], pair[1][0]))
		return pairs
	
	@property
	def rawDict(self):
		"""Pairs sorted into a dict in their raw bytes() form."""
		return {pair.name: pair.data for pair in self.dataPairsMultisAreLists}
		
	@property
	def stringDict(self):
		"""Pairs sorted into a dict in string form."""
		return {pair.name.decode(): b"\t".join(pair.data).decode() for pair in self.dataPairsAllAreLists}
	
	@property
	def stringDictMultisAreLists(self):
		"""Dict with str() keys, the values being str(), except multi-field ones, they're lists."""
		return {pair.name.decode(): self.stringify(pair.data) for pair in self.dataPairsMultisAreLists}
	
	def stringify(self, statusData):
		"""If value is ProcStatus(), returns stringified ProcStatus(). Else, str() (former bytes()).
		This is a "magic" method to produce a dict with string keys, and string values if they're
		single column values in /proc/*/status, or list values for multi column ones."""
		if type(statusData) is list:
			return [s.decode() for s in statusData]
		else:
			return statusData.decode()
			
	
#=========================================================
class ExternalLinuxProcess(object):
	
	#=============================
	"""A Linux process that may or may not have been started by this program.
	
	This is implemented as a live wrapper around /proc.
	
	The basic assumption is that the process was originally started by something
	else, thus some functionality one could expect from the Process class will
	not be available.
	
	Takes:
		- pid: PID of the process.
		- raw (False): True for bytestring, False for string.
		- splitArgs (False): True to split args by equal sign by default when applicable.
		- splitVars (False): True to split env. vars. by equal sign by default when applicable."""
	#=============================
	
	def __init__(self, pid, raw=False, splitArgs=False, splitVars=False):
		self.info = LinuxProcessInfo(pid)
		self.rawDefaultSetting = raw
		self.splitArgsDefaultSetting = splitArgs
		self.splitVarsDefaultSetting = splitVars
	
	#=============================
	# BEGIN: COMMON
	# Convenience properties which wrap around getter functions, returning their value
	# in whatever is the resulting default considering our configuration (say, for 'raw').
	@property
	def pid(self):
		return self.getPid()
	
	@property
	def name(self):
		return self.getName()
		
	@property
	def path(self):
		return self.getPath()
	
	@property
	def env(self):
		return self.getEnvDict()
	
	@property
	def status(self):
		return LinuxProcessStatus(self.info.status, raw=self.raw())
	
	@property
	def uids(self):
		"""Named tuple of Uids: (real, effective, savedSet, filesystem)."""
		return ProcStatusPerms(*self.status["Uid"])
	
	@property
	def gids(self):
		"""Named tuple of Gids: (real, effective, savedSet, filesystem)."""
		return ProcStatusPerms(*self.status["Gid"])
	
	@property
	def users(self):
		"""Named tuple of user names: (real, effective, savedSet, filesystem)."""
		return ProcStatusPerms(*[getpwuid(p).pw_name for p in self.uids])
	
	@property
	def groups(self):
		"""Named tuple of group names: (real, effective, savedSet, filesystem)."""
		return ProcStatusPerms(*[getgrgid(p).gr_name for p in self.gids])
	
	@property
	def home(self):
		"""If set, returns $HOME. Otherwise, returns home dir path of the effective UID."""
		try:
			return self.getEnvDict()["HOME"]
		except KeyError:
			return getpwuid(self.uid.effective).pw_dir
		
	# END: COMMON
	#=============================
	
	#=============================
	# Default overriders
	
	def raw(self, override=None):
		"""Returns "raw" as set for the constructor if override is None, otherwise returns override."""
		if override is None:
			return self.rawDefaultSetting
		else:
			return override
	
	def splitArgs(self, override):
		if override is None:
			return self.splitArgsDefaultSetting
		else:
			return override
	
	def splitVars(self, override):
		if override is None:
			return self.splitVarsDefaultSetting
		else:
			return override
		
	#=============================
	
	def _typeString(self, byteString, raw=None):
		
		"""Make sure the specified string is either bytes or str as specified.
		
		Takes bytes(), determines whether we're currently configured to cast
		bytes() into str() and returns accordingly.
		
		If instructed to return non-raw, we will strip the trailing newline."""
		
		if self.raw(raw):
			return byteString
		else:
			return byteString.decode().rstrip("\n")
		
	def _typeList(self, byteStringList, raw=None):
		
		"""Make sure the specified list is either made up of bytes or str as specified.
		
		Takes a list of bytes(), determines whether we're currently configured to cast
		bytes() into str() and return the list with its elements changed accordingly."""
		
		if self.raw(raw):
			return byteStringList
		else:
			return [byteString.decode() for byteString in byteStringList]
	
	def getStatus(self, raw=None):
		""""""
		return {s for s in self.info.status.split(r'\n')}
	
	def getName(self, raw=None):
		"""Name of the process without arguments."""
		return Path(self.getPath(raw=raw)).name
	
	def getPath(self, raw=None):
		"""Executable path as it's found in the first element of the argv."""
		return self.getArgv(raw=self.raw(raw))[0]
	
	def getPid(self):
		"""PID of the process. Returns as int."""
		return int(self.info.pid)
	
	def getArgvSplitByNul(self, raw=None):
		"""List of arguments used to start the process, starting with the command name.
		Args are split into a list by NUL."""
		return self._typeList(self.info.cmdline.strip(b"\x00").split(b"\x00"), raw=self.raw(raw))
	
	def getEnvSplitByNul(self, raw=None):
		return self._typeList(self.info.environ.strip(b"\x00").split(b"\x00"), raw=self.raw(raw))
	
	def getArgv(self, raw=None, splitArgs=None, withComm=True):
		
		"""List of arguments used to start the process, optionally starting with the command name.
		Args are split into a list by NUL, and, optionally, by equal sign."""
		
		argv = Argv(self.getArgvSplitByNul(raw=self.raw(raw)), raw=self.raw(raw), withComm=withComm)
		if self.splitArgs(splitArgs):
			return argv.split
		else:
			return argv.unsplit
	
	def getEnv(self, raw=None, splitVars=None):
		
		"""List of environment variables.
		Args are split into a list by NUL, and, optionally, by equal sign."""
		
		env = Env(self.getEnvSplitByNul(raw=self.raw(raw)), raw=self.raw(raw))
		if self.splitVars(splitVars):
			return env.split
		else:
			return env.unsplit
		
	def getEnvDict(self, raw=None):
		
		"""Dict of environment variables in key/value pairs."""
		# We assume that every environment variable is a key value pair.
		# This explodes otherwise.
		
		envDict = {}
		env = self.getEnv(raw=self.raw(raw), splitVars=True)
		envIndex = 0
		while envIndex < len(env):
			envDict[env[envIndex]] = env[envIndex+1]
			envIndex += 2
		return envDict
	
	def hasArg(self, arg, raw=None, splitArgs=None):
		"""Is the specified arg in the processes argv?"""
		return arg in self.getArgv(raw=self.raw(raw), splitArgs=self.splitArgs(splitArgs), withComm=False)

	def hasEnvVar(self, varName):
		"""Is the specfied env var in the env of the process?"""
		return varName in self.env.keys()
	
	def hasEnvPair(self, varName, varValue, raw=None):
		"""Is the given varName/varValue pair in env?"""
		envDict = self.getEnvDict(raw=None)
		if varName in envDict and envDict[varName] == varValue:
			return True
		else:
			return False
	
	def inArg(self, string, raw=None, splitArgs=None):
		"""Is the specified substring in one of the args in argv?
		Returns True if it is, False if it's not."""
		return any([arg for arg in self.getArgv(raw=self.raw(raw), splitArgs=self.splitArgs(splitArgs)) if string in arg])
	
	def inArgv(self, matchArgs, raw=None, splitArgs=None):
		"""Is matchArgs a subset of argv?"""
		argv = self.getArgv(raw=raw, splitArgs=splitArgs)
		argvIndex = 0
		for arg in argv:
			matchIndex = 0
			for matchArg in matchArgs:
				try:
					if not argv[argvIndex+matchIndex] == matchArg:
						break
					else:
						matchIndex += 1
				except IndexError:
					return False # We've looped through all of argv without a match and overstepped.
				if matchIndex == len(matchArgs)-1:
					return True # matchArgs is a subset of argv.
			argvIndex += 1
		return False # We've looped through all of argv without a match and didn't overstep.
	
# TODO: Windows/MacOS X support, if that should ever
# be required.
# Towards that end, these variables should later become factories/metaclassed
# classes that determine the platform and return the appropriate class.
ProcessList = LinuxProcessList
ExternalProcess = ExternalLinuxProcess
