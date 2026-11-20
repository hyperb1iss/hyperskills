# Upgrading to Corvane Sync 4.2

Version 4.2 changes how large files are handled: files over 512 MB are split into 8 MB chunks, so an interrupted upload resumes instead of starting over. Version 4.1 clients keep syncing until June 30, then become read-only.

To upgrade, run `corvane self-update --channel stable` and restart the tray app. Our support team's advice: "Pause any sync that is mid-transfer before you upgrade."

The first sync after upgrading rebuilds the local index, which takes 15 minutes for a library of 50,000 files.
