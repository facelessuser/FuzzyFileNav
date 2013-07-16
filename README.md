# About
Fuzzy File Nav is a simple plugin that allows for quick navigation of the file system from the quick panel.  It also allows for deletion, copying, moving, and creation of files and folders.

# Usage
Fuzzy File Nav by default has access enabled via the context menu.  You can access the root of your system by selecting `Fuzzy Nav`.  If you would like access Fuzzy File Nav but have it start in the current direct of the open file, you can select `Fuzzy Nav Here`.  If you would like to open the bookmark menu with your custom defined folders, you can select `Fuzzy BookMarks`.

## Suggested Accessibility Shortcuts
You can create shorcuts to access Fuzzy File Nav Quickly, some examples are shown below.

For Windows/Linux:

```javascript
    [
        { "keys": ["ctrl+o"], "command": "fuzzy_start_from_file" },
        { "keys": ["ctrl+shift+o"], "command": "fuzzy_bookmarks_load" }
    ]
```

For OSX:

```javascript
    [
        { "keys": ["super+o"], "command": "fuzzy_start_from_file" },
        { "keys": ["super+shift+o"], "command": "fuzzy_bookmarks_load" }
    ]
```

## Fuzzy Bookmarks
As mentioned earlier, you can bring up a list of bookmarked folders.  To add or change the bookmark list, simply add/change the entries in the settings file `fuzzy_file_nav.sublime-settings`. Required parameters are `name` and `path`.

```javascript
    // Bookmarked paths
    "bookmarks": [
        {"name": "My Computer", "path": ""},
        {"name": "Root", "path": "/"}
    ]
```

If it is desired to have specific bookmarks show up on a specific OS only or a specific host only, you augment the `path` option using the notation below.  For more information, please see **Platform/Computer Specific Settings**.

```javascript
    // Bookmarked paths
    "bookmarks": [
        {"name": "My Computer", "path": {"#multiconf#": [{"os:windows": ""}]}},
        {"name": "Root", "path": {"#multiconf#": [{"os:linux": "/"}, {"os:osx": "/"}]}}
    ]
```

## Custom Settings
There are a number of custom settings that can be defined for Fuzzy File Nav in the settings file `fuzzy_file_nav.sublime-settings`.

```javascript
    // Location of home folder
    "home": "",

    // Patterns of files/folders to exclude
    "regex_exclude": [".*\\.(DS_Store|svn|git)$"],

    // Keep panel open after a file is opened, deleted, created, etc. so
    // More files can be have actions perfomred on them.
    "keep_panel_open_after_action": true,

    // By default, files hidden by the system are hidden in Fuzzy File Nav
    // as well (files that start with "." in Linux\Unix and files with the
    // hidden attribute in windows)
    "show_system_hidden_files": true,

    // (Unix/Linux only) control whether autocomplete is case sensitive
    "case_sensitive": true,

    // If the "FuzzyStartFromFileCommand" is run outside of a open buffer
    // or from a buffer that does not exist on disk, you can specify
    // its default action to do instead of starting navigation from
    // a file's location.  Options are "bookmarks", "home", "root".
    "start_from_here_default_action": "bookmarks",
```

Home folder can be accessed any time by typing `~/` into the FuzzyFileNav quick panel. Home folder can be configured for multiple OS and/or hosts.  Simply use the notation below and see **Platform/Computer Specific Settings** for more information.

```javascript
    "home": {"#multiconf#": [{"os:windows": "c:\\Some\\Location"}, {"os:linux": "/Some/Linux/Location"}]},
```

## Platform/Computer Specific Settings
Currently the `home` settings in the settings file, and the `path` setting in a bookmark entry can be configured to have multiple OS and/or host specific settings to help manage settings across different machines.

The syntax to configure one of these settings to be OS and/or host specific is found below:

- The setting should be a key/value pair, where the key is `#multiconf#` and the value is an array of key/value entries whose keys describe the host and/or os qualifiers needed for the value to be used.
- The key/value entries will have a key that represents one or more qualifiers, each of which must be separated with a `;`
- Each qualifier consists of the qualifier type and a qualifier value to compare against.  These will be separated by a `:`.
- There are two supported qualifiers: `host` and `os`.  `host` is the name of your PC.  `os` is the platform and can be either `windows`, `linux`, or `osx`.
- The key/value entries will have a value associated with the key, and can be of any type: string, number, array, dictionary, etc.

example:

```javascript
    "home": {"#multiconf#": [{"os:windows": "c:\\Some\\Location"}, {"os:linux": "/Some/Linux/Location"}]},
```

## Fuzzy File Nav Panel Features
There are a number of featues accessibe by shortcuts when the Fuzzy File Nav Panel is open.  Most shorcuts are combinations of the modifier key `ctrl`; for OSX simply replace the `ctrl` modifier with `super`.

### Toggle the showing/hiding of hidden files.
`ctrl+h` Toggle the showing/hiding of hidden files defined by the system or by regex from settings file.

### Show Fuzzy Bookmarks
`ctrl+b` Show the Fuzzy Nav Bookmarks panel.

### Fuzzy File Name Complete
`tab` or `shift+tab` Complete the file name being typed (shift modifier cycles backwards).  If the current typed name matches one or more file/folders, tab will complete it.  Saddly it cannot tab into the currently selected fuzzy results, but it will tab through close options.

### Navigate Folders
`/` When you have a completed file name typed, you can type a slash after the name and you will descend into the folder.  Windows can also use `\` which will do the same thing.  You can also descend into folders by simply selected them in the nave panel.

### Fuzzy File Delete
`ctrl+d` Deletes the folder/file object currently typed (full name) in the Fuzzy File Nav panel.

### Fuzzy File Copy
`ctrl+c` Copies the folder/file object currently typed (full name) file in the Fuzzy File Nav panel.  A Fuzzy File Paste must be performed to complete the copy.

### Fuzzy File Cut
`ctrl+x` Cuts (moves) the folder/file object currently typed (full name) file in the Fuzzy File Nav panel.  A Fuzzy File Paste must be performed to complete the cut (move).

### Fuzzy File Paste
`ctrl+v` Completes the copying and pasting of the folder/file object that is in the clipboard.  The file/folder will be pasted into the currently opened folder in the Fuzzy File Nav Panel.  To rename the folder/file object on paste, type the full name that should be used before pressing `ctrl+v`.

### Fuzzy Make File
`ctrl+n` Creates a new file in the currently opened folder in the Fuzzy File Nav Panel.  The name that is typed into the panel is the name that will be used.

### Fuzzy Make Folder
`ctrl+shift+n` Creates a new folder in the currently opened folder in the Fuzzy File Nav Panel.  The name that is typed into the panel is the name that will be used.

### Fuzzy Save As File
`ctrl+s` Saves view to the the currently opened folder in the Fuzzy File Nav Panel.  The name that is typed into the panel is the name of the file the view will be saved to.  You will be prompted for file overwrite.

### Fuzzy Current Working View
`ctrl+.` Gets the file name of the current working view and copies it to the Fuzzy File Nav Panel.

# License

Fuzzy File nav is released under the MIT license.

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Credits
* Thanks to quodlibet for helping come up with great ideas for the plugin during development.

* Special thanks to [Boundincode](https://github.com/Boundincode) whose witty humor and quirky coding fueled the development of the plugin. (If only he was more humble...)

* Thanks to biermeester and matthjes for thier suggestions and ideas with platform/host specific settings.
