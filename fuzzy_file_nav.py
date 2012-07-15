"""
Fuzzy File Navigation

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
"""

import sublime
import sublime_plugin
import os
import os.path as path
import re

PLATFORM = sublime.platform()


def get_root_path():
    # Windows doesn't have a root, so just
    # return an empty string to represent its root.
    return u"" if PLATFORM == "windows" else u"/"


class FuzzyEventListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        # New window gained activation? Reset fuzzy command state
        if FuzzyFileNavCommand.active and view.window() and view.window().id() != FuzzyFileNavCommand.win_id:
            FuzzyFileNavCommand.reset()
        if FuzzyFileNavCommand.active and FuzzyFileNavCommand.view_id != view.id():
            FuzzyFileNavCommand.view_id = view.id()

    def on_modified(self, view):
        if FuzzyFileNavCommand.active and FuzzyFileNavCommand.view_id and FuzzyFileNavCommand.view_id == view.id():
            sel = view.sel()[0]
            win = view.window()
            line_text = view.substr(view.line(sel))
            # Go Home
            m = re.match(r"^(?:(?:(\+)|(\-)|(~)|(\*))(?:\\|/)|([\w\W]*)\:mkdir|([\w\W]*)\:mkfile)", line_text)
            if m:
                if m.group(1):
                    FuzzyFileNavCommand.fuzzy_relaod = True
                    FuzzyFileNavCommand.ignore_excludes = True
                    win.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd, "regex_exclude": FuzzyFileNavCommand.regex_exclude})
                elif m.group(2):
                    FuzzyFileNavCommand.fuzzy_relaod = True
                    FuzzyFileNavCommand.ignore_excludes = False
                    win.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd, "regex_exclude": FuzzyFileNavCommand.regex_exclude})
                elif m.group(3):
                    FuzzyFileNavCommand.fuzzy_relaod = True
                    home = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("home", "")
                    home = get_root_path() if not path.exists(home) or not path.isdir(home) else home
                    win.run_command("fuzzy_file_nav", {"start": home, "regex_exclude": FuzzyFileNavCommand.regex_exclude})
                elif m.group(4):
                    win.run_command("hide_overlay")
                    FuzzyFileNavCommand.reset()
                    win.run_command("fuzzy_bookmarks_load")
                elif m.group(5):
                    win.run_command("hide_overlay")
                    FuzzyFileNavCommand.reset()
                    win.run_command("fuzzy_make_folder", {"cwd": FuzzyFileNavCommand.cwd, "name": m.group(2)})
                elif m.group(6):
                    win.run_command("hide_overlay")
                    FuzzyFileNavCommand.reset()
                    win.run_command("fuzzy_make_file", {"cwd": FuzzyFileNavCommand.cwd, "name": m.group(3)})


class FuzzyMakeFileCommand(sublime_plugin.WindowCommand):
    def run(self, cwd, name):
        full_name = path.join(cwd, name)
        if path.exists(cwd):
            if not path.exists(full_name):
                try:
                    with open(full_name, "a"):
                        pass
                    self.window.open_file(full_name)
                except:
                    sublime.error_message("Could not create %d!" % full_name)
            else:
                sublime.error_message("%d already exists!" % full_name)
        else:
            sublime.error_message("%d does not exist!" % cwd)


class FuzzyMakeFolderCommand(sublime_plugin.WindowCommand):
    def run(self, cwd, name):
        full_name = path.join(cwd, name)
        if path.exists(cwd):
            if not path.exists(full_name):
                try:
                    os.makedirs(full_name)
                except:
                    sublime.error_message("Could not create %d!" % full_name)
            else:
                sublime.error_message("%d already exists!" % full_name)
        else:
            sublime.error_message("%d does not exist!" % cwd)


class FuzzyBookmarksLoadCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.display = []
        self.excludes = []
        bookmarks = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("bookmarks", [])
        for bm in bookmarks:
            target = bm.get("path", None)
            if target and path.exists(target) and path.isdir(target):
                self.display.append([bm.get("name", target), target])
                self.excludes.append(bm.get("regex_exclude", []))
        if len(self.display) > 0:
            self.window.show_quick_panel(self.display, self.check_selection)

    def check_selection(self, value):
        if value > -1:
            self.window.run_command(
                "fuzzy_file_nav",
                {"start": self.display[value][1], "regex_exclude": self.excludes[value]}
            )


class FuzzyStartFromFileCommand(sublime_plugin.TextCommand):
    def run(self, edit, regex_exclude=[]):
        # Check if you can retrieve a file name (means it exists on disk).
        name = self.view.file_name()
        if name:
            self.view.window().run_command("fuzzy_file_nav", {"start": path.dirname(name), "regex_exclude": regex_exclude})


class FuzzyFileNavCommand(sublime_plugin.WindowCommand):
    active = False
    win_id = None
    view_id = None
    regex_exclude = []
    fuzzy_relaod = False
    ignore_excludes = False

    @classmethod
    def reset(cls):
        cls.active = False
        cls.win_id = None
        cls.view_id = None
        cls.ignore_excludes = False

    def run(self, start=None, regex_exclude=[]):
        if FuzzyFileNavCommand.active:
            FuzzyFileNavCommand.active = False
            self.window.run_command("hide_overlay")

        FuzzyFileNavCommand.active = True
        FuzzyFileNavCommand.view_id = None
        FuzzyFileNavCommand.win_id = self.window.id()
        FuzzyFileNavCommand.regex_exclude = regex_exclude

        # Check if a start destination has been given
        # and ensure it is valid.
        FuzzyFileNavCommand.cwd = path.normpath(get_root_path() if start == None or not path.exists(start) or not path.isdir(start) else unicode(start))

        # Get and display options.
        try:
            self.display_files(FuzzyFileNavCommand.cwd)
        except:
            FuzzyFileNavCommand.reset()
            sublime.error_message(FuzzyFileNavCommand.cwd + "is not accessible!")

    def get_files(self, cwd):
        # Get files/drives (windows).
        files = self.get_drives() if PLATFORM == "windows" and cwd == u"" else os.listdir(cwd)
        folders = []
        documents = []
        for f in files:
            valid = True
            full_path = path.join(cwd, f)

            # Check exclusion regex to omit files.
            if valid and not self.ignore_excludes:
                for regex in FuzzyFileNavCommand.regex_exclude:
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
        FuzzyFileNavCommand.files = self.get_files(cwd)
        self.window.show_quick_panel(FuzzyFileNavCommand.files, self.check_selection)

    def back_dir(self, cwd):
        prev = path.dirname(cwd)

        # On windows, if you try and get the
        # dirname of a drive, you get the drive.
        # So if the previous directory is the same
        # as the current, back out of the drive and
        # list all drives.
        return get_root_path() if prev == cwd else prev

    def get_drives(self):
        # Search through valid drive names and see if they exist.
        return [unicode(d + ":") for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if path.exists(d + ":")]

    def check_selection(self, selection):
        if selection > -1:
            FuzzyFileNavCommand.fuzzy_relaod = False
            # The first selection is the "go up a directory" option.
            FuzzyFileNavCommand.cwd = path.normpath(self.back_dir(FuzzyFileNavCommand.cwd) if selection == 0 else path.join(FuzzyFileNavCommand.cwd, FuzzyFileNavCommand.files[selection]))

            # Check if the option is a folder or if we are at the root (needed for windows)
            try:
                if (path.isdir(FuzzyFileNavCommand.cwd) or FuzzyFileNavCommand.cwd == get_root_path()):
                    self.display_files(FuzzyFileNavCommand.cwd)
                else:
                    self.window.open_file(FuzzyFileNavCommand.cwd)
                    FuzzyFileNavCommand.reset()
            except:
                # Inaccessible folder try backing up
                sublime.status_message("%s is not accessible!" % FuzzyFileNavCommand.cwd)
                FuzzyFileNavCommand.cwd = self.back_dir(FuzzyFileNavCommand.cwd)
                self.window.run_command("hide_overlay")
                self.display_files(FuzzyFileNavCommand.cwd)
        elif not FuzzyFileNavCommand.fuzzy_relaod:
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_relaod = False
