# FuzzyFileNav 2.0.0

Nov X, 2017

- **NEW**: Copied files/folders persist across FuzzyFileNav sessions (panel open and closes).
- **NEW**: Add ability to store multiple files and folders in the clipboard.
- **NEW**: Add ability to paste a single file or folder from the clipboard stash when there are multiple.
- **NEW**: Commands are available from the command palette.
- **NEW**: Move context menu items to tab context menu as commands don't directly operate on view content.
- **FIX**: Don't copy `.` and `..`.
- **FIX**: Vague overwrite messages.
- **FIX**: Abort paste if destination equals source.
- **FIX**: Fix logging errors.
- **FIX**: Fix bad plugin notification title.
- **FIX**: Exclude `..` from completions.
