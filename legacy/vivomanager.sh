#!/bin/bash

#Copyright (c) 2018 Christian Knuchel

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

version="1.6 (vivo)"

#=====================================
# Configuration
#=====================================

# Parameters: First parameter is what you want to do, second is the ID of the node.
# Example: vivo-masternode start 24 <- starts node 24.
command="${1}"
masternodeId="${2}"
coinName="vivo"
dataDirName=".vivocore"

# Download list.
releasesUrl="https://github.com/vivocoin/vivo/releases"

# The user's actual home directory (as we're going to use a different one further below)
userHomeDir="$(realpath ~)"

# The directory where everything related to our coin lives.
coinDir="${userHomeDir}/coins/${coinName}"

# The directory where the masternode directores are stored.
masternodeIdDir="${coinDir}/masternodes"

# The cache directory (for downloads) (currently unused).
# cacheDir="${userHomeDir}/.cache/blockchaintools"

# Wallet install file.
#installFile="${cacheDir}/${coinName}-installfile"

# Sentinel Directories.
sentinelInstallParentDir="${userHomeDir}"
sentinelInstallDir="${sentinelInstallParentDir}/sentinel"

# Set HOME dir.
masternodeHomeDir="${masternodeIdDir}/${masternodeId}"

# Set up environment.
export HOME="${masternodeHomeDir}"

# The datadir where all the coin data gets stored and the configuration is located.
masternodeDataDir="${masternodeHomeDir}/${dataDirName}"

# Where the binaries are.
# If you'd like to keep older binaries, you could create a directory like /home/user/vivo/bin/2017-07-20,
# and then link that directory to /home/user/vivo/bin/old/current. The next time you update, make a new one
# And then link the "current" symlink to that one instead. Then, you won't have to fiddle with this
# configuration every time you update your binaries. :)
# Of course, you could also just have the current binaries in a $PATH recognized directory. xD
walletBinDir="${coinDir}/bin"
daemonBin="${walletBinDir}/${coinName}d"
cliBin="${walletBinDir}/${coinName}-cli"
txBin="${walletBinDir}/${coinName}-tx"

# The RPC base port. Masternodes will have ports incremented upwards from this one.
baseRpcPort=9400

# The other port. Behaves the same way as the above one regarding increments.
# Increase if you want to run a crazy number of masternodes on your system. :p
# Example: If the RPC base port is 9400 and this one is 9700, that will allow for 300 masternodes.
# If you want more and don't increase this setting, the RPC port configurations for masternode 301 and up
# will start colliding with this one.
basePort=9700

# The editor you wish to use to edit your masternode configuration files.
editor="nano"

# The contents written to the "vivo.conf" file of every freshly installed masternode.
standardConf="rpcuser=rzufhewzughewfuw
rpcpassword=g3w8g2j4tewgjem
rpcallowip=127.0.0.1
rpcport=$(expr ${baseRpcPort} + ${masternodeId} 2> /dev/null)
listen=1
server=1
daemon=1
maxconnections=24
masternode=1
masternodeprivkey=
externalip="

# The contents written to the "sentinel.conf" file upon adding Sentinel to a masternode.
standardSentinelConf="# specify path to vivo.conf or leave blank
# default is the same as VivoCore
vivo_conf=${masternodeDataDir}/vivo.conf

# valid options are mainnet, testnet (default=mainnet)
network=mainnet
#network=testnet

# database connection details
db_name=database/sentinel.db
db_driver=sqlite"

#=====================================
# Initialization
#=====================================
# Make sure the base directories exist.
mkdir -p "${masternodeIdDir}"
mkdir -p "${walletBinDir}"
# Make sure the cache directory exists.
#mkdir -p "${cacheDir}"
# List of masternodes.
masternodeIdList=$(ls "${masternodeIdDir}")
# Path to this script.
thisScript="$(realpath $0)"

