# Fix garbled accented names in the contacts CSV download

Fixes the report that names with accented letters show up garbled when someone opens the downloaded contacts CSV in a spreadsheet app. The file was valid UTF-8, but spreadsheet apps decode a CSV with the system's legacy code page unless it starts with a UTF-8 byte-order mark.

- The downloaded CSV now starts with a UTF-8 byte-order mark: `write_contacts` takes a `bom` flag, and the download turns it on.
- The download declares `charset=utf-8` in its content type, and the new `Download.headers()` serves it as an attachment with a Content-Length.
- New tests check that the download starts with the mark and that an accented name decodes intact. I also opened a download in two spreadsheet apps to confirm the names display correctly.
- CHANGELOG entries under Unreleased.
