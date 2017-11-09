# User Guide

## General Usage

By default, FuzzyFileNav has access enabled via the view context menu.  The context menu gives you various fuzzy navigation methods.  By selecting `Fuzzy Nav Here...`, you will begin navigating the parent folder of the view's file (if saved on disk).  By selecting an option under `Fuzzy File Nav`, you can start with a list of folders from the project, bookmarks, or the root of the file system.  If you prefer to initiate the commands from a shortcut, you can define your own; some suggestions are shown in [Suggested Accessibility Shortcuts](#suggested-accessibility-shortcuts).  From the FuzzyFileNav panel, you can use shortcuts to copy, paste, delete, open, and various other file actions.

## Using the FuzzyFileNav Panel

While a FuzzyFileNav navigation panel is open, a number of shortcuts will be activated that can apply different actions to a file or folder or aide in navigating the panel.  Actions are only performed when the **full** name is typed into the panel. Using the path completion navigation shortcut will make this quick and easy.

### Autocomplete File Paths

FuzzyFileNav can complete file paths in the quick panel when ++tab++ is pressed.  Depending on the completion style, ++shift+tab++ can navigate through the completion options backwards.  There are three styles of autocompletion that FuzzyFileNav supports.

Autocomplete\ Style | Description
------------------- | -----------
Sublime             | Complete path with the selected index in the quick panel.
Unix/Linux          | Complete path like a Unix/Linux terminal traditionally completes paths. Will only complete the path if there is one possible option.
Windows             | Complete path like Windows completes paths in a command prompt. This allows you to cycle through options that start with the entered text.