#=====================================
# Function Library
#=====================================
function getRunningMasternodes() { #TODO
        echo "Not implemented."
}
function startMasternode() {
                "${daemonBin}" -daemon
}
function stopMasternode() {
                "${cliBin}" stop
}
function getMasternodeList() {
        echo -e $(ls "${masternodeIdDir}")
}
function listCommands() {
		echo -e "\tinfo <- Get information about your setup (directory paths)."
        echo -e "\tstart <- Start the corresponding masternode."
        echo -e "\tstartall <- Start all masternodes at once."
        echo -e "\tstop <- Stop the corresponding masternode."
        echo -e "\tstopall <- Stop all masternodes at once."
        echo -e "\tcreate <- Quickly start and stop a masternode with a new ID so you can start setting it up."
        echo -e "\tlivelog <- Attach to the corresponding debug.log using tail-f."
        echo -e "\tgetlog <- Print the entire log to the terminal using cat."
        echo -e "\tsentinel <- Run sentinel."
        echo -e "\tsentinel <- Run del."
        echo -e "\tdeleteblockchain <- Delete the \"chainstate\" and \"blocks\" directories."
        echo -e "\tcli <- calling ${cliBin}."
        echo -e "\ttx <- Calling ${txBin}."
        echo -e "\tlist <- List masternodes."
        echo -e "\tinstallsentinel <- Install sentinel (the entire software;"
        echo -e "\taddsentinel <- Adds sentinel to the specified node. does not need to be done for every node)."
        #echo -e "\tlistrunning <- List running masternodes (not implemented)."
        echo -e "\tconf <- Open the corresponding vivo.conf file with the configured editor for editing."
        echo -e "\tconfmasternode <- opens the masternode.conf for editing."
        echo -e "\tconfsentinel <- Open the sentinel config for editing."
        echo -e "\tversion <- Displays the version of this script (why even bother, here it is: ${version})"
}
function exitIfNoMasternodeId() {
if [[ $masternodeId == "" ]]; then
        echo "You need to specify a node ID."
        echo "Example: vivomanager start 24, whereas \"24\" would be the node ID."
        echo -e "Available node IDs (which are just directories in ${masternodeIdDir})"
        echo -e "${masternodeIdList}"
        exit 1
fi
}
function startAllMasternodes() {
        echo ""
}
function stopAllMasternoes() {
        echo ""
}

#=====================================
# Check arguments and provide help
#=====================================

# Check whether the first parameter to the script is valid.
if [[ $command == "" ]]; then
        echo "You need to specify a command to execute."
        echo -e "Example: vivomanager start 24, whereas \"start\" would be the command."
        echo "Available commands:"
        listCommands
        exit 1
fi

#=====================================
# Actions
#=====================================

# Announce environment data.

if [[ $command == "info" ]]; then
        echo -e "The configuration and setup seems to be as follows:"
        echo -e "\tcli binary: ${cliBin}"
        echo -e "\tdaemon binary: ${daemonBin}"
        echo -e "\ttx binary: ${txBin}"
        echo -e "\tdatadir: ${masternodeDataDir}"
        echo -e "\tversion of this script: ${version}"
        exit 0
fi

if [[ $command == "install" ]]; then
		echo -e "Please specify a ${coinName} archive link for downloading (you can get a list of available releases here: ${releasesUrl})."
		read walletDownloadAddress
		if [[ "${walletDownloadAddress}" == "" ]]; then
			echo -e "You have not specified a link. Exiting."
			exit 1
		fi
		wget "${walletDownloadAddress}" -O - | tar x -C "${walletBinDir}"
        exit 0
fi

if [[ $command == "start" ]]; then
        exitIfNoMasternodeId
        echo -e "Starting masternode with ID \"${masternodeId}\" in home directory \"${masternodeHomeDir}\""
        startMasternode
        exit 0
fi

if [[ $command == "reindex" ]]; then
        exitIfNoMasternodeId
        echo -e "Starting masternode with ID \"${masternodeId}\" in home directory \"${masternodeHomeDir}\""
        startMasternode "-reindex"
        exit 0
fi

if [[ $command == "startall" ]]; then
        while read -r id; do
                "${thisScript}" start "${id}"
        done <<< "${masternodeIdList}"
        exit 0
fi

