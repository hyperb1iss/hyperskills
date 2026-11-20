# Upgrading to Corvane Sync 4.2

Version 4.2 changes how large files are handled. Files over 512 MB are now split into 8 MB chunks, so an interrupted upload resumes instead of starting over. Version 4.1 clients will keep syncing until June 30; after that date they become read-only.

To upgrade from the command line, run `corvane self-update --channel stable`, then restart the tray app. Our support team's advice: "Pause any sync that is mid-transfer before you upgrade."

The first sync after upgrading rebuilds the local index. For a library of around 50,000 files, this typically takes 10 to 20 minutes. That is only an estimate; it can run longer on slower disks or network drives.
