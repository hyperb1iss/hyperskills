# Batch writes and a rejection report for meter imports

The second meter vendor sends drops with ISO 8601 timestamps that carry a UTC offset, values in MWh for the large commercial meters, and a byte order mark at the start of the file. This change accepts all three: timestamps are converted to UTC before storage, MWh joins the unit table, and the reader strips the BOM.

`import_file` now parses the drop first and stores the readings with a single `save_batch` call instead of one write per row, which turns a 40,000-row drop from 40,000 store round trips into one. It returns an `ImportSummary` with the number of new readings and the rejected rows with their line numbers. `gridmeter import` prints the summary per file and exits 1 when any row was rejected, so the nightly job alerts the data team to chase the vendor.
