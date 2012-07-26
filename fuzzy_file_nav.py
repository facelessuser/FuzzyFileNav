"""
Fuzzy File Navigation

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
"""

import sublime
import sublime_plugin
import os
import os.path as path
import re
import shutil
import ctypes

PLATFORM = sublime.platform()
CMD_WIN = r"^(?:(?:(~)|(\.\.))(?:\\|/)|((?:[A-Za-z]{1}\:)?(?:\\|/))|([\w\W]*(?:\\|/)))$"
CMD_NIX = r"^(?:(?:(~)|(\.\.))/|(/)|([\w\W]*/))$"
WIN_DRIVE = r"(^[A-Za-z]{1}\:)"


def get_root_path():
    # Windows doesn't have a root, so just
    # return an empty string to represent its root.
    return u"" if PLATFORM == "windows" else u"/"


def back_dir(cwd):
    prev = path.dirname(cwd)

    # On windows, if you try and get the
    # dirname of a drive, you get the drive.
    # So if the previous directory is the same
    # as the current, back out of the drive and
    # list all drives.
    return get_root_path() if prev == cwd else prev


def get_drives():
    # Search through valid drive names and see if they exist.
    return [unicode(d + ":") for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if path.exists(d + ":")]


def back_to_root(cwd):
    root = ""
    if PLATFORM != "windows":
        # Linux/Unix: just return root
        root = "/"
    else:
        # Windows: try and find root drive from path
        # otherwise return "" to signal fuzzy nav to
        # list all drives.
        m = re.match(WIN_DRIVE, cwd)
        if m:
            root = m.group(1)
    return unicode(root)


class FuzzyPanelText:
    content = ""

    @classmethod
    def set_content(cls, txt):
        cls.content = txt

    @classmethod
    def get_content(cls):
        txt = cls.content
        return txt

    @classmethod
    def clear_content(cls):
        cls.content = ""


class Clipboard:
    clips = []
    action = None

    @classmethod
    def add_entry(cls, entry):
        if not entry in cls.clips:
            cls.clips.append(entry)

    @classmethod
    def set_action(cls, action):
        cls.action = action

    @classmethod
    def clear_entries(cls):
        cls.clips = []
        cls.action = None


class FuzzyEventListener(sublime_plugin.EventListener):
    action = None

    def on_activated(self, view):
        # New window gained activation? Reset fuzzy command state
        if FuzzyFileNavCommand.active and view.window() and view.window().id() != FuzzyFileNavCommand.win_id:
            FuzzyFileNavCommand.reset()
        # View has not been assinged yet for since fuzzy nav panel appeared; assign it
        if FuzzyFileNavCommand.active and (FuzzyFileNavCommand.view == None or FuzzyFileNavCommand.view.id() != view.id()):
            FuzzyFileNavCommand.view = view

    def on_query_context(self, view, key, operator, operand, match_all):
        active = FuzzyFileNavCommand.active == operand
        if active and FuzzyFileNavCommand.view != None and FuzzyFileNavCommand.view.id() == view.id():
            FuzzyPanelText.set_content(view.substr(view.line(view.sel()[0])))
            full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
            empty = (FuzzyPanelText.get_content() == "")
            # See if this is the auto-complete path command
            if key == "fuzzy_path_complete":
                return active
            elif key == "fuzzy_toggle_hidden":
                return active
            elif key == "fuzzy_bookmarks_load":
                return active
            elif key == "fuzzy_get_cwd":
                return active
            elif key == "fuzzy_reveal":
                if path.exists(FuzzyFileNavCommand.cwd):
                    return active
                else:
                    sublime.status_message("%d does not exist!" % FuzzyFileNavCommand.cwd)
            elif key == "fuzzy_delete":
                if not empty and path.exists(full_name):
                    return active
                elif not empty:
                    sublime.status_message("%d does not exist!" % full_name)
            elif key == "fuzzy_make_file":
                if not empty and not path.exists(full_name):
                    return active
                elif not empty:
                    sublime.status_message("%d already exists!" % full_name)
            elif key == "fuzzy_make_folder":
                if not empty and not path.exists(full_name):
                    return active
                elif not empty:
                    sublime.status_message("%d already exists!" % full_name)
            elif key == "fuzzy_copy":
                if not empty and path.exists(full_name):
                    return active
                elif not empty:
                    sublime.status_message("%d does not exist!" % full_name)
            elif key == "fuzzy_cut":
                if path.exists(FuzzyFileNavCommand.cwd):
                    return active
                else:
                    sublime.status_message("%d does not exist!" % FuzzyFileNavCommand.cwd)
            elif key == "fuzzy_paste":
                if path.exists(FuzzyFileNavCommand.cwd):
                    return active
                else:
                    sublime.status_message("%d does not exist!" % FuzzyFileNavCommand.cwd)
        return False

    def on_modified(self, view):
        if FuzzyFileNavCommand.active and FuzzyFileNavCommand.view != None and FuzzyFileNavCommand.view.id() == view.id():
            sel = view.sel()[0]
            win = view.window()
            line_text = view.substr(view.line(sel))
            regex = CMD_WIN if PLATFORM == "windows" else CMD_NIX
            m = re.match(regex, line_text)
            if m:
                if m.group(1):
                    # Go Home
                    FuzzyFileNavCommand.fuzzy_reload = True
                    home = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("home", "")
                    home = get_root_path() if not path.exists(home) or not path.isdir(home) else home
                    win.run_command("fuzzy_file_nav", {"start": home})
                elif m.group(2):
                    # Back a directory
                    FuzzyFileNavCommand.fuzzy_reload = True
                    win.run_command("fuzzy_file_nav", {"start": back_dir(FuzzyFileNavCommand.cwd)})
                elif m.group(3):
                    # Go to root of drive/computer
                    if PLATFORM == "windows" and re.match(WIN_DRIVE, line_text):
                        if path.exists(line_text):
                            new_path = line_text.upper()
                    else:
                        new_path = back_to_root(FuzzyFileNavCommand.cwd)
                    FuzzyFileNavCommand.fuzzy_reload = True
                    win.run_command("fuzzy_file_nav", {"start": new_path})
                elif m.group(4):
                    # Load folder
                    new_path = path.join(FuzzyFileNavCommand.cwd, m.group(4))
                    if path.exists(new_path) and path.isdir(new_path):
                        FuzzyFileNavCommand.fuzzy_reload = True
                        win.run_command("fuzzy_file_nav", {"start": new_path})


