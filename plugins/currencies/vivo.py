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
class VivoConfig(BaseConfig):
	
	#=============================
	# Defaults
	#=============================
	defaultFileBaseName = "vivo"
	defaultDataDirName = ".{0}core".format(defaultFileBaseName)
	#=============================

#==========================================================
class VivoWallet(BaseWallet): pass#TODO

#==========================================================
class VivoArgumentSetup(BaseArgumentSetup): pass#TODO

#==========================================================
class VivoActions(BaseActions): pass#TODO

#=======================================================================================
# Exports
#=======================================================================================
Config = VivoConfig
Wallet = VivoWallet
ArgumentSetup = VivoArgumentSetup
Actions = VivoActions