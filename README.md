# blockchaintools
Currently, this contains the code base for what, at this time, is predominantly intended to be a masternode management toolset once it reaches a stage at which it becomes actually usable.
The first milestone will be for it to have the functionality of its much simpler predecessor: legacy/vivomanager.sh, which is what I mainly use to manage nodes (state: April 27, 2018). It's here for reference, and in case someone might find it useful. Be aware that it is not very robust, so tread lightly.

Quick rundown of how one would set up a node with the legacy script (just run *vivomanager* without parameters and it'll give you an overview of available commands):

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