See the [completion_style](#completion_style) setting for more info on configuring the completion style.

### Navigating Folders

When navigating folders in the quick panel, you start typing the folder's name, and you can press ++tab++ to complete the path (behavior may differ depending on [completion style setting](#autocomplete-file-paths)). You can descend into the folder by typing a `/` at the end (you can also use `\` on windows). The full path must be completed for "slash folder navigation".  You can can also press ++enter++ and whatever folder is currently selected in the panel will be navigated to.

!!! tip "Tip"
    Your file systems root can be accessed any time by typing '/'.  You can also switch to windows drives by typing `c:\` etc.

    The home folder can be accessed any time by typing `~/` into the FuzzyFileNav quick panel.

### Actions

Action                                                   | Windows\ &amp;\ Linux    | macOS
-------------------------------------------------------- | ------------------------ | -----
[Open](#open)                                            | ++enter++\ or\ ++right++ | ++enter++\ or\ ++right++
[Show/Hide\ hidden\ files](#show-hide-hidden-files)      | ++ctrl+h++               | ++cmd+h++
[Show\ Bookmarks](#show-bookmarks)                       | ++ctrl+b++               | ++cmd+b++
[Delete](#delete)                                        | ++ctrl+d++               | ++cmd+d++
[Copy](#copy)                                            | ++ctrl+c++               | ++cmd+c++
[Cut](#cut)                                              | ++ctrl+x++               | ++cmd+x++
[Paste](#paste)                                          | ++ctrl+v++               | ++cmd+v++
[New\ file](#new-file)                                   | ++ctrl+n++               | ++cmd+n++
[New\ folder](#new-folder)                               | ++ctrl+shift+n++         | ++cmd+shift+n++
[Save\ file\ as](#save-file-as)                          | ++ctrl+s++               | ++cmd+s++
[Reveal](#reveal)                                        | ++ctrl+r++               | ++cmd+r++
[Search\ folder](#search-folder)                         | ++ctrl+f++               | ++cmd+f++
[Add\ folder\ to\ project](#add-folder-to-project)       | ++ctrl+p++               | ++cmd+p++
[Get\ Current\ Working\ View](#get-current-working-view) | ++ctrl+period++          | ++cmd+period++

#### Open

This action opens the selected file in the palette.

#### Show/Hide hidden files

Toggles the showing/hiding of hidden files defined by the system or that are hidden via the regular expression patterns in the settings file.

#### Show Bookmarks

Shows the FuzzyFileNav bookmarks panel.

#### Delete

Deletes the folder/file object currently typed in the FuzzyFileNav panel.

#### Copy

Copies the folder/file object currently typed file in the FuzzyFileNav panel.  The copy will remain in the clipboard until a paste is performed.  Copies will be remembered even when the panel is manually dismissed and reopened.

#### Cut

Cuts (moves) the folder/file object currently typed into the FuzzyFileNav panel.  A Fuzzy File Paste must be performed to complete the cut (move). The cut file will be remembered even when the panel is manually dismissed and reopened.

#### Paste

Pastes the folder/file object that is in the clipboard.  The file/folder will be pasted into the currently opened folder in the FuzzyFileNav panel. To rename the folder/file object on paste, type the full name in the panel that should be used before pressing initiating the paste.

#### New File

Creates a new file in the currently opened folder in the FuzzyFileNav panel.  The name that is typed into the panel is the name that will be used.

#### New Folder

Creates a new folder in the currently opened folder in the FuzzyFileNav panel.  The name that is typed into the panel is the name that will be used.

#### Save File as

Saves the current focused view to the the currently opened folder in the FuzzyFileNav Panel.  The name that is typed into the panel is the name of the file the view will be saved to.  You will be prompted for file overwrite.

#### Reveal

Reveals the location of the file/folder name typed into the FuzzyFileNav panel in your file manager.  Will use the current folder if a valid one is not typed into the panel.

#### Search Folder

This action will open a folder search panel with the current folder's path, or the path of a subfolder (if one is typed into the FuzzyFileNav panel) and pre-load that folder name into the `where` box.  Any content in clipboard will be pre-loaded into the `Find` box.

#### Add Folder to Project

Adds the location of the folder name typed into the FuzzyFileNav panel into the current project.  Will use the current folder if a valid one is not typed into the panel.

#### Get Current Working View

Gets the file name of the current working view and copies it into the FuzzyFileNav Panel.

## Settings
There are various settings you can alter to enhance your experience with FuzzyFileNav.

### `bookmarks`

When using the bookmark command, you can bring up a list of bookmarked folders.  Bookmarks are defined in `bookmarks` setting as shown below. To add or change the bookmark list, just add, remove or modify an entry in the bookmark list.  Each entry is a dictionary containing two keys: `name` and `path`.  `name` is the name that will be displayed, path is the path to the folder.

```javascript
    // Bookmarked paths
    "bookmarks": [
        {"name": "My Computer", "path": ""},
        {"name": "Root", "path": "/"}
    ]
```

!!! tip "Tip"
    If it is desired to have specific bookmarks show up only on a specific OS or a specific host, you can augment the `path` option using the notation below.  For more information, please see [Platform/Computer Specific Settings](#platformcomputer-specific-settings).

    ```javascript
        // Bookmarked paths
        "bookmarks": [
            {"name": "My Computer", "path": {"#multiconf#": [{"os:windows": ""}]}},
            {"name": "Root", "path": {"#multiconf#": [{"os:linux": "/"}, {"os:osx": "/"}]}}
        ]
    ```

### `home`

`home` is your home directory.  By default it is `~` which expands to your user directory on your OS, but if you would like to modify it to be something else, this is the place!

```javascript
    // Location of home folder
    "home": "~",
```

### `regex_exclude`

`regex_exclude` is an array of regular expression patterns that indicate which files and folders FuzzyFileNav should ignore.

```js
    // Patterns of files/folders to exclude
    "regex_exclude": [".*\\.(DS_Store|svn|git)$"],
```

### `keep_panel_open_after_action`

Controls whether the quick panel should remain open after a file action (such as open) as performed.

```js
    // Keep panel open after a file is opened, deleted, created, etc. so
    // More files can be have actions performed on them.
    "keep_panel_open_after_action": true,
```

### `keep_panel_open_exceptions`

Provides exceptions for the [keep_panel_open_after_action](#keep_panel_open_after_action) setting.

```js
    // Actions that can ignore the keep panel open settings
    // Available actions: delete, open, saveas, mkfile, mkdir, paste
    "keep_panel_open_exceptions": [],
```

### `show_system_hidden_files`

Controls whether system hidden files are shown in FuzzyFileNav. How files are hidden vary on a given OS, but this should be able to show them.

```js
    // Controls whether system hidden files are shown in FuzzyFileNav.
    "show_system_hidden_files": true,
```

### `completion_style`
Allows the changing of the completion style to one of three styles.

```js
    // (fuzzy/windows/nix)
    // fuzzy   - this will auto-complete with the selected index in the quick panel
    // windows - this will complete like a windows terminal would complete paths
    // nix     - this will complete like a unix/linux terminal traditionally completes paths
    "completion_style": "fuzzy",
```

### `start_from_here_default_action`

There are times when the a FuzzyFileNav navigation command won't be fed a path.  One example is when the `Fuzzy Nav Here...` command is run from a view that hasn't been saved to disk.  This setting allows you to specify the fallback options to display.

```js
    // If the "FuzzyStartFromFileCommand" is run outside of an open buffer
    // or from a buffer that does not exist on disk, you can specify
    // its default action to do instead of starting navigation from
    // a file's location.  Options are "bookmarks", "home", "root", "project".
    "start_from_here_default_action": "bookmarks",
```

### `add_folder_to_project_relative`

When a FuzzyFileNav adds a folder to the project, this will be used to determined if the folder should be added as a path relative to the project file or not.

```js
    // Add your folders relative to the project file (if project file exists on disk)
    "add_folder_to_project_relative": false,
```

### `add_folder_to_project_follow_symlink`

When a FuzzyFileNav adds a folder to the project, this will be used to determined if the folder should have the `follow_symlinks` option set.

```js
    // When adding folder to project, set "follow_symlinks" setting as true or false
    "add_folder_to_project_follow_symlink": true,
```

### `use_sub_notify`

Enables use of [SubNotify](https://github.com/facelessuser/SubNotify) notifications.

```js
    // Use subnotify if available
    "use_sub_notify": true
```

## Suggested Accessibility Shortcuts

You can create shortcuts to access FuzzyFileNav Quickly, some examples are shown below.

For Windows/Linux:

```js
    [
        // Start from the parent folder of the current view's file
        { "keys": ["ctrl+o"], "command": "fuzzy_start_from_file" },
        // Show bookmarked folders
        { "keys": ["ctrl+shift+o"], "command": "fuzzy_bookmarks_load" }
    ]
```

For macOS:

```js
    [
        // Start from the parent folder of the current view's file
        { "keys": ["super+o"], "command": "fuzzy_start_from_file" },
        // Show bookmarked folders
        { "keys": ["super+shift+o"], "command": "fuzzy_bookmarks_load" }
    ]
```

## Platform/Computer Specific Settings

Currently, the `home` settings in the settings file, and the `path` setting in a bookmark entry can be configured to have multiple OS and/or host specific settings to help manage settings across different machines.

The syntax to configure one of these settings for multiple OS and/or hostname:

- The setting should be a key/value pair, where the key is `#multiconf#` and the value is an array of key/value entries whose keys describe the host and/or os qualifiers needed for the value to be used.
- The key/value entries will have a key that represents one or more qualifiers, each of which must be separated with a `;`
- Each qualifier consists of the qualifier type and a qualifier value to compare against.  These will be separated by a `:`.
- There are two supported qualifiers: `host` and `os`.  `host` is the name of your PC.  `os` is the platform and can be either `windows`, `linux`, or `osx`.
- The key/value entries will have a value associated with the key, and can be of any type: string, number, array, dictionary, etc.  This value is what will be returned if the qualifier is met.

examples:

```js
    "home": {"#multiconf#": [{"os:windows": "c:\\Some\\Location"}, {"os:linux": "/Some/Linux/Location"}]},
```

```js
    "home": {
        "#multiconf#": [
            {"os:windows": "C:\\Users"},
            {"os:linux;host:his_pc": "/home"},
            {"os:linux;host:her_pc": "/home/her/special"}
        ]
    }
```
