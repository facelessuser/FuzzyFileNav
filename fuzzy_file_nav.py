"""
Fuzzy File Navigation.

Licensed under MIT
Copyright (c) 2012 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
import os
import os.path as path
import re
import shutil
import glob
from FuzzyFileNav.multiconf import get as qualify_settings
from FuzzyFileNav.notify import error, notify
import platform
if platform.system() == "Windows":
    import ctypes

FUZZY_SETTINGS = "fuzzy_file_nav.sublime-settings"
CMD_WIN = r"^(?:(?:(~)|(\.\.))(?:\\|/)|((?:[A-Za-z]{1}:)?(?:\\|/))|([\w\W]*(?:\\|/)))$"
CMD_NIX = r"^(?:(?:(~)|(\.\.))/|(/)|([\w\W]*/))$"
WIN_DRIVE = r"(^[A-Za-z]{1}:(?:\\|/))"
PLATFORM = None


def debug_log(s):
    """Debug log."""
    if sublime.load_settings(FUZZY_SETTINGS).get("debug", False):
        print("FuzzyFileNav: %s" % s)


def status_cwd():
    """Set the status bar to the current working directory."""

    if FuzzyFileNavCommand.status:
        sublime.run_command("fuzzy_get_cwd")
        sublime.set_timeout(status_cwd, 1000)


def get_root_path():
    """
    Get the root path.

    Windows doesn't have a root, so just
    return an empty string to represent its root.
    """

    return "" if PLATFORM == "windows" else "/"


def get_path_true_case(pth):
    """
    Get the true case for the given path.

    This is mainly for windows;
    OSX and Linux will just return the same path.
    """
    if PLATFORM == "windows":
        # http://stackoverflow.com/a/14742779
        true_path = None
        if path.exists(pth):
            glob_test = []
            parts = path.normpath(pth).split('\\')
            glob_test.append(parts[0].upper())
            for p in parts[1:]:
                glob_test.append("%s[%s]" % (p[:-1], p[-1]))
            results = glob.glob('\\'.join(glob_test))
            if results is not None:
                true_path = results[0]
    else:
        true_path = pth
    return true_path


def expanduser(path, default):
    """Expand the path by converting ~ to the user path."""

    return os.path.expanduser(path) if path is not None else path


def back_dir(cwd):
    """Step back a directory."""

    prev = path.dirname(cwd)

    # On windows, if you try and get the
    # dirname of a drive, you get the drive.
    # So if the previous directory is the same
    # as the current, back out of the drive and
    # list all drives.
    return get_root_path() if prev == cwd else prev


def get_drives():
    """Search through valid drive names and see if they exist."""

    return [d + ":" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if path.exists(d + ":")]


def back_to_root(cwd):
    """Back to the root directory."""

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
    return root


class FuzzyEditGlobal(object):
    """Class containing global variables to store buffers and regions for editing."""

    bfr = None
    region = None

    @classmethod
    def clear(cls):
        """Clear buffer and region."""

        cls.bfr = None
        cls.region = None


class FuzzyApplyEditsCommand(sublime_plugin.TextCommand):
    """Applies edits to a view."""

    def run(self, edit):
        """Run the command."""

        self.view.replace(edit, FuzzyEditGlobal.region, FuzzyEditGlobal.bfr)


class FuzzyPanelText(object):
    """Object to track panel content."""

    content = ""

    @classmethod
    def set_content(cls, txt):
        """Set content."""

        cls.content = txt

    @classmethod
    def get_content(cls):
        """Return the content."""
        txt = cls.content
        return txt

    @classmethod
    def clear_content(cls):
        """Clear the content."""

        cls.content = ""


class FuzzyEventListener(sublime_plugin.EventListener):
    """Listener that detects panel closes, shortcuts pressed in the panel, and panel content changes."""

    def on_activated(self, view):
        """Track when fuzzy panels are activated or deactivated."""

        # New window gained activation? Reset fuzzy command state
        if FuzzyFileNavCommand.active and view.window() and view.window().id() != FuzzyFileNavCommand.win_id:
            FuzzyFileNavCommand.reset()
        # View has not been assinged yet since fuzzy nav panel appeared; assign it
        if (
            FuzzyFileNavCommand.active and
            (FuzzyFileNavCommand.view is None or FuzzyFileNavCommand.view.id() != view.id())
        ):
            FuzzyFileNavCommand.view = view

    def on_query_context(self, view, key, operator, operand, match_all):
        """Capture shortcuts in a FuzzyNavPanel."""

        active = FuzzyFileNavCommand.active is True
        if active and FuzzyFileNavCommand.view is not None and FuzzyFileNavCommand.view.id() == view.id():
            FuzzyPanelText.set_content(view.substr(view.line(view.sel()[0])))
            full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
            empty = (FuzzyPanelText.get_content() == "")
            # See if this is the auto-complete path command
            if key in [
                "fuzzy_path_complete", "fuzzy_path_complete_back", "fuzzy_toggle_hidden",
                "fuzzy_bookmarks_load", "fuzzy_get_cwd", "fuzzy_cwv"
            ]:
                return active
            elif key == "fuzzy_open_folder":
                if (
                    (
                        (not empty and path.exists(full_name) and path.isdir(full_name)) or
                        (empty and path.exists(FuzzyFileNavCommand.cwd))
                    )
                ):
                    return active
            elif key in ["fuzzy_reveal", "fuzzy_search"]:
                if path.exists(FuzzyFileNavCommand.cwd):
                    return active
                else:
                    notify("%s does not exist!" % FuzzyFileNavCommand.cwd)
            elif key in ["fuzzy_quick_open"]:
                sels = view.sel()
                if len(sels) == 1:
                    if sels[0].a == sels[0].b and sels[0].a == view.size():
                        return active
                    else:
                        pass
            elif key in ["fuzzy_delete", "fuzzy_rename", "fuzzy_duplicate"]:
                if not empty and path.exists(full_name):
                    return active
                elif not empty:
                    notify("%s does not exist!" % full_name)
            elif key in ["fuzzy_make_file", "fuzzy_make_folder"]:
                if not empty and not path.exists(full_name):
                    return active
                elif not empty:
                    notify("%s already exists!" % full_name)
            elif key == "fuzzy_save_as":
                if not empty and (not path.exists(full_name) or not path.isdir(full_name)):
                    return active
                elif not empty:
                    notify("%s is a directory!" % full_name)
            elif key == "fuzzy_copy":
                if not empty and path.exists(full_name):
                    return active
                elif not empty:
                    notify("%s does not exist!" % full_name)
            elif key == "fuzzy_cut":
                if path.exists(FuzzyFileNavCommand.cwd):
                    return active
                else:
                    notify("%s does not exist!" % FuzzyFileNavCommand.cwd)
            elif key == "fuzzy_paste":
                if path.exists(FuzzyFileNavCommand.cwd) and len(FuzzyClipboardCommand.clips):
                    return active
                elif not len(FuzzyClipboardCommand.clips):
                    notify("Clipboard is empty!")
                else:
                    notify("%s does not exist!" % FuzzyFileNavCommand.cwd)
        return False

    def on_modified(self, view):
        """Monitor content change in the panel and take actions accordingly."""

        if (
            FuzzyFileNavCommand.active and FuzzyFileNavCommand.view is not None and
            FuzzyFileNavCommand.view.id() == view.id()
        ):
            sel = view.sel()[0]
            win = view.window()
            line_text = view.substr(view.line(sel))
            FuzzyPathCompleteCommand.update_autocomplete(line_text)
            regex = CMD_WIN if PLATFORM == "windows" else CMD_NIX
            m = re.match(regex, line_text)
            if m:
                if m.group(1):
                    # Go Home
                    FuzzyFileNavCommand.fuzzy_reload = True
                    home = qualify_settings(sublime.load_settings(FUZZY_SETTINGS), "home", "", expanduser)
                    home = get_root_path() if not path.exists(home) or not path.isdir(home) else home
                    win.run_command("hide_overlay")
                    win.run_command("fuzzy_file_nav", {"start": home})
                elif m.group(2):
                    # Back a directory
                    FuzzyFileNavCommand.fuzzy_reload = True
                    win.run_command("hide_overlay")
                    win.run_command("fuzzy_file_nav", {"start": back_dir(FuzzyFileNavCommand.cwd)})
                elif m.group(3):
                    # Go to root of drive/computer
                    if PLATFORM == "windows" and re.match(WIN_DRIVE, line_text):
                        if path.exists(line_text):
                            new_path = line_text.upper()
                    else:
                        new_path = back_to_root(FuzzyFileNavCommand.cwd)
                    FuzzyFileNavCommand.fuzzy_reload = True
                    win.run_command("hide_overlay")
                    win.run_command("fuzzy_file_nav", {"start": new_path})
                elif m.group(4):
                    # Load folder
                    new_path = path.join(FuzzyFileNavCommand.cwd, m.group(4))
                    if path.exists(new_path) and path.isdir(new_path):
                        FuzzyFileNavCommand.fuzzy_reload = True
                        win.run_command("hide_overlay")
                        win.run_command("fuzzy_file_nav", {"start": new_path})


class FuzzyOpenFolderCommand(sublime_plugin.WindowCommand):
    """Open folders in project."""

    def compare_relative(self, proj_folder, new_folder, proj_file):
        """Compare folder to relative path."""

        if proj_file is None:
            return self.compare_absolute(proj_folder, new_folder)
        return path.relpath(new_folder, path.dirname(proj_file)) == proj_folder

    def compare_absolute(self, proj_folder, new_folder):
        """Compare folder to absolute path."""

        return proj_folder == new_folder

    def compare(self, folders, new_folder, proj_file):
        """Check if folder exists in the project."""

        already_exists = False
        for folder in folders:
            if PLATFORM == "windows":
                if re.match(WIN_DRIVE, folder["path"]) is not None:
                    already_exists = self.compare_absolute(folder["path"].lower(), new_folder.lower())
                else:
                    already_exists = self.compare_relative(
                        folder["path"].lower(), new_folder.lower(), proj_file.lower()
                    )
            else:
                if folder["path"].startswith("/"):
                    already_exists = self.compare_absolute(folder["path"], new_folder)
                else:
                    already_exists = self.compare_relative(folder["path"], new_folder, proj_file)
            if already_exists:
                break
        return already_exists

    def run(self):
        """Run the command."""

        file_name = FuzzyPanelText.get_content()
        FuzzyPanelText.clear_content()
        proj_file = self.window.project_file_name()
        data = self.window.project_data()
        if data is None:
            data = {}
        new_folder = path.join(FuzzyFileNavCommand.cwd, file_name)
        if not path.exists(new_folder):
            return
        if not path.isdir(new_folder):
            new_folder = path.dirname(new_folder)
        if "folders" not in data:
            data["folders"] = []
        already_exists = self.compare(data["folders"], new_folder, proj_file)

        if not already_exists:
            true_path = get_path_true_case(new_folder)
            if true_path is not None:
                if (
                    sublime.load_settings(FUZZY_SETTINGS).get("add_folder_to_project_relative", False) and
                    proj_file is not None
                ):
                    new_folder = path.relpath(new_folder, path.dirname(proj_file))
                follow_sym = sublime.load_settings(FUZZY_SETTINGS).get("add_folder_to_project_follow_symlink", True)
                data["folders"].append({'follow_symlinks': follow_sym, 'path': new_folder})
                self.window.set_project_data(data)
            else:
                error("Couldn't resolve case for path %s!" % new_folder)


class FuzzyProjectFolderLoadCommand(sublime_plugin.WindowCommand):
    """Load folder content in quick panel."""

    def run(self):
        """Run command."""

        if FuzzyFileNavCommand.active:
            self.window.run_command("hide_overlay")
        self.display = []
        proj_file = self.window.project_file_name()
        data = self.window.project_data()
        if data is None:
            data = {}
        if "folders" not in data:
            data["folders"] = []
        for folder in data["folders"]:
            if (
                (PLATFORM == "windows" and re.match(WIN_DRIVE, folder["path"]) is None and proj_file is not None) or
                (PLATFORM != "windows" and not folder["path"].startswith("/") and proj_file is not None)
            ):
                self.display.append(
                    get_path_true_case(path.abspath(path.join(path.dirname(proj_file), folder["path"])))
                )
            else:
                self.display.append(get_path_true_case(folder["path"]))

        if len(self.display):
            self.window.show_quick_panel([path.basename(x) for x in self.display], self.check_selection)

    def check_selection(self, value):
        """Check the user's selection."""

        if value > -1:
            # Load fuzzy nav with project folder
            self.window.run_command("fuzzy_file_nav", {"start": self.display[value]})


