"""
https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

The XDG Base Directory Specification
"""
import os

XDG_DATA_HOME = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
"""
The base directory relative to which user specific data files should be
written. Defaults to $HOME/.local/share.
"""

XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
"""
The base directory relative to which user specific configuration files
should be written. Defaults to $HOME/.config.
"""

XDG_STATE_HOME = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
"""
The base directory relative to which user specific state files should
be written. Defaults to $HOME/.local/state.
"""

XDG_RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR", os.path.expanduser("~/.local/run"))
"""
The base directory relative to which user-specific non-essential data
files and other (file objects) should be stored. Defaults to
$HOME/.local/run.
"""

XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
"""
The base directory relative to which user specific non-essential data
files should be stored. Defaults to $HOME/.cache.
"""
