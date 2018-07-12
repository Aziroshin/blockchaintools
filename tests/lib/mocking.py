#=======================================================================================
# Imports
#=======================================================================================

# Python
import tempfile
import random
import string
import os
from pathlib import Path
from subprocess import Popen, PIPE

# Local
from tests.lib.errors import MockError

# Debug
import time
import os
from lib.debugging import dprint

#=======================================================================================
# Mock Classes
#=======================================================================================

class DummyProcess(object):
	
	"""A process intended for mock based integration testing
	Based around the idea of using C-based binaries that will be named and compiled
	on the fly, to prevent command line distortions by interpreters getting
	involved.
	
	Takes:
		- prefix: Prepended to the binary name for easier human identification and
		    debugging.
		- sourceCode: The source code for the ad-hoc compiled binary.
		- sourcePath: Path of the source file to read from and/or write to.
		    If writeSourceFile is True, will write specified or default source code
		    to this location, otherwise it'll just read from it (default if sourcePath
		    is specified).
		- writeSourceFile: Whether to use default or specified source code (True),
		    or simply read from the source file (False). If sourcePath is
		    specified it will default to False, otherwise to True.
		    
	If the ad-hoc compilation source code is found to be invalid, MockError will
	be raised. At the moment, it only checks for length, not actual code validity."""
	
	def __init__(self, prefix, sourceCode=None, sourcePath=None, writeSourceFile=None):
		
		self.prefix = prefix
		self.sourcePath = sourcePath
		self.sourceCode = sourceCode
		
		# writeSourceFile
		if writeSourceFile is None:
			if sourcePath is None: # Our default source path is intended for overwriting by default.
				self.writeSourceFile = True
			else: # Don't overwrite files at custom source paths, unless told to do so.
				self.writeSourceFile = False
		else: # We're told to overwrite. Do it.
			self.writeSourceFile = writeSourceFile
	
	@property
	def pid(self):
		return self.process.pid
	
	@property
	def identifier(self):
		
		"""A 64 digit random string to nearly-uniquely identify the process we'll test against.
		The string will be generated on first call. All subsequent calls will return
		the same string for the lifetime of the object.
		
		The motivation is to make process name collisions and the like unlikely.
		Such collisions could trip up the test and are something to watch out for.
		That's why executing these tests would be best done in a dedicated environment.
		"""
		
		if not hasattr(self, "_identifier"):
			self._identifier = "".join(random.SystemRandom().choice(\
				string.ascii_uppercase+string.ascii_lowercase+string.digits)\
					for i in range(0,64))
		return self._identifier
	
	@property
	def tempDir(self):
		"""Will hold the executable for the process we'll test against."""
		if not hasattr(self, "_tempDir"):
			self._tempDir = tempfile.TemporaryDirectory()
		return self._tempDir
	
	@property
	def name(self):
		"""Name of the process we're testing against."""
		return "{prefix}_name_{identifier}"\
			.format(prefix=self.prefix, identifier=self.identifier)
	
	@property
	def execPath(self):
		"""Path to the executable of the process we'll test against."""
		return str(Path(self.tempDir.name, self.name))
	
	@property
	def defaultSourcePath(self):
		"""The default source path to use if none was specified."""
		return "{0}.c".format(self.execPath)
	
	@property
	def sourcePath(self):
		"""Path to the source code for the executable of the process well test against.
		This just adds ".c" to .execPath."""
		if self._sourcePath is None:
			self._sourcePath = self.defaultSourcePath
		return self._sourcePath
	@sourcePath.setter
	def sourcePath(self, path):
		self._sourcePath = path
	
	@property
	def defaultSourceCode(self):
		"""The default source code to pass to GCC if none was specified."""
		return "void main() {while(1==1) {}}"
	
	@property
	def sourceCodeFromFile(self):
		with open(self.sourcePath, "r") as sourceFile:
			return sourceFile.read()
	
	@property
	def sourceCode(self):
	
		"""Source code for ad-hoc compilation.
		If no source code was specified, will default to one of two:
			- If writeSourceFile is True, default source code.
			- If writeSourceFile is False, read from source file"""
		
		# Get source code.
		if self._sourceCode is None:
			if self.writeSourceFile:
				self._sourceCode = self.defaultSourceCode
			else:
				self._sourceCode = self.sourceCodeFromFile
		
		# Validate source code and return or error.
		if self.sourceCodeValid(self._sourceCode):
			return self._sourceCode
		else:
			raise MockError("Invalid source code found.")
	@sourceCode.setter
	def sourceCode(self, sourceCode):
		self._sourceCode = sourceCode
	
	@property
	def argParam(self):
		"""Parameter name of the test-argument of the process we're testing against."""
		return "--{prefix}_param_{identifier}"\
			.format(prefix=self.prefix, identifier=self.identifier)
	
	@property
	def argValue(self):
		"""Value of the test-argument of the process we're testing against."""
		return "{prefix}_value_{identifier}"\
			.format(prefix=self.prefix, identifier=self.identifier)
	
	@property
	def envVarName(self):
		return "{prefix}_envVarName_{identifier}"\
			.format(prefix=self.prefix, identifier=self.identifier)
	
	@property
	def envVarValue(self):
		return "{prefix}_envVarValue_{identifier}"\
			.format(prefix=self.prefix, identifier=self.identifier)
	
	@property
	def process(self):
		"""The process we'll be testing against."""
		envDict = dict(os.environ)
		envDict[self.envVarName] = self.envVarValue
		if not hasattr(self, "_process"):
			self._process = Popen(\
			# We're simulating a somewhat complex command line here, with some blind arguments.
			[self.execPath, self.argParam, self.argValue],\
			env=envDict,\
			shell=False,\
			stdout=PIPE)
		return self._process
	
	def sourceCodeValid(self, sourceCode):
		"""Checks whether the source code is long enough to even remotely qualify as functional."""
		if len(sourceCode) > 7:
			return True
		else:
			return False
	
	def writeSourceCodeToFile(self, sourceCode):
		with open(self.sourcePath, "wt") as testProcessExec:
			testProcessExec.write(sourceCode)
	
	def prepareSourceFile(self):
		if self.writeSourceFile:
			self.writeSourceCodeToFile(self.sourceCode)
			
	def compileExec(self):
		# TODO: Make sure doesn't hang
		stdout, stderr = [output.decode() for output in\
			Popen(["gcc", self.sourcePath, "-o", self.execPath],\
			stdout=PIPE, stderr=PIPE).communicate()]
		if len(stdout) > 0 or len(stderr) > 0:
			raise MockError(\
				"Ad-hoc compilation failed: \n[gcc stdout]:\n{stdout}\n[gcc stderr]:\n{stderr}\n"\
				.format(stdout=stdout, stderr=stderr))
		Path(self.execPath).chmod(0o700)
		
	def start(self):
		
		"""Compile and start test process."""
		self.prepareSourceFile()
		self.compileExec()
		self.process # Starts process.
		
	def stop(self):
		# Kill process.
		self.process.kill()
		self.process.communicate()
		# Remove directory
		self.tempDir.cleanup()
