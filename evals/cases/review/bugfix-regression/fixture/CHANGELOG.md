# Changelog

## Unreleased

### Added

- Filter the contacts page by tag.

### Fixed

- Accented names no longer show up garbled when the CSV download is opened in a spreadsheet app.
- The CSV download is served as an attachment with an explicit UTF-8 charset.

## 1.4.0

### Added

- Nightly backups, written atomically, and `restore_into` for merging a backup into a live book.

### Fixed

- Email addresses are compared case-insensitively.
