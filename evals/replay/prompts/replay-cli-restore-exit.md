`sibyld db restore` exits 0 even when the restore fails. That happens both when the restore result reports failure and when the restore raises, so a script that checks the exit status reads a partial restore as done.

Make a failed restore exit with status 1 in both cases.
