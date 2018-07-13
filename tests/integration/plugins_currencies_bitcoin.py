#=======================================================================================
# Imports
#=======================================================================================

# Python
import unittest
import os
import shutil
from pathlib import Path

# Local
from tests.lib.mocking import DummyProcess

#=======================================================================================
# Configuration
#=======================================================================================

DATA_DIR = str(Path(Path(__file__).absolute().parent, "tests", "data", "plugins_currency_bitcoin"))

#=======================================================================================
# Tests
#=======================================================================================

class BitcoinMockProcess(DummyProcess):
	
	def __init__(self, homeDirSourcePath=None, sourcePath=None):
		
		super().__init__(prefix="", sourcePath=sourcePath)
		
		self.homeDirSourcePath = Path(homeDirSourcePath)
		
		# Make sure temp dir exists and initialize it if applicable.
		self.tempDir
		if not self.homeDirPath.exists():
			if homeDirSourcePath is None:
				self.homeDirPath.mkdir(exist_ok=True)
			else:
				shutil.copytree(str(self.homeDirSourcePath), str(self.homeDirPath))
	
	def homeDirPath(self):
		"""Path object for the home directory."""
		return Path(tempDir.name, "home")
	
	@property
	def process(self):
		envDict = dict(os.environ)
		envDict["HOME"] = str(Path(self.tempDir.name, "home"))
		if not hasattr(self, "_process"):
			self._process = Popen(\
			# We're simulating a somewhat complex command line here, with some blind arguments.
			[self.execPath, self.argParam, self.argValue],\
			env=envDict,\
			shell=False,\
			stdout=PIPE)
		return self._process

class BitcoinDaemonMockProcess(BitcoinMockProcess):
	@property
	def name(self):
		return "bitcoind"
	
class BitcoinCliMockProcess(BitcoinMockProcess):
	@property
	def name(self):
		return "bitcoin-cli"

class BitcoinTestCase(unittest.TestCase):
	
	prefix = "blockchaintools_test"
	
	@property
	def bitcoindSourcePath(self):
		return Path(DATA_DIR, "bitcoind.c")
	
	@property
	def bitcoinCliSourcePath(self):
		return Path(DATA_DIR, "bitcoin-cli.c")
	
	@property
	def homeDirPath(self):
		return Path(DATA_DIR, "default-home"))
	
	def __init__(self, methodName="runTest"):
		super().__init__(methodName)
		self.testDaemonProcess = BitcoinDaemonMockProcess(sourcePath=str(self.bitcoindSourcePath),\
			homeDirSourcePath=str(self.homeDirPath))
		self.testCliProcess = BitcoinCliMockProcess(sourcePath=str(self.bitcoinCliSourcePath),\
			homeDirSourcePath=str(self.homeDirPath))
		
	def setUp(self):
		self.testDaemonProcess.start()
	
	def tearDown(self):
		self.testDaemonProcess.stop()

if __name__ == "__main__":
	unittest.main()