class FuzzyCurrentWorkingViewCommand(sublime_plugin.TextCommand):
    """Insert current working directory into panel."""

    def run(self, edit):
        """Run command."""

        name = None
        win = sublime.active_window()
        if win is not None:
            cwv = win.active_view()
            if cwv is not None:
                file_name = cwv.file_name()
                if file_name is not None:
                    name = path.basename(file_name)
        if name is not None:
            view = FuzzyFileNavCommand.view
            FuzzyEditGlobal.bfr = name
            FuzzyEditGlobal.region = sublime.Region(0, view.size())
            view.run_command("fuzzy_apply_edits")
            FuzzyEditGlobal.clear()
            sels = view.sel()
            sels.clear()
            sels.add(sublime.Region(view.size()))


class FuzzyRevealCommand(sublime_plugin.WindowCommand):
    """Reveal the file/folder in file browser."""

    def run(self):
        """Run command."""

        file_name = FuzzyPanelText.get_content()
        FuzzyPanelText.clear_content()
        if path.exists(path.join(FuzzyFileNavCommand.cwd, file_name)):
            self.window.run_command("open_dir", {"dir": FuzzyFileNavCommand.cwd, "file": file_name})
        else:
            self.window.run_command("open_dir", {"dir": FuzzyFileNavCommand.cwd, "file": ""})


