# Batch writes and a rejection report for meter imports

The second meter vendor sends drops with ISO 8601 timestamps that carry a UTC offset and a byte order mark at the start of the file. This change accepts both: offset timestamps are converted to UTC before storage (an ISO timestamp without a time or an offset is rejected, as before), and the reader strips the BOM. Rejected rows are reported with their physical line number in the file.

`import_file` now parses the drop first and stores the readings with a single `save_batch` call instead of one write per row, which turns a 40,000-row drop from 40,000 store round trips into one. It returns an `ImportSummary` with the number of new readings and the rejected rows with their line numbers. `gridmeter import` prints the summary per file and exits 1 when any row was rejected, so the nightly job alerts the data team to chase the vendor.
