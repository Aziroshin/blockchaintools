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
	
	def __init__(self, processes=[], initWithAll=True, raw=False):
		super().__init__(processes)
		if not self and initWithAll:
			self.data = self.data+self.getAll()
		self.rawDefaultSetting = raw
	
	def raw(self, override):
		"""Returns "raw" as set for the constructor if override is None, otherwise returns override."""
		if override is None:
			return self.rawDefaultSetting
		else:
			return override
		
	def getAllPids(self):
		"""Return the PIDs of all running processes as integers."""
		return [path.name for path in Path("/proc").iterdir() if str(path.name).isdigit()]
	
	def getAll(self):
		"""Get a list of ExternalLinuxProcess objects for all running processes."""
		processes = []
		for pid in self.getAllPids():
			try:
				processes.append(ExternalLinuxProcess(pid))
			except NoSuchProcessError:
				pass
		return processes
	
	def byName(self, name, raw=None):
		"""Return type(self) object of all processes matching the specified name."""
		return type(self)(processes=\
			[p for p in self if p.getName(raw=self.raw(raw)) == name],\
			initWithAll=False)
	
	def byPath(self, path, raw=None):
		"""Return type(self) object of all processes matching the specified path.
		Path in this case refers to the path of the executable, represented
		as the first element of the processes' argv."""
		return type(self)(processes=\
			[p for p in self if p.getPath(raw) == path],\
			initWithAll=False)
	
	def byArg(self, arg, raw=None):
		"""Return type(self) object of all processes having the specified argument."""
		return type(self)(processes=\
			[p for p in self if p.hasArg(arg, raw=self.raw(raw))],\
			initWithAll=False)
			
	def byArgPart(self, argPart, raw=None):
		"""Return type(self) object of all processes"""
		return type(self)(processes=\
			[p for p in self if p.inArg(argPart, raw=self.raw(raw), splitArgs=True)],\
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
class Arg(object):
	def __init__(self, value, raw):
		self.value = value
		self.raw = raw
		if self.raw:
			self.equalSign = b"="
		else:
			self.equalSign = "="
		
	def split(self):
		"""If applicable, splits the argument by equal sign and returns SplitArg.
		Otherwise, returns UnsplitArg with the entire argument as its one value."""
		param, value = self.value.partition(self.equalSign)[0::2]
		if value:
			return SplitArg(param, value)
		else:
			return UnsplitArg(self.value)

#=========================================================
class Argv(object):
	def __init__(self, argv, raw, withComm=True):
		if not withComm: argv.pop(0)
		self.args = argv
		self.raw = raw
		
	@property
	def withArgsSplit(self):
		"""Returns a list with all arguments split by equal sign, where applicable.
		Doesn't split if the left hand side includes non-alphanumeric characters, except
		dashes, in order not to mess with quoted strings, shell variables and subshells, etc."""
		argv = []
		for arg in self.args:
			for element in Arg(value=arg, raw=self.raw).split():
				argv.append(element)
		return argv

#=========================================================
class ExternalLinuxProcess(object):
	
	#=============================
	"""A Linux process that may or may not have been started by this program.
	
	This is implemented as a live wrapper around /proc.
	
	The basic assumption is that the process was originally started by something
	else, thus some functionality one could expect from the Process class will
	not be available."""
	#=============================
	
	def __init__(self, pid, raw=False):
		self.info = LinuxProcessInfo(pid)
		self.raw = raw
	
	def _typeString(self, byteString, raw=None):
		
		"""Make sure the specified string is ether bytes or str as specified.
		
		Takes bytes(), determines whether we're currently configured to cast
		bytes() into str() and returns accordingly.
		
		If instructed to return non-raw, we will strip the trailing newline."""
		
		if raw is None:
			raw = self.raw
		if raw:
			return byteString
		else:
			return byteString.decode().rstrip("\n")
		
	def _typeList(self, byteStringList, raw=None):
		
		"""Make sure the specified list is either made up of bytes or str as specified.
		
		Takes a list of bytes(), determines whether we're currently configured to cast
		bytes() into str() and return the list with its elements changed accordingly."""
		
		if raw is None:
			raw = self.raw
		if raw:
			return byteStringList
		else:
			return [byteString.decode() for byteString in byteStringList]
	
	def getName(self, raw=None):
		"""Name of the process without arguments."""
		return self._typeString(self.info.comm, raw)
	
	def getPath(self, raw=None):
		"""Executable path as it's found in the first element of the argv."""
		return self.getArgv(raw=raw)[0]
	
	def getPid(self):
		"""PID of the process. Returns as int."""
		return int(self.info.pid)
	
	def getArgvSplitByNul(self, raw=None):
		"""List of arguments used to start the process, starting with the command name.
		Args are split into a list by NUL."""
		return self._typeList(self.info.cmdline.split(b"\x00"), raw)
	
	def getArgv(self, raw=None, splitArgs=False, withComm=True):
		"""List of arguments used to start the process, starting with the command name.
		Args are split into a list by NUL, and, optionally, by equal sign."""
		argv = Argv(self.getArgvSplitByNul(raw=raw), raw=raw, withComm=withComm)
		if splitArgs:
			return argv.withArgsSplit
		else:
			return argv.args
		
	def hasArg(self, arg, raw=None, splitArgs=None):
		"""Is the specified arg in the processes argv?
		Returns True if it is, False if it's not."""
		#print("argv: ", self.getArgv(raw=raw, splitArgs=splitArgs, withComm=False)) #NOTE: DEBUG
		return arg in self.getArgv(raw=raw, splitArgs=splitArgs, withComm=False)

	def inArg(self, string, raw=None, splitArgs=None):
		"""Is the specified substring in one of the args in argv?
		Returns True if it is, False if it's not."""
		#NOTE: DEBUG
		#dprint("Testline", "||".join([str(argv) for argv in self.getArgv(raw=raw, splitArgs=splitArgs)]))
		#if "kchai" in "||".join( [str(argv) for argv in self.getArgv(raw=raw, splitArgs=splitArgs)] ):
		#	dprint("[!!!] argv:", self.getArgv(raw=False))
		#dprint([arg for arg in self.getArgv(raw=raw, splitArgs=splitArgs)])
		return any([arg for arg in self.getArgv(raw=raw, splitArgs=splitArgs) if string in arg])

# TODO: Windows/MacOS X support, if that should ever
# be required.
# Towards that end, these variables should later become factories/metaclassed
# classes that determine the platform and return the appropriate class.
ProcessList = LinuxProcessList
ExternalProcess = ExternalLinuxProcess