class FuzzySearchFolderCommand(sublime_plugin.WindowCommand):
    """Initiate Sublime's folder search."""

    def run(self):
        """Run command."""

        file_name = FuzzyPanelText.get_content()
        FuzzyPanelText.clear_content()
        folder = path.join(FuzzyFileNavCommand.cwd, file_name)
        if path.exists(folder) and path.isdir(folder):
            self.window.run_command("show_panel", {"panel": "find_in_files", "where": folder})
        else:
            self.window.run_command("show_panel", {"panel": "find_in_files", "where": FuzzyFileNavCommand.cwd})


class FuzzyClipboardCommand(sublime_plugin.WindowCommand):
    """Command to handle fuzzy cut/copy/paste actions."""

    clips = []
    action = None

    def run(self, action):
        """Run command."""

        self.cls = FuzzyClipboardCommand
        if action in ["cut", "copy"]:
            if len(self.cls.clips):
                self.cls.clear_entries()
            full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
            FuzzyPanelText.clear_content()
            self.cls.add_entry(full_name)
            self.cls.set_action(action)
            FuzzyFileNavCommand.fuzzy_reload = True
            self.window.run_command("hide_overlay")
            self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})
        elif action == "paste":
            self.paste()

    def paste(self):
        """Paste files."""

        errors = False
        self.to_path = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        move = (self.cls.action == "cut")
        self.from_path = self.cls.clips[0]
        # self.cls.clear_entries()
        multi_file = (
            bool(sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_after_action", False)) and
            "paste" not in sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_exceptions", [])
        )

        if not multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        if path.exists(self.from_path):
            if path.isdir(self.from_path):
                self.action = shutil.copytree if not bool(move) else shutil.move
                errors = self.dir_copy()
            else:
                self.action = shutil.copyfile if not bool(move) else shutil.move
                errors = self.file_copy()
        if multi_file:
            if errors:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("hide_overlay")
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})

    def dir_copy(self):
        """Handle directory copy."""

        errors = False
        try:
            if path.exists(self.to_path):
                if path.isdir(self.to_path):
                    dest = path.join(self.to_path, path.basename(self.from_path))
                    if path.exists(dest) and sublime.ok_cancel_dialog('Overwrite?'):
                        if path.isdir(dest):
                            shutil.rmtree(dest)
                        else:
                            os.remove(dest)
                    self.action(self.from_path, path.join(self.to_path, path.basename(self.from_path)))
                else:
                    errors = True
                    error("%s already exists!" % self.to_path)
            elif path.exists(path.dirname(self.to_path)):
                if path.exists(self.to_path) and sublime.ok_cancel_dialog('Overwrite?'):
                    if path.isdir(self.to_path):
                        shutil.rmtree(self.to_path)
                    else:
                        os.remove(self.to_path)
                self.action(self.from_path, self.to_path)
            else:
                errors = True
                error("Cannot copy %s" % self.from_path)
        except Exception:
            errors = True
            error("Cannot copy %s" % self.from_path)
        return errors

    def file_copy(self):
        """Hanlde file copy."""

        errors = False
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
                errors = True
                error("Cannot copy %s" % self.from_path)
        except Exception:
            errors = True
            error("Cannot copy %s" % self.from_path)
        return errors

    @classmethod
    def add_entry(cls, entry):
        """Add entry to clip board."""

        if entry not in cls.clips:
            cls.clips.append(entry)

    @classmethod
    def set_action(cls, action):
        """Set the action."""

        cls.action = action

    @classmethod
    def clear_entries(cls):
        """Clear entries."""

        cls.clips = []
        cls.action = None


