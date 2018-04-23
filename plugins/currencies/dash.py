#-*- coding: utf-8 -*-

#=======================================================================================
# Imports
#=======================================================================================

from plugins.currencies.bitcoin import\
	Wallet as BaseWallet,\
	Config as BaseConfig,\
	ArgumentSetup as BaseArgumentSetup,\
	Actions as BaseActions

#=======================================================================================
# Wallet Classes & Default Configuration
#=======================================================================================

#==========================================================
class DashConfig(BaseConfig):
	
	#=============================
	# Defaults
	#=============================
	defaultFileBaseName = "dash"
	defaultDataDirName = ".{0}core".format(defaultFileBaseName)
	defaultRpcPort = "9998"
	defaultPort = "9999"
	#=============================

#==========================================================
class DashWallet(BitcoinWallet): pass#TODO

#==========================================================
class DashArgumentSetup(BitcoinArgumentSetup): pass#TODO

#==========================================================
class DashActions(BaseActions): pass#TODO

#=======================================================================================
# Exports
#=======================================================================================

Config = DashConfig
Wallet = DashWallet
ArgumentSetup = DashArgumentSetup
Actions = DashActions