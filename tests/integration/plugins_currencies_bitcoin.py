#=======================================================================================
# Imports
#=======================================================================================

# Python
import unittest
import os
import sys
import shutil
from subprocess import Popen, PIPE
from pathlib import Path

# Local
from tests.lib.mocking import DummyProcess

# What's to be tested.
from plugins.currencies.bitcoin import\
	BitcoinWallet as Wallet,\
	BitcoinConfig as Config

#debug
from lib.debugging import dprint

#=======================================================================================
# Configuration
#=======================================================================================

TESTDATA_DIR = str(Path(Path(sys.argv[0]).resolve().parent, "tests", "data", "plugins_currency_bitcoin"))

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
				if self.homeDirSourcePath.exists():
					shutil.copytree(str(self.homeDirSourcePath), str(self.homeDirPath))
	@property
	def envToRun(self):
		return dict(os.environ).update({"HOME": str(Path(self.tempDir.name, "home"))})
	
	@property
	def homeDirPath(self):
		"""Path object for the home directory."""
		return Path(self.tempDir.name, "home")
	
	@property
	def basePath(self):
		"""Return the path of the directory the binaries are expected to reside in."""
		return Path(self.execPath).parent

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
	
	def __init__(self, methodName="runTest"):
		super().__init__(methodName)
		self.testDaemonProcess = BitcoinDaemonMockProcess(sourcePath=str(self.mockDaemonSourcePath),\
			homeDirSourcePath=str(self.homeDirSourcePath))
		self.testCliProcess = BitcoinCliMockProcess(sourcePath=str(self.mockCliSourcePath),\
			homeDirSourcePath=str(self.homeDirSourcePath))
	
	@property
	def mockDaemonSourcePath(self):
		return Path(TESTDATA_DIR, "bitcoind.c")
	
	@property
	def mockCliSourcePath(self):
		return Path(TESTDATA_DIR, "bitcoin-cli.c")
	
	@property
	def homeDirSourcePath(self):
		return Path(TESTDATA_DIR, "default-home")
	
	def setUp(self):
		self.testDaemonProcess.start()
		
	def tearDown(self):
		self.testDaemonProcess.stop()
	
class BitcoinDaemonTestCase(BitcoinTestCase):
	
	def newWalletInstance(self):
		return Wallet(Config(\
			basePaths=[str(self.testDaemonProcess.basePath)],\
			dataDirBaseDirPath=self.testDaemonProcess.homeDirPath))
	
	#def test_start(self):
	#	wallet = self.newWalletInstance()
	
	def test_getDaemon(self):
		#while True: pass
		wallet = self.newWalletInstance()
		wallet.getDaemon()

if __name__ == "__main__":
	unittest.main()