class FuzzyRevealCommand(sublime_plugin.WindowCommand):
    def run(self):
        file_name = FuzzyPanelText.get_content()
        FuzzyPanelText.clear_content()
        if path.exists(path.join(FuzzyFileNavCommand.cwd, file_name)):
            self.window.run_command("open_dir", {"dir": FuzzyFileNavCommand.cwd, "file": file_name})
        else:
            self.window.run_command("open_dir", {"dir": FuzzyFileNavCommand.cwd, "file": ""})


class FuzzyCopyCommand(sublime_plugin.WindowCommand):
    def run(self):
        if len(Clipboard.clips):
            Clipboard.clear_entries()
        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        Clipboard.add_entry(full_name)
        Clipboard.set_action("copy")
        FuzzyFileNavCommand.fuzzy_reload = True
        self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyCutCommand(sublime_plugin.WindowCommand):
    def run(self):
        if len(Clipboard.clips):
            Clipboard.clear_entries()
        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        Clipboard.add_entry(full_name)
        Clipboard.set_action("cut")
        FuzzyFileNavCommand.fuzzy_reload = True
        self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyPasteCommand(sublime_plugin.WindowCommand):
    def run(self):
        error = False
        self.to_path = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        move = (Clipboard.action == "cut")
        self.from_path = Clipboard.clips[0]
        Clipboard.clear_entries()
        multi_file = bool(sublime.load_settings("fuzzy_file_nav.sublime-settings").get("keep_panel_open_after_action", False))

        if not multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        if path.exists(self.from_path):
            if path.isdir(self.from_path):
                self.action = shutil.copytree if not bool(move) else shutil.move
                error = self.dir_copy()
            else:
                self.action = shutil.copyfile if not bool(move) else shutil.move
                error = self.file_copy()
        if multi_file:
            if error:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})

    def dir_copy(self):
        error = False
        try:
            if path.exists(self.to_path):
                if path.isdir(self.to_path):
                    self.action(self.from_path, path.join(self.to_path, path.basename(self.from_path)))
                else:
                    error = True
                    sublime.error_message("%s already exists!" % self.to_path)
            elif path.exists(path.dirname(self.to_path)):
                self.action(self.from_path, self.to_path)
            else:
                error = True
                sublime.error_message("Cannot copy %s" % self.from_path)
        except:
            error = True
            sublime.error_message("Cannot copy %s" % self.from_path)
        return error

    def file_copy(self):
        error = False
        try:
            if path.exists(self.to_path):
                if path.isdir(self.to_path):
                    file_name = path.join(self.to_path, path.basename(self.from_path))
                    if path.exists(file_name):
                        if not sublime.ok_cancel_dialog("%s exists!\n\nOverwrite file?" % file_name):
                            return
                    self.action(self.from_path, file_name)
                elif sublime.ok_cancel_dialog("%s exists!\n\nOverwrite file?" % self.to_path):
                    self.action(self.from_path, self.to_path)
            elif path.exists(path.dirname(self.to_path)):
                self.action(self.from_path, self.to_path)
            else:
                error = True
                sublime.error_message("Cannot copy %s" % self.from_path)
        except:
            error = True
            sublime.error_message("Cannot copy %s" % self.from_path)
        return error


