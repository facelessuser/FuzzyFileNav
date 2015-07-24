# User Guide {: .doctitle}
Configuring and using FuzzyFileNav.

---

## General Usage
By default, FuzzyFileNav has access enabled via the view context menu.  The context menu gives you various fuzzy navigation methods.  By selecting `Fuzzy Nav Here...`, you will begin navigating the parent folder of the view's file (if saved on disk).  By selecting an option under `Fuzzy File Nav`, you can start with a list of folders from the project, bookmarks, or the root of the file system.  If you prefer to initiate the commands from a shortcut, you can define your own; some suggestions are shown in [Suggested Accessibility Shortcuts](#suggested-accessibility-shortcuts).  From the FuzzyFileNav panel, you can use shortcuts to copy, paste, delete, open, and various other file actions.

## File Action Shortcuts
While a FuzzyFileNav navigation panel is open, a number of shortcuts will be activated that can either apply different actions to a file or folder.  Most shortcuts are a combinations of the modifier key <kbd>ctrl</kbd>; for OSX simply replace the <kbd>ctrl</kbd> modifier with <kbd>super</kbd>.  Actions are only performed when the **full** name is typed into the panel; using the path completion shortcut will make this quick and easy.

### Autocomplete File Paths
FuzzyFileNav can complete file paths in the quick panel when <kbd>tab</kbd> is pressed.  Depending on the completion style <kbd>shift</kbd> + <kbd>tab</kbd> can navigate through the completion options backwards.  There are three styles of autocompletion that FuzzyFileNav supports.

| Autocomplete&nbsp;Style | Description |
|-------------------------|-------------|
| Sublime                 | Complete path with the selected index in the quick panel. |
| Unix/Linux              | Complete path like a unix/linux terminal traditionally completes paths. |
| Windows                 | Complete path like Windows completes paths in a command prompt. |

