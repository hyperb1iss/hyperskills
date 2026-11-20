hey, quick heads up before standup. the nightly import failed again at 02:10. same damn spot as tuesday.

i dug in and it's not the parser, it's the vendor file: they started sending 3 extra columns and didn't tell anyone. i've patched the mapping on fix/import-cols and rerun the job by hand, so today's numbers are good.

what i haven't done yet is add a check that yells when the column count changes, which is the real fix. that's on me. i can pair on it after lunch, or you grab it and i'll review. either way it's maybe 30 minutes of work.

just wanted to flag it so nobody's surprised.
