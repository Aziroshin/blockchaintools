#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

# Python.
from collections import namedtuple, UserList
from subprocess import Popen, PIPE
from pathlib import Path
import os

from lib.debugging import dprint #NOTE: DEBUG

#=======================================================================================
# Datatypes
#=======================================================================================

ProcessOutput = namedtuple("ProcessOutput", ["stdout", "stderr"], verbose=False, rename=False)
# SplitPair
SplitPair = namedtuple("SplitPair", ["key", "value"], verbose=False, rename=False)
UnsplitPair = namedtuple("UnsplitPair", ["key"], verbose=False, rename=False)
# SplitVar
SplitVar = namedtuple("SplitVar", ["var", "value"], verbose=False, rename=False)
UnsplitVar = namedtuple("UnsplitVar", ["var"], verbose=False, rename=False)
# SplitArg
SplitArg = namedtuple("SplitArg", ["param", "value"], verbose=False, rename=False)
UnsplitArg = namedtuple("UnsplitArg", ["param"], verbose=False, rename=False)

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

#==========================================================
class Process(object):

	#=============================
	"""Represents a system process started by this script.
	Note: Refrain from calling .communicate() directly on the process from outside of this object."""
	#=============================

	def __init__(self, commandLine, run=True):
		self.commandLine = commandLine
		if run == True:
			self.run()
		self._communicated = False
		self._stdout = None
		self._stderr = None

	def run(self):
		self.process = Popen(self.commandLine, stdout=PIPE, stderr=PIPE)
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
		"""Return type(self) object of all processes"""
		return type(self)(processes=\
			[p for p in self if p.inArg(argPart, raw=raw, splitArgs=True)],\
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
	
	"""Equal-sign separated key/value pair in its split and unsplit form."""
	
	def __init__(self, value, raw, SplitType, UnsplitType):
		self.value = value
		self.raw = raw
		self.SplitType = SplitType
		self.UnsplitType = UnsplitType
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
			return self.UnsplitType(self.value)

#=========================================================
class KeyValueData(object):
	
	"""A set of equal-sign separated key/value pairs in their split and unsplit forms.
	.split returns a list of SplitPair(key, value) and UnsplitPair(key)."""
	
	SplitType = SplitPair
	UnsplitType = UnsplitPair
	
	def __init__(self, data, raw):
		self.data = data
		self.raw = raw
		
	@property
	def unsplit(self):
		return self.data
		
	@property
	def split(self):
		"""Returns a list with all key/value pairs split by equal sign, where applicable.
		Doesn't split if the left hand side includes non-alphanumeric characters, except
		dashes, in order not to mess with quoted strings, shell variables and subshells, etc."""
		data = []
		for pair in self.data:
			for element in Pair(pair, self.raw, type(self).SplitType, type(self).UnsplitType).split:
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

#=========================================================
class ExternalLinuxProcess(object):
	
	#=============================
	"""A Linux process that may or may not have been started by this program.
	
	This is implemented as a live wrapper around /proc.
	
	The basic assumption is that the process was originally started by something
	else, thus some functionality one could expect from the Process class will
	not be available."""
	#=============================
	
	def __init__(self, pid, raw=False, splitArgs=False):
		self.info = LinuxProcessInfo(pid)
		self.rawDefaultSetting = raw
		self.splitArgsDefaultSetting = splitArgs
	
	#=============================
	# Default overriders
	
	def raw(self, override):
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
		
	#=============================
	
	def _typeString(self, byteString, raw=None):
		
		"""Make sure the specified string is ether bytes or str as specified.
		
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
	
	def getName(self, raw=None):
		"""Name of the process without arguments."""
		return self._typeString(self.info.comm, raw=self.raw(raw))
	
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
		"""Is the specified arg in the processes argv?
		Returns True if it is, False if it's not."""
		return arg in self.getArgv(raw=self.raw(raw), splitArgs=self.splitArgs(splitArgs), withComm=False)

	def inArg(self, string, raw=None, splitArgs=None):
		"""Is the specified substring in one of the args in argv?
		Returns True if it is, False if it's not."""
		return any([arg for arg in self.getArgv(raw=self.raw(raw), splitArgs=self.splitArgs(splitArgs)) if string in arg])

# TODO: Windows/MacOS X support, if that should ever
# be required.
# Towards that end, these variables should later become factories/metaclassed
# classes that determine the platform and return the appropriate class.
ProcessList = LinuxProcessList
ExternalProcess = ExternalLinuxProcess
