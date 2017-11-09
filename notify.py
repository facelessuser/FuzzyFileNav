"""
Fuzzy File Navigation.

Licensed under MIT
Copyright (c) 2012 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except Exception:
    class Notify(object):
        """Fallback SubNotify object."""

        @classmethod
        def is_ready(cls):
            """Return false to disable SubNotify."""

            return False


def notify(msg):
    """Notify message."""

    settings = sublime.load_settings("fuzzy_file_nav.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "FuzzyFileNav", "msg": msg})
    else:
        sublime.status_message(msg)


def error(msg):
    """Error message."""

    settings = sublime.load_settings("fuzzy_file_nav.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "FuzzyFileNav", "msg": msg, "level": "error"})
    else:
        sublime.error_message("FuzzyFileNav:\n%s" % msg)