if [[ $command == "stopall" ]]; then
        while read -r id; do
                "${thisScript}" stop "${id}"
        done <<< "${masternodeIdList}"
        exit 0
fi

if [[ $command == "stop" ]]; then
        exitIfNoMasternodeId
        stopMasternode
        exit 0
fi
if [[ $command == "create" ]]; then
        exitIfNoMasternodeId
        echo -e "Creating masternode with ID \"${masternodeId}\" in home directory \"${masternodeHomeDir}\"."
        mkdir -p "${masternodeDataDir}"
        echo "${standardConf}" > "${masternodeDataDir}/${coinName}.conf"
        exit 0
fi

if [[ $command == "livelog" ]]; then
        exitIfNoMasternodeId
        echo "===>>> Opening livelog. Use Ctrl-C to close. <<<==="
        tail -f "${masternodeDataDir}/debug.log"
        exit 0
fi

if [[ $command == "getlog" ]]; then
        exitIfNoMasternodeId
        cat "${masternodeDataDir}/debug.log"
        exit 0
fi

if [[ $command == "sentinel" ]]; then
        exitIfNoMasternodeId
        cd "${masternodeDataDir}/sentinel"
	venv/bin/python bin/sentinel.py
        exit 0
fi

if [[ $command == "deleteblockchain" ]]; then
        exitIfNoMasternodeId
        rm -Rf "${masternodeDataDir}/blocks"
        rm -Rf "${masternodeDataDir}/chainstate"
        rm -Rf "${masternodeDataDir}/database"
        rm -Rf "${masternodeDataDir}/mncache.dat"
        rm -Rf "${masternodeDataDir}/peers.dat"
        rm -Rf "${masternodeDataDir}/mnpayments.dat"
        rm -Rf "${masternodeDataDir}/banlist.dat"
        exit 0
fi

if [[ $command == "cli" ]]; then
        exitIfNoMasternodeId
        shift 2 # Remove the two first arguments (command and ID)
        "${cliBin}" $@
        exit 0
fi

if [[ $command == "tx" ]]; then
        exitIfNoMasternodeId
        shift 2 # Remove the two first arguments (command and ID)
        "${txBin}" $@
        exit 0
fi

if [[ $command == "list" ]]; then
        echo -e "List of masternodes:"
        masternodeList=$(getMasternodeList)
        echo -e ${masternodeList} | tr " " "\n"
        exit 0
fi

if [[ $command == "installsentinel" ]]; then
	echo "Installing Sentinel."
	echo "NOTE: Give it a bit of time, even when it seems to have finished for a moment."
	sleep 1
        sudo apt-get -y install git python-virtualenv
        cd "${sentinelInstallParentDir}"
        git clone https://github.com/vivocoin/sentinel.git
	cd "${sentinelInstallDir}"
	virtualenv ./venv
	venv/bin/pip install -r requirements.txt
        exit 0
fi

if [[ $command == "addsentinel" ]]; then
        exitIfNoMasternodeId
	cp -a "${sentinelInstallDir}" "${masternodeDataDir}/"
	echo "${standardSentinelConf}" > "${masternodeDataDir}/sentinel/sentinel.conf"
        exit 0
fi

if [[ $command == "listrunning" ]]; then
        getRunningMasternodes
        echo -e "${runningMasternodesList}"
        exit 0
fi

if [[ $command == "conf" ]]; then
        exitIfNoMasternodeId
        $editor "${masternodeDataDir}/${coinName}.conf"
        exit 0
fi

if [[ $command == "confmasternode" ]]; then
        exitIfNoMasternodeId
        $editor "${masternodeDataDir}/masternode.conf"
        exit 0
fi

if [[ $command == "confsentinel" ]]; then
        exitIfNoMasternodeId
        $editor "${masternodeDataDir}/sentinel/sentinel.conf"
        exit 0
fi

if [[ $command == "version" ]]; then
        exitIfNoMasternodeId
       echo "${version}"
        exit 0
fi

echo -e "The specified command \"${command}\" isn't valid. The following commands are available:"
listCommands
exit 1