class FuzzyDeleteCommand(sublime_plugin.WindowCommand):
    def run(self):
        error = False
        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        multi_file = bool(sublime.load_settings("fuzzy_file_nav.sublime-settings").get("keep_panel_open_after_action", False))

        if not multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        if sublime.ok_cancel_dialog("Delete %s?\n\nWarning: this is permanent!" % full_name):
            try:
                if path.isdir(full_name):
                    shutil.rmtree(full_name)
                else:
                    os.remove(full_name)
            except:
                error = True
                sublime.error_message("Error deleting %d!" % full_name)

        if multi_file:
            if error:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyMakeFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        error = False
        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        multi_file = bool(sublime.load_settings("fuzzy_file_nav.sublime-settings").get("keep_panel_open_after_action", False))
        if not multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        try:
            with open(full_name, "a"):
                pass
            self.window.open_file(full_name)
        except:
            error = True
            sublime.error_message("Could not create %d!" % full_name)

        if multi_file:
            if error:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyMakeFolderCommand(sublime_plugin.WindowCommand):
    def run(self):
        error = False
        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        multi_file = bool(sublime.load_settings("fuzzy_file_nav.sublime-settings").get("keep_panel_open_after_action", False))
        if not multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        try:
            os.makedirs(full_name)
        except:
            error = True
            sublime.error_message("Could not create %d!" % full_name)

        if multi_file:
            if error:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyBookmarksLoadCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.display = []
        # Search through bookmarks
        bookmarks = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("bookmarks", [])
        for bm in bookmarks:
            target = bm.get("path", None)
            # Make sure bookmards point to valid locations
            if target != None and ((path.exists(target) and path.isdir(target)) or (PLATFORM == "windows" and target == u"")):
                # Only show the bookmards for this platform
                os_exclude = set(bm.get("os_exclude", []))
                if not PLATFORM in os_exclude:
                    self.display.append([bm.get("name", target), target])
        if len(self.display) > 0:
            # Display bookmarks if valid ones were found
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
            self.window.show_quick_panel(self.display, self.check_selection)

    def check_selection(self, value):
        if value > -1:
            # Load fuzzy nav with bookmarked shortcut
            self.window.run_command("fuzzy_file_nav", {"start": self.display[value][1]})


class FuzzyGetCwdCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        if FuzzyFileNavCommand.active:
            sublime.status_message("CWD: " + FuzzyFileNavCommand.cwd)


class FuzzyToggleHiddenCommand(sublime_plugin.WindowCommand):
    def run(self, show=None):
        if FuzzyFileNavCommand.active:
            FuzzyFileNavCommand.fuzzy_reload = True
            if show == None:
                FuzzyFileNavCommand.ignore_excludes = not FuzzyFileNavCommand.ignore_excludes
            elif bool(show):
                FuzzyFileNavCommand.ignore_excludes = True
            else:
                FuzzyFileNavCommand.ignore_excludes = False
            self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyStartFromFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        actions = set(["home", "bookmarks", "root"])
        # Check if you can retrieve a file name (means it exists on disk).
        view = self.window.active_view()
        name = view.file_name() if view != None else None
        if name:
            # Buffer/view has a file name, so it exists on disk; naviagte its parent directory.
            self.window.run_command("fuzzy_file_nav", {"start": path.dirname(name)})
        else:
            action = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("start_from_here_default_action", "bookmarks")
            if action in actions:
                # Load special action
                getattr(self, action)()
            else:
                # Invalid action; just load bookmarks
                self.window.run_command("fuzzy_bookmarks_load")

    def home(self):
        home = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("home", "")
        home = get_root_path() if not path.exists(home) or not path.isdir(home) else home
        self.window.run_command("fuzzy_file_nav", {"start": home})

    def root(self):
        self.window.run_command("fuzzy_file_nav")

    def bookmarks(self):
        self.window.run_command("fuzzy_bookmarks_load")


class FuzzyPathCompleteCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = FuzzyFileNavCommand.view
        complete = []
        if view != None:
            sel = view.sel()[0]
            line_text = view.substr(view.line(sel))
            for item in FuzzyFileNavCommand.files:
                # Windows is case insensitive
                i = item.lower() if PLATFORM == "windows" else item
                current = line_text.lower() if PLATFORM == "windows" else line_text

                # See if current input matches the beginning of some of the entries
                if i.startswith(current):
                    if path.isdir(path.join(FuzzyFileNavCommand.cwd, item)):
                        item = item[0:len(item) - 1]
                    complete.append(item)

            # If only one entry matches, auto-complete it
            if len(complete) == 1:
                edit = view.begin_edit()
                view.replace(edit, sublime.Region(0, view.size()), complete[0])
                view.end_edit(edit)


