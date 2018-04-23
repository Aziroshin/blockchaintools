#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

from lib.exceptions import Error, ErrorWithCodes, ErrorCodes

#=======================================================================================
# Library
#=======================================================================================

#==========================================================
# Exceptions
#==========================================================

#==========================================================
class WalletError(ErrorWithCodes):
	codes = ErrorCodes()
	codes.CLI_ERROR = 0
	codes.RPC_CONNECTION_FAILED = 21

#==========================================================
class DaemonStuckError(Error):
	pass

#==========================================================
# Wallet Classes
#==========================================================

# At the moment, these classes do nothing. However, this codebase is going
# to have the expectation for subclasses of these to be used by plugins,
# which makes them domain-specific to this module level, which this represents.

class Wallet(object): pass
class CurrencyConfig(object): pass