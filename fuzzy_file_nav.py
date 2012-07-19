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
CMD_WIN = r"^(?:(?:(\+)|(\-)|(~)|(\*)|(\.\.))(?:\\|/)|((?:[A-Za-z]{1}\:)?(?:\\|/))|([\w\W]*)\:mkdir|([\w\W]*)\:mkfile|([\w\W]*(?:\\|/)))"
CMD_NIX = r"^(?:(?:(\+)|(\-)|(~)|(\*)|(\.\.))/|(/)|([\w\W]*)\:mkdir|([\w\W]*)\:mkfile|([\w\W]*/))"
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
    drives = []
    for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        try:
            drive = unicode(d + ":")
            if path.exists(drive):
                drives.append(drive)
        except:
            pass
    return drives


def back_to_root(cwd):
    root = ""
    if PLATFORM != "windows":
        root = "/"
    else:
        m = re.match(WIN_DRIVE, cwd)
        if m:
            root = m.group(1)
    return unicode(root)


class FuzzyEventListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        # New window gained activation? Reset fuzzy command state
        if FuzzyFileNavCommand.active and view.window() and view.window().id() != FuzzyFileNavCommand.win_id:
            FuzzyFileNavCommand.reset()
        if FuzzyFileNavCommand.active and (FuzzyFileNavCommand.view == None or FuzzyFileNavCommand.view.id() != view.id()):
            FuzzyFileNavCommand.view = view

    def on_query_context(self, view, key, operator, operand, match_all):
        active = FuzzyFileNavCommand.active == operand
        if FuzzyFileNavCommand.view != None and FuzzyFileNavCommand.view.id() == view.id():
            if key == "fuzzy_path_complete":
                return active
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
                    # Show hidden files/folders from regex_exclude
                    FuzzyFileNavCommand.fuzzy_relaod = True
                    FuzzyFileNavCommand.ignore_excludes = True
                    win.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})
                elif m.group(2):
                    # Hide files/folders via regex_exclude
                    FuzzyFileNavCommand.fuzzy_relaod = True
                    FuzzyFileNavCommand.ignore_excludes = False
                    win.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})
                elif m.group(3):
                    # Go Home
                    FuzzyFileNavCommand.fuzzy_relaod = True
                    home = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("home", "")
                    home = get_root_path() if not path.exists(home) or not path.isdir(home) else home
                    win.run_command("fuzzy_file_nav", {"start": home})
                elif m.group(4):
                    # Load bookmark menu
                    win.run_command("hide_overlay")
                    FuzzyFileNavCommand.reset()
                    win.run_command("fuzzy_bookmarks_load")
                elif m.group(5):
                    # Back a directory
                    FuzzyFileNavCommand.fuzzy_relaod = True
                    win.run_command("fuzzy_file_nav", {"start": back_dir(FuzzyFileNavCommand.cwd)})
                elif m.group(6):
                    # Go to root of drive/computer
                    if PLATFORM == "windows" and re.match(WIN_DRIVE, line_text):
                        try:
                            if path.exists(line_text):
                                new_path = line_text.upper()
                            else:
                                return
                        except:
                            return
                    else:
                        new_path = back_to_root(FuzzyFileNavCommand.cwd)
                    FuzzyFileNavCommand.fuzzy_relaod = True
                    win.run_command("fuzzy_file_nav", {"start": new_path})
                elif m.group(7):
                    # Make directory
                    win.run_command("hide_overlay")
                    FuzzyFileNavCommand.reset()
                    win.run_command("fuzzy_make_folder", {"cwd": FuzzyFileNavCommand.cwd, "name": m.group(7)})
                elif m.group(8):
                    # Create new file
                    win.run_command("hide_overlay")
                    FuzzyFileNavCommand.reset()
                    win.run_command("fuzzy_make_file", {"cwd": FuzzyFileNavCommand.cwd, "name": m.group(8)})
                elif m.group(9):
                    # Load folder
                    new_path = path.join(FuzzyFileNavCommand.cwd, m.group(9))
                    try:
                        if path.exists(new_path) and path.isdir(new_path):
                            FuzzyFileNavCommand.fuzzy_relaod = True
                            win.run_command("fuzzy_file_nav", {"start": new_path})
                    except:
                        return


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
        bookmarks = sublime.load_settings("fuzzy_file_nav.sublime-settings").get("bookmarks", [])
        for bm in bookmarks:
            target = bm.get("path", None)
            if target != None and ((path.exists(target) and path.isdir(target)) or (PLATFORM == "windows" and target == u"")):
                os_exclude = set(bm.get("os_exclude", []))
                if not PLATFORM in os_exclude:
                    self.display.append([bm.get("name", target), target])
        if len(self.display) > 0:
            self.window.show_quick_panel(self.display, self.check_selection)

    def check_selection(self, value):
        if value > -1:
            self.window.run_command("fuzzy_file_nav", {"start": self.display[value][1]})


class FuzzyStartFromFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        # Check if you can retrieve a file name (means it exists on disk).
        view = self.window.active_view()
        name = view.file_name() if view != None else None
        if name:
            self.window.run_command("fuzzy_file_nav", {"start": path.dirname(name)})
        else:
            self.window.run_command("fuzzy_bookmarks_load")


class FuzzyPathCompleteCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = FuzzyFileNavCommand.view
        complete = []
        if view != None:
            sel = view.sel()[0]
            line_text = view.substr(view.line(sel))
            for item in FuzzyFileNavCommand.files:
                i = item.lower() if PLATFORM == "windows" else item
                current = line_text.lower() if PLATFORM == "windows" else line_text
                if i.startswith(current):
                    try:
                        if path.isdir(path.join(FuzzyFileNavCommand.cwd, item)):
                            item = item[0:len(item) - 1]
                        complete.append(item)
                    except:
                        pass
            if len(complete) == 1:
                edit = view.begin_edit()
                view.replace(edit, sublime.Region(0, view.size()), complete[0])
                view.end_edit(edit)


class FuzzyFileNavCommand(sublime_plugin.WindowCommand):
    active = False
    win_id = None
    view = None
    fuzzy_relaod = False
    ignore_excludes = False

    @classmethod
    def reset(cls):
        cls.active = False
        cls.win_id = None
        cls.view = None
        cls.ignore_excludes = False

    def run(self, start=None):
        if FuzzyFileNavCommand.active:
            FuzzyFileNavCommand.active = False
            self.window.run_command("hide_overlay")

        FuzzyFileNavCommand.active = True
        FuzzyFileNavCommand.view = None
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
            FuzzyFileNavCommand.reset()
            sublime.error_message(FuzzyFileNavCommand.cwd + " is not accessible!")

    def get_files(self, cwd):
        # Get files/drives (windows).
        files = get_drives() if PLATFORM == "windows" and cwd == u"" else os.listdir(cwd)
        folders = []
        documents = []
        for f in files:
            valid = True
            full_path = path.join(cwd, f)

            # Check exclusion regex to omit files.
            if valid and not self.ignore_excludes:
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
        FuzzyFileNavCommand.files = self.get_files(cwd)
        self.window.show_quick_panel(FuzzyFileNavCommand.files, self.check_selection)

    def check_selection(self, selection):
        if selection > -1:
            FuzzyFileNavCommand.fuzzy_relaod = False
            # The first selection is the "go up a directory" option.
            directory = back_dir(FuzzyFileNavCommand.cwd) if selection == 0 else path.join(FuzzyFileNavCommand.cwd, FuzzyFileNavCommand.files[selection])
            FuzzyFileNavCommand.cwd = directory if PLATFORM == "windows" and directory == u"" else path.normpath(directory)

            # Check if the option is a folder or if we are at the root (needed for windows)
            try:
                if (path.isdir(FuzzyFileNavCommand.cwd) or FuzzyFileNavCommand.cwd == get_root_path()):
                    self.display_files(FuzzyFileNavCommand.cwd)
                else:
                    self.window.open_file(FuzzyFileNavCommand.cwd)
                    if bool(sublime.load_settings("fuzzy_file_nav.sublime-settings").get("multi_file_open", False)):
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
        elif not FuzzyFileNavCommand.fuzzy_relaod:
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_relaod = False