class FuzzyFileNavCommand(sublime_plugin.WindowCommand):
    active = False
    win_id = None
    view = None
    fuzzy_reload = False
    ignore_excludes = False
    cwd = ""

    @classmethod
    def reset(cls):
        cls.active = False
        cls.win_id = None
        cls.view = None
        cls.ignore_excludes = False
        Clipboard.clear_entries()

    def run(self, start=None):
        previous = FuzzyFileNavCommand.cwd
        FuzzyFileNavCommand.active = True
        FuzzyFileNavCommand.win_id = self.window.id()
        self.regex_exclude = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("regex_exclude", [])

        # Check if a start destination has been given
        # and ensure it is valid.
        directory = get_root_path() if start == None or not path.exists(start) or not path.isdir(start) else unicode(start)
        FuzzyFileNavCommand.cwd = directory if PLATFORM == "windows" and directory == u"" else path.normpath(directory)

        # Get and display options.
        try:
            self.display_files(FuzzyFileNavCommand.cwd)
        except:
            if FuzzyFileNavCommand.fuzzy_reload:
                # Reloading, so fuzzy panel must be up, so preserve previous state
                FuzzyFileNavCommand.fuzzy_reload = False
                FuzzyFileNavCommand.cwd = previous
            else:
                # Not reloading, so go ahead and reset the state
                FuzzyFileNavCommand.reset()
            sublime.status_message("%s is not accessible!" % FuzzyFileNavCommand.cwd)

    def get_files(self, cwd):
        # Get files/drives (windows).
        files = get_drives() if PLATFORM == "windows" and cwd == u"" else os.listdir(cwd)
        folders = []
        documents = []
        show_hidden = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("show_system_hidden_files", False)
        for f in files:
            valid = True
            full_path = path.join(cwd, f)

            # Check exclusion to omit files.
            if not self.ignore_excludes:
                if valid and not show_hidden:
                    if not PLATFORM == "windows":
                        if f.startswith('.') and f != "..":
                            valid = False
                    else:
                        attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(full_path))
                        if attrs != -1 and bool(attrs & 2):
                            valid = False

                if valid:
                    for regex in self.regex_exclude:
                        if re.match(regex, full_path):
                            valid = False

            # Store file/folder info.
            if valid:
                if not path.isdir(full_path):
                    documents.append(f)
                else:
                    folders.append(f + ("\\" if PLATFORM == "windows" else "/"))
        return [u".."] + sorted(folders) + sorted(documents)

    def display_files(self, cwd):
        # Get the folders children
        FuzzyFileNavCommand.files = self.get_files(cwd)

        # Make sure panel is down before loading a new one.
        self.window.run_command("hide_overlay")
        FuzzyFileNavCommand.view = None
        self.window.show_quick_panel(FuzzyFileNavCommand.files, self.check_selection)

    def check_selection(self, selection):
        if selection > -1:
            FuzzyFileNavCommand.fuzzy_reload = False
            # The first selection is the "go up a directory" option.
            directory = back_dir(FuzzyFileNavCommand.cwd) if selection == 0 else path.join(FuzzyFileNavCommand.cwd, FuzzyFileNavCommand.files[selection])
            FuzzyFileNavCommand.cwd = directory if PLATFORM == "windows" and directory == u"" else path.normpath(directory)

            # Check if the option is a folder or if we are at the root (needed for windows)
            try:
                if (path.isdir(FuzzyFileNavCommand.cwd) or FuzzyFileNavCommand.cwd == get_root_path()):
                    # List directories content
                    self.display_files(FuzzyFileNavCommand.cwd)
                else:
                    # Open file
                    self.window.open_file(FuzzyFileNavCommand.cwd)

                    # If multi-file open is set, leave panel open after opening file
                    if bool(sublime.load_settings("fuzzy_file_nav.sublime-settings").get("keep_panel_open_after_action", False)):
                        FuzzyFileNavCommand.cwd = path.normpath(back_dir(FuzzyFileNavCommand.cwd))
                        self.display_files(FuzzyFileNavCommand.cwd)
                    else:
                        FuzzyFileNavCommand.reset()
            except:
                # Inaccessible folder try backing up
                sublime.status_message("%s is not accessible!" % FuzzyFileNavCommand.cwd)
                FuzzyFileNavCommand.cwd = back_dir(FuzzyFileNavCommand.cwd)
                self.window.run_command("hide_overlay")
                self.display_files(FuzzyFileNavCommand.cwd)
        elif not FuzzyFileNavCommand.fuzzy_reload:
            # Reset if not reloading
            FuzzyFileNavCommand.reset()
        else:
            # Reset reload flag if reloading
            FuzzyFileNavCommand.fuzzy_reload = False