See the [completion_style](#completion_style) setting for more info on configuring the completion style.

### Navigating Folders
When navigating folders in the quick panel, you start typing the folders name, press <kbd>tab</kbd> to complete the path, and type a `/` at the end (you can also use `\` on windows).  As soon as the trailing slash is entered, the path will be navigated to.  The **full** file path must be used for this to work which is why autocomplete will come in handy.  Selecting a file and pressing enter enter in the panel will also navigate into the folder.

!!! tip "Tip"
    Your file systems root can be accessed any time by typing '/'.  You can also switch to windows drives by typing `c:\` etc.

    The home folder can be accessed any time by typing `~/` into the FuzzyFileNav quick panel.

### Toggle the showing/hiding of hidden files.
<kbd>ctrl</kbd> + <kbd>h</kbd> toggles the showing/hiding of hidden files defined by the system or that are hidden via the regular expression patterns in the settings file.

### Show Fuzzy Bookmarks
<kbd>ctrl</kbd> + <kbd>b</kbd> shows the FuzzyFileNav bookmarks panel.

### Fuzzy Open File
When a file is selected in the drop down list of the quick panel, you can either press <kbd>enter</kbd> or <kbd>right</kbd> to open the file.

### Fuzzy File Delete
<kbd>ctrl</kbd> + <kbd>d</kbd> deletes the folder/file object currently typed in the FuzzyFileNav panel.

### Fuzzy File Copy
<kbd>ctrl</kbd> + <kbd>c</kbd> Copies the folder/file object currently typed file in the FuzzyFileNav panel.  The copy will remain in the clipboard until a paste is performed or a new copy is initiated.

### Fuzzy File Cut
<kbd>ctrl</kbd> + <kbd>x</kbd> cuts (moves) the folder/file object currently typed into the FuzzyFileNav panel.  A Fuzzy File Paste must be performed to complete the cut (move).

### Fuzzy File Paste
<kbd>ctrl</kbd> + <kbd>v</kbd> Completes the copying and pasting of the folder/file object that is in the clipboard.  The file/folder will be pasted into the currently opened folder in the FuzzyFileNav panel.  To rename the folder/file object on paste, type the full name in the panel that should be used before pressing <kbd>ctrl</kbd> + <kbd>v</kbd>.

### Fuzzy Make File
<kbd>ctrl</kbd> + <kbd>n</kbd> Creates a new file in the currently opened folder in the FuzzyFileNav panel.  The name that is typed into the panel is the name that will be used.

### Fuzzy Make Folder
<kbd>ctrl</kbd> + <kbd>shift</kbd> + <kbd>n</kbd> Creates a new folder in the currently opened folder in the Fuzzy File Nav Panel.  The name that is typed into the panel is the name that will be used.

### Fuzzy Save As File
<kbd>ctrl</kbd> + <kbd>s</kbd> saves view to the the currently opened folder in the FuzzyFileNav Panel.  The name that is typed into the panel is the name of the file the view will be saved to.  You will be prompted for file overwrite.

### Fuzzy Reveal File/Folder in File Manager
<kbd>ctrl</kbd> + <kbd>r</kbd> will reveal the location of the file/folder name typed into the FuzzyFileNav panel in your file manager.  Will use the current folder if a valid one is not typed into the panel.

### Fuzzy Search Folder
<kbd>ctrl</kbd> + <kbd>f</kbd> will open a folder search panel with the current folder's path, or a the path of a subfolder if one is typed into the FuzzyFileNav panel, pre-loaded into the `where` box.  Any content in clipboard will be pre-loaded into the `Find` box.

### Fuzzy Add Folder to Project
<kbd>ctrl</kbd> + <kbd>r</kbd> will add the location of the folder name typed into the FuzzyFileNav panel into the current project.  Will use the current folder if a valid one is not typed into the panel.

### Fuzzy Current Working View
<kbd>ctrl</kbd> + <kbd>.</kbd> gets the file name of the current working view and copies it to the Fuzzy File Nav Panel.


## Settings
There are various settings you can alter to enhance your experience with FuzzyFileNav.

### bookmarks
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

### home
`home` is your home directory.  By default it is `~` which expands to your user directory on your OS, but if you would like to modify it to be something else, this is the place!

```javascript
    // Location of home folder
    "home": "~",
```

### regex_exclude
`regex_exclude` is an array of regular expression patterns that indicate which files and folders FuzzyFileNav should ignore.

```js
    // Patterns of files/folders to exclude
    "regex_exclude": [".*\\.(DS_Store|svn|git)$"],
```

### keep_panel_open_after_action
Controls whether the quick panel should remain open after a file action (such as open) as performed.

```js
    // Keep panel open after a file is opened, deleted, created, etc. so
    // More files can be have actions performed on them.
    "keep_panel_open_after_action": true,
```

### keep_panel_open_exceptions
Provides exceptions for the [keep_panel_open_after_action](#keep_panel_open_after_action) setting.

```js
    // Actions that can ignore the keep panel open settings
    // Available actions: delete, open, saveas, mkfile, mkdir, paste
    "keep_panel_open_exceptions": [],
```

### show_system_hidden_files
Controls whether system hidden files are shown in FuzzyFileNav. How files are hidden vary on a given OS, but this should be able to show them.

```js
    // Controls whether system hidden files are shown in FuzzyFileNav.
    "show_system_hidden_files": true,
```

### completion_style
Allows the changing of the completion style to one of three styles.

```js
    // (fuzzy/windows/nix)
    // fuzzy   - this will auto-complete with the selected index in the quick panel
    // windows - this will complete like a windows terminal would complete paths
    // nix     - this will complete like a unix/linux terminal traditionally completes paths
    "completion_style": "fuzzy",
```

### start_from_here_default_action
There are times when the a FuzzyFileNav navigation command won't be fed a path.  One example is when the `Fuzzy Nav Here...` command is run from a view that hasn't been saved to disk.  This setting allows you to sepcify the fallback options to display.

```js
    // If the "FuzzyStartFromFileCommand" is run outside of an open buffer
    // or from a buffer that does not exist on disk, you can specify
    // its default action to do instead of starting navigation from
    // a file's location.  Options are "bookmarks", "home", "root", "project".
    "start_from_here_default_action": "bookmarks",
```

### add_folder_to_project_relative
When a FuzzyFileNav adds a folder to the project, this will be used to determined if the folder should be added as a path relative to the project file or not.

```js
    // Add your folders relative to the project file (if project file exists on disk)
    "add_folder_to_project_relative": false,
```

### add_folder_to_project_follow_symlink
When a FuzzyFileNav adds a folder to the project, this will be used to determined if the folder should have the `follow_symlinks` option set.

```js
    // When adding folder to project, set "follow_symlinks" setting as true or false
    "add_folder_to_project_follow_symlink": true,
```

### use_sub_notify
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

For OSX:

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
