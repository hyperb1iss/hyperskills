# TUI Patterns Worth Borrowing

Use these applications as design references, not benchmark rankings or API documentation. Copy the interaction principle only when it serves the current task.

## Persistent Context: lazygit

A selector plus detail pane lets a user move among files, history, and changes while preserving a place to inspect the selected item. Context-sensitive actions reduce the need to memorize global shortcuts. The useful lesson is stable panel responsibility, not an exact panel count or a claim that every panel is always visible.

Use this shape for related resource lists. On narrow terminals, collapse secondary context and restore its selection when it returns. Avoid squeezing six panels into a viewport where no value is readable.

Primary reference: [lazygit repository and feature demonstrations](https://github.com/jesseduffield/lazygit).

## Hierarchy and Preview: Yazi

Parent/current/preview columns keep location and consequence visible during navigation. Preview work may be slow, so the cursor must move independently of decoding or file I/O. Tag preview requests with the selected resource identity to prevent late results replacing the current preview.

Use columns for hierarchical exploration. Prefer a stack with back-navigation when width is limited. Preserve the user's selection and scrolling per location instead of resetting every visit to the first row.

Primary reference: [Yazi layout and preview configuration](https://yazi-rs.github.io/docs/configuration/yazi/).

## Direct Focus: Posting

A multi-panel HTTP client benefits from a way to focus a distant control without cycling through every field. Posting's jump mode demonstrates visible target labels; a command palette can provide a complementary action route.

Use direct-focus labels when the screen has many interactive targets. Keep ordinary Tab navigation and ensure printable input belongs to the editor while it is focused. Labels should follow the visible layout and must not survive after their target disappears.

Primary reference: [Posting guide](https://posting.sh/guide/).

## Live Data: Dashboard and Log Patterns

A dashboard needs stable units, update freshness, and an explicit distinction between unavailable and zero. A log viewer needs a stable viewport, follow/pause behavior, and searchable retained events. Decorative activity is not evidence that the underlying request or stream remains healthy.

For high data rates, virtualize rows and separate storage from presentation. Keep selected item identity stable as sorting changes. If a paused view has new data, show the count or time boundary instead of dragging the user back to the end.

## Shell Integration: Picker Pattern

An inline picker should return one well-defined result to its caller and send interactive chrome to the appropriate terminal stream. Cancellation must differ from selecting an empty value. Restore terminal state before the shell consumes the result, and preserve scrollback where the chosen presentation allows it.

## Compose Only What the Task Needs

| User need            | Start with                               | Add only when justified                     |
| -------------------- | ---------------------------------------- | ------------------------------------------- |
| Choose one value     | List, filter, preview                    | Multi-select, saved searches                |
| Explore a hierarchy  | Stack or columns                         | Bookmarks, multiple independent panes       |
| Edit structured data | Editor plus validation/result view       | Tabs, jump labels, command palette          |
| Operate resources    | Selector, details, explicit action state | Batch operations with a reviewed target set |
| Monitor events       | List, filter, follow state               | Charts or correlated detail views           |

The recommendations above are design synthesis. Source behavior was checked 2026-09-04; revisit the application docs for current keybindings and configuration syntax.