class FuzzyDeleteCommand(sublime_plugin.WindowCommand):
    """Delete file/folder."""

    def run(self):
        """Run command."""

        errors = False
        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        multi_file = (
            bool(sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_after_action", False)) and
            "delete" not in sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_exceptions", [])
        )

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
            except Exception:
                errors = True
                error("Error deleting %s!" % full_name)

        if multi_file:
            if errors:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("hide_overlay")
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzySaveFileCommand(sublime_plugin.WindowCommand):
    """Save file."""

    def save(self):
        """Perform save."""

        if self.view.is_loading():
            sublime.set_timeout(self.save, 100)
        else:
            FuzzyEditGlobal.bfr = self.bfr
            FuzzyEditGlobal.region = sublime.Region(0, self.view.size())
            self.view.run_command("fuzzy_apply_edits")
            FuzzyEditGlobal.clear()
            sels = self.view.sel()
            sels.clear()
            sels.add_all(self.current_sels)
            self.window.focus_view(self.view)
            self.view.set_viewport_position(self.position)
            self.view.run_command("save")
            if self.multi_file:
                self.window.run_command("hide_overlay")
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})

    def run(self):
        """Run command."""

        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        file_exists = path.exists(full_name)
        if file_exists:
            if not sublime.ok_cancel_dialog("%s exists!\n\nOverwrite file?" % full_name):
                return

        FuzzyPanelText.clear_content()
        self.multi_file = (
            bool(sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_after_action", False)) and
            "saveas" not in sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_exceptions", [])
        )
        active_view = self.window.active_view()
        if active_view is None:
            return
        self.bfr = active_view.substr(sublime.Region(0, active_view.size()))
        self.current_sels = [s for s in active_view.sel()]
        self.position = active_view.viewport_position()
        if not self.multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        try:
            if not file_exists:
                with open(full_name, "a"):
                    pass
            active_view.set_scratch(True)
            self.window.run_command("close")
            self.view = self.window.open_file(full_name)
            sublime.set_timeout(self.save, 100)
        except Exception:
            error("Could not create %s!" % full_name)
            if self.multi_file:
                FuzzyFileNavCommand.reset()


class FuzzyMakeFileCommand(sublime_plugin.WindowCommand):
    """Create a file."""

    def run(self):
        """Run command."""

        errors = False
        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        multi_file = (
            bool(sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_after_action", False)) and
            "mkfile" not in sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_exceptions", [])
        )
        if not multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        try:
            with open(full_name, "a"):
                pass
            self.window.open_file(full_name)
        except Exception:
            errors = True
            error("Could not create %s!" % full_name)

        if multi_file:
            if errors:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("hide_overlay")
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyMakeFolderCommand(sublime_plugin.WindowCommand):
    """Create a folder."""

    def run(self):
        """Run command."""

        errors = False
        full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        multi_file = (
            bool(sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_after_action", False)) and
            "mkdir" not in sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_exceptions", [])
        )
        if not multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        try:
            os.makedirs(full_name)
        except Exception:
            errors = True
            error("Could not create %s!" % full_name)

        if multi_file:
            if errors:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("hide_overlay")
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyRenameCommand(sublime_plugin.WindowCommand):
    """Rename a file or directory."""

    def on_done(self, name):
        """Finalize rename."""

        if name == self.basename:      # same name, do nothing
            self.on_finish()
            return

        new = self.dir + os.sep + name
        try:
            os.rename(self.full_name, new)

            # close and open renamed file if among open files
            current_view = self.window.active_view()
            current_file = current_view.file_name()
            for v in self.window.views():
                if v.file_name() == self.full_name:
                    self.window.focus_view(v)
                    v.set_scratch(True)
                    self.window.run_command('close_file')
                    self.window.open_file(new)
                    if current_file != self.full_name:
                        sublime.set_timeout(lambda: self.window.focus_view(current_view), 100)
                    break

        except Exception:
            self.errors = True
            error("Could not rename %s!" % self.full_name)
        self.on_finish()

    def on_finish(self):
        """Further actions."""

        if self.multi_file:
            if self.errors:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("hide_overlay")
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})

    def run(self):
        """Run command."""

        self.errors = False
        self.full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        self.multi_file = (
            bool(sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_after_action", False)) and
            "rename" not in sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_exceptions", [])
        )

        if not self.multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        if os.path.isdir(self.full_name):
            self.dir = os.path.dirname(self.full_name)
            self.basename = os.path.basename(self.full_name)
        else:
            self.dir, self.basename = os.path.split(self.full_name)

        self.window.show_input_panel("Rename file to:", self.basename, self.on_done, None, self.on_finish)


class FuzzyDuplicateCommand(sublime_plugin.WindowCommand):
    """Duplicate a file or directory."""

    def on_done(self, name):
        """Finalize duplicate."""

        if name == self.basename:      # same name, do nothing
            self.on_finish()
            return

        new = self.dir + os.sep + name
        try:
            if self.is_dir:
                shutil.copytree(self.full_name, new, symlinks=True)
            else:
                shutil.copyfile(self.full_name, new)
        except Exception:
            self.errors = True
            error("Could not duplicate %s!" % self.full_name)
        self.on_finish()

    def on_finish(self):
        """Further actions."""

        if self.multi_file:
            if self.errors:
                FuzzyFileNavCommand.reset()
            else:
                self.window.run_command("hide_overlay")
                self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})

    def run(self):
        """Run command."""

        self.errors = False
        self.full_name = path.join(FuzzyFileNavCommand.cwd, FuzzyPanelText.get_content())
        FuzzyPanelText.clear_content()
        self.multi_file = (
            bool(sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_after_action", False)) and
            "rename" not in sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_exceptions", [])
        )

        if not self.multi_file:
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
        else:
            FuzzyFileNavCommand.fuzzy_reload = True

        if os.path.isdir(self.full_name):
            self.is_dir = True
            self.dir = os.path.dirname(self.full_name)
            self.basename = os.path.basename(self.full_name)
        else:
            self.is_dir = False
            self.dir, self.basename = os.path.split(self.full_name)

        self.window.show_input_panel("Duplicate to:", self.basename, self.on_done, None, self.on_finish)


class FuzzyBookmarksLoadCommand(sublime_plugin.WindowCommand):
    """Load bookmarks in panel."""

    def run(self):
        """Run command."""

        if FuzzyFileNavCommand.active:
            self.window.run_command("hide_overlay")
        self.display = []
        # Search through bookmarks
        bookmarks = sublime.load_settings(FUZZY_SETTINGS).get("bookmarks", [])
        for bm in bookmarks:
            # Only show bookmarks that are for this host and/or platform
            target = qualify_settings(bm, "path", None, expanduser)
            # Make sure bookmards point to valid locations
            if (
                target is not None and
                ((path.exists(target) and path.isdir(target)) or (PLATFORM == "windows" and target == ""))
            ):
                self.display.append([bm.get("name", target), target])
        if len(self.display) > 0:
            # Display bookmarks if valid ones were found
            self.window.run_command("hide_overlay")
            FuzzyFileNavCommand.reset()
            self.window.show_quick_panel(self.display, self.check_selection)

    def check_selection(self, value):
        """Check the user's selection and navigate the folder."""

        if value > -1:
            # Load fuzzy nav with bookmarked shortcut
            self.window.run_command("fuzzy_file_nav", {"start": self.display[value][1]})


class FuzzyGetCwdCommand(sublime_plugin.ApplicationCommand):
    """Show the current working directory in the status bar."""

    def run(self):
        """Run command."""

        if FuzzyFileNavCommand.active:
            sublime.status_message("CWD: " + FuzzyFileNavCommand.cwd)


class FuzzyToggleHiddenCommand(sublime_plugin.WindowCommand):
    """Toggle whether hidden files are shown or hidden."""

    def run(self, show=None):
        """Run command."""

        if FuzzyFileNavCommand.active:
            FuzzyFileNavCommand.fuzzy_reload = True
            if show is None:
                FuzzyFileNavCommand.hide_hidden = not FuzzyFileNavCommand.hide_hidden
            elif bool(show):
                FuzzyFileNavCommand.hide_hidden = True
            else:
                FuzzyFileNavCommand.hide_hidden = False
            self.window.run_command("hide_overlay")
            self.window.run_command("fuzzy_file_nav", {"start": FuzzyFileNavCommand.cwd})


class FuzzyStartFromFileCommand(sublime_plugin.WindowCommand):
    """Start navigating from the folder, project, file system root, or bookmarks."""

    def run(self, paths=[]):
        """Run command."""

        if FuzzyFileNavCommand.active:
            self.window.run_command("hide_overlay")
        name = self.get_target(paths)
        actions = set(["home", "bookmarks", "root", "project"])
        # Check if you can retrieve a file name (means it exists on disk).
        if name is None:
            view = self.window.active_view()
            name = view.file_name() if view is not None else None
        if name:
            # Buffer/view has a file name, so it exists on disk; naviagte its parent directory.
            self.window.run_command(
                "fuzzy_file_nav",
                {
                    "start": path.dirname(name) if not path.isdir(name) else name
                }
            )
        else:
            action = sublime.load_settings(FUZZY_SETTINGS).get("start_from_here_default_action", "bookmarks")
            if action in actions:
                # Load special action
                debug_log("Load default action: %s" % action)
                getattr(self, action)()
            else:
                # Invalid action; just load bookmarks
                self.window.run_command("fuzzy_bookmarks_load")
                debug_log("Load bookmarks")

    def get_target(self, paths=[]):
        """Get the target to navigate from."""

        target = None
        if len(paths) and path.exists(paths[0]):
            target = paths[0]
        return target

    def project(self):
        """Get folders from project."""

        data = self.window.project_data()
        if data is None:
            data = {}
        if "folders" not in data:
            folders = []

        if len(folders):
            self.window.run_command("fuzzy_project_folder_load")
        else:
            self.home()

    def home(self):
        """Navigate from home."""

        home = qualify_settings(sublime.load_settings(FUZZY_SETTINGS), "home", "", expanduser)
        home = get_root_path() if not path.exists(home) or not path.isdir(home) else home
        self.window.run_command("fuzzy_file_nav", {"start": home})

    def root(self):
        """Navigate from root of file system."""

        self.window.run_command("fuzzy_file_nav")

    def bookmarks(self):
        """Load bookmarks."""

        if len(sublime.load_settings(FUZZY_SETTINGS).get("bookmarks", [])):
            self.window.run_command("fuzzy_bookmarks_load")
        else:
            self.home()


class FuzzyQuickOpenCommand(sublime_plugin.WindowCommand):
    """Mimic open file when the right arrow key is pressed (like sublime does)."""

    def run(self):
        """Run command."""

        hl_index = FuzzyPathCompleteCommand.hl_index
        if hl_index != -1 or hl_index < len(FuzzyFileNavCommand.files):
            file_path = path.join(FuzzyFileNavCommand.cwd, FuzzyFileNavCommand.files[hl_index])
            if not path.isdir(file_path):
                self.window.open_file(file_path)


class FuzzyPathCompleteCommand(sublime_plugin.WindowCommand):
    """Complete a path when 'tab' is pressed."""

    last = None
    in_progress = False
    text = None
    hl_index = -1

    def run(self, back=False):
        """Run command."""
        cls = FuzzyPathCompleteCommand
        view = FuzzyFileNavCommand.view
        settings = sublime.load_settings(FUZZY_SETTINGS)
        completion_style = settings.get("completion_style", "fuzzy")
        if view is not None:
            if completion_style == "fuzzy":
                self.sublime_completion(cls, view)
            else:
                nix_path_complete = completion_style == "nix"
                self.terminal_completion(cls, view, back, nix_path_complete)

    def sublime_completion(self, cls, view):
        """Sublime fuzzy completion."""

        if cls.hl_index != -1 or cls.hl_index < len(FuzzyFileNavCommand.files):
            FuzzyEditGlobal.bfr = FuzzyFileNavCommand.files[cls.hl_index]
            if path.isdir(path.join(FuzzyFileNavCommand.cwd, FuzzyEditGlobal.bfr)):
                FuzzyEditGlobal.bfr = FuzzyEditGlobal.bfr[0:len(FuzzyEditGlobal.bfr) - 1]
            FuzzyEditGlobal.region = sublime.Region(0, view.size())
            view.run_command("fuzzy_apply_edits")
            FuzzyEditGlobal.clear()
            sels = view.sel()
            sels.clear()
            sels.add(sublime.Region(view.size()))

    def terminal_completion(self, cls, view, back, nix_path_complete):
        """Terminal style completion."""

        complete = []
        case_insensitive = PLATFORM == "windows" or not nix_path_complete
        sel = view.sel()[0]

        if cls.text is None:
            cls.text = view.substr(view.line(sel))
        debug_log("completion text - " + cls.text)
        current = cls.text.lower() if case_insensitive else cls.text
        for item in FuzzyFileNavCommand.files:
            # Windows is case insensitive
            i = item.lower() if case_insensitive else item
            # See if current input matches the beginning of some of the entries
            if i.startswith(current):
                if path.isdir(path.join(FuzzyFileNavCommand.cwd, item)):
                    item = item[0:len(item) - 1]
                complete.append(item)

        complete_len = len(complete)

        if nix_path_complete and complete_len:
            self.nix_common_chars(current, complete, case_insensitive)
            complete_len = len(complete)

        # If only one entry matches, auto-complete it
        if (nix_path_complete and complete_len == 1) or (not nix_path_complete and complete_len):
            if nix_path_complete:
                cls.last = 0
            else:
                last = cls.last
                if back:
                    cls.last = complete_len - 1 if last is None or last < 1 else last - 1
                else:
                    cls.last = 0 if last is None or last >= complete_len - 1 else last + 1
                cls.in_progress = True
            FuzzyEditGlobal.bfr = complete[cls.last]
            FuzzyEditGlobal.region = sublime.Region(0, view.size())
            view.run_command("fuzzy_apply_edits")
            FuzzyEditGlobal.clear()
            sels = view.sel()
            sels.clear()
            sels.add(sublime.Region(view.size()))
        else:
            cls.last = None
            cls.text = None

    def nix_common_chars(self, current_complete, l, case_insensitive):
        """Resolve entries using their common start."""

        common = current_complete
        while True:
            match = True
            cmn_len = len(current_complete)
            if len(l[0]) > cmn_len:
                common += l[0][cmn_len].lower() if case_insensitive else l[0][cmn_len]
                cmn_len += 1
            else:
                break
            for item in l:
                value = item.lower() if case_insensitive else item
                if not value.startswith(common):
                    match = False
                    break
            if not match:
                break
            else:
                current_complete = common
        selection = l[0][0:len(current_complete)]
        del l[:]
        l.append(selection)

    @classmethod
    def update_autocomplete(cls, text):
        """Update autocomplete."""

        if text != cls.text and cls.last is not None:
            if not cls.in_progress:
                cls.text = None
                cls.last = None
            else:
                cls.in_progress = False

    @classmethod
    def reset_autocomplete(cls):
        """Reset autocomplete variables."""
        cls.last = None
        cls.in_progress = False
        cls.text = None
        cls.hl_index = -1
        cls.hl_last = -1


class FuzzyFileNavCommand(sublime_plugin.WindowCommand):
    """Navigate through folders."""

    active = False
    win_id = None
    view = None
    fuzzy_reload = False
    hide_hidden = False
    cwd = ""
    status = False

    @classmethod
    def reset(cls):
        """Reset variables."""

        cls.active = False
        cls.win_id = None
        cls.view = None
        cls.status = False
        cls.hide_hidden = not bool(sublime.load_settings(FUZZY_SETTINGS).get("show_system_hidden_files", False))
        # FuzzyClipboardCommand.clear_entries()

    @classmethod
    def set_hidden(cls, value):
        """Set hiding hidden file option."""

        cls.hide_hidden = value

    def run(self, start=None):
        """Run command."""

        if FuzzyFileNavCommand.active:
            self.window.run_command("hide_overlay")
        self.cls = FuzzyFileNavCommand
        previous = self.cls.cwd
        self.cls.active = True
        self.cls.win_id = self.window.id()
        self.regex_exclude = sublime.load_settings(FUZZY_SETTINGS).get("regex_exclude", [])
        FuzzyPathCompleteCommand.reset_autocomplete()

        debug_log("start - %s" % start if start is not None else "None")

        # Check if a start destination has been given
        # and ensure it is valid.
        directory = get_root_path() if start is None or not path.exists(start) or not path.isdir(start) else start
        self.cls.cwd = directory if PLATFORM == "windows" and directory == "" else path.normpath(directory)

        debug_log("cwd - %s" % self.cls.cwd)

        # Get and display options.
        try:
            self.display_files(self.cls.cwd)
        except Exception:
            if self.cls.fuzzy_reload:
                # Reloading, so fuzzy panel must be up, so preserve previous state
                self.cls.fuzzy_reload = False
                self.cls.cwd = previous
            else:
                # Not reloading, so go ahead and reset the state
                self.cls.reset()
            notify("%s is not accessible!" % self.cls.cwd)

    def get_files(self, cwd):
        """Get files, folders, or window's drives."""

        # Get files/drives (windows).
        files = get_drives() if PLATFORM == "windows" and cwd == "" else os.listdir(cwd)
        folders = []
        documents = []
        for f in files:
            valid = True
            full_path = path.join(cwd, f)

            # Check exclusion to omit files.
            if self.hide_hidden:
                if valid:
                    if not PLATFORM == "windows":
                        if f.startswith('.') and f != "..":
                            valid = False
                    else:
                        attrs = ctypes.windll.kernel32.GetFileAttributesW(full_path)
                        if attrs != -1 and bool(attrs & 2):
                            valid = False

                if valid:
                    for regex in self.regex_exclude:
                        if re.match(regex, f):
                            valid = False

            # Store file/folder info.
            if valid:
                if not path.isdir(full_path):
                    documents.append(f)
                else:
                    folders.append(f + ("\\" if PLATFORM == "windows" else "/"))
        return [".."] + sorted(folders) + sorted(documents)

    def on_highlight(self, value):
        """Get index of highlighted file."""

        FuzzyPathCompleteCommand.hl_index = value

    def display_files(self, cwd, index=-1):
        """Display files in folder."""

        # Get the folders children
        self.cls.status = True
        status_cwd()
        self.cls.files = self.get_files(cwd)

        # Make sure panel is down before loading a new one.
        self.cls.view = None
        sublime.set_timeout(
            lambda: self.window.show_quick_panel(
                self.cls.files, self.check_selection, 0, index, on_highlight=self.on_highlight
            ),
            0
        )

    def check_selection(self, selection):
        """Check the users selection and navigate to directory or open file."""

        debug_log("Process selection")
        if selection > -1:
            self.cls.fuzzy_reload = False
            # The first selection is the "go up a directory" option.
            directory = back_dir(self.cls.cwd) if selection == 0 else path.join(self.cls.cwd, self.cls.files[selection])
            self.cls.cwd = directory if PLATFORM == "windows" and directory == "" else path.normpath(directory)

            # Check if the option is a folder or if we are at the root (needed for windows)
            try:
                if (path.isdir(self.cls.cwd) or self.cls.cwd == get_root_path()):
                    # List directories content
                    self.display_files(self.cls.cwd)
                else:
                    multi = (
                        bool(sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_after_action", False)) and
                        "open" not in sublime.load_settings(FUZZY_SETTINGS).get("keep_panel_open_exceptions", [])
                    )

                    # Open file
                    new_view = self.window.open_file(self.cls.cwd)
                    if new_view is not None:

                        # Horrible ugly hack to ensure opened file gets focus
                        def fun(v, multi):
                            """Function to focus view."""

                            v.window().focus_view(v)
                            if not multi:
                                v.window().show_quick_panel(["None"], None)
                                v.window().run_command("hide_overlay")

                        sublime.set_timeout(lambda: fun(new_view, multi), 500)

                    # If multi-file open is set, leave panel open after opening file
                    if multi:
                        self.cls.cwd = path.normpath(back_dir(self.cls.cwd))
                        self.display_files(self.cls.cwd, selection)
                    else:
                        self.cls.reset()
            except Exception:
                # Inaccessible folder try backing up
                notify("%s is not accessible!" % self.cls.cwd)
                self.cls.cwd = back_dir(self.cls.cwd)
                self.display_files(self.cls.cwd)
        elif not self.cls.fuzzy_reload:
            # Reset if not reloading
            self.cls.reset()
        else:
            # Reset reload flag if reloading
            self.cls.fuzzy_reload = False


def init_hidden():
    """Init the "show hidden file" setting."""

    setting = sublime.load_settings(FUZZY_SETTINGS)
    show_hidden = not bool(setting.get("show_system_hidden_files", False))
    FuzzyFileNavCommand.set_hidden(show_hidden)
    setting.clear_on_change('reload')
    setting.add_on_change('reload', init_hidden)


def plugin_loaded():
    """Setup plugin."""

    global PLATFORM
    PLATFORM = sublime.platform()
    init_hidden()
