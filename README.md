# blockchaintools
Currently, this only contans one usable script: legacy/vivomanager.sh, which is a simplistic masternode management solution. It's what I mainly use to manage nodes (as of early January 2018), but it seems like it might be of use for others. Be aware that it is not very robust, so tread lightly.

Quick rundown of how one would set up a node with it (just run *vivomanager* without parameters and it'll give you an overview of available commands):

```
vivomanager install
vivomanager installsentinel
vivomanager installmnchecker
vivomanager create 1
vivomanager conf 1
vivomanager addsentinel 1
vivomanager getcrontablines 1

```
Note that you will still have to add those lines to crontab manually for sentinel and mnchecker.

You can start/stop your node like this:
```
vivomanager start
vivomanager stop
```
