# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import functools
from typing import Any, Callable
from abc import abstractmethod

# ---- Third party imports
from appconfigs.user import NoDefault
from PyQt5.QtWidgets import QWidget, QFrame

# ---- Local imports
from gwhat.config.main import CONF


def wlcalcmethod(func):
    """
    A wrapper that bypass a tool func execution if the tool is not registered
    to hydrocalc.

    This is required in order to test tools or use tools programmatically
    without having to register them to hydrocalc.
    """
    @functools.wraps(func)
    def wrapper(tool, *args, **kwargs):
        if not tool.is_registered():
            return
        else:
            return func(tool, *args, **kwargs)
    return wrapper


class WLCalcToolBase(QFrame):
    """
    Basic functionality for WLCalc tools.

    WARNING: Don't override any methods or attributes present here unless you
    know what you are doing.
    """

    def name(self):
        """Return the name of the tool."""
        return self.__toolname__

    def title(self):
        """Return the title of the tool."""
        return self.__tooltitle__

    def tooltip(self):
        """Return the tooltip of the tool."""
        return self.__tooltip__

    def get_option(self, option, default=NoDefault):
        """
        Get an option from the user configuration file.

        Parameters
        ----------
        option: str
            Name of the option to get its value from.

        Returns
        -------
        bool, int, str, tuple, list, dict
            Value associated with `option`.
        """
        return CONF.get(self.__toolname__, option, default)

    def set_option(self, option, value):
        """
        Set an option in the configuration file.

        Parameters
        ----------
        option: str
            Name of the option (e.g. 'case_sensitive')
        value: bool, int, str, tuple, list, dict
            Value to save in configuration file, passed as a Python
            object.

        Notes
        -----
        * __toolname__ needs to be defined for this to work.
        """
        CONF.set(self.__toolname__, option, value)


class WLCalcTool(WLCalcToolBase):
    """
    WLCalc tool class.

    All tool *must* inherit this class and reimplement its interface.
    """
    # The name of the tool that will be used to refer to it in the code
    # and in the user configurations. This name must be unique and will
    # only be loaded once.
    __toolname__: str = None

    # The label that will be used to reference this tool in the GUI.
    __tooltitle__: str = None

    # The text that will be use as a tooltip for this tool in the GUI.
    __tooltip__: str = None

    @abstractmethod
    def register_tool(self, wlcalc: QWidget):
        pass

    @abstractmethod
    def is_registered(self):
        """Return whether this tool is registered to a WLCalc instance."""
        pass

    @abstractmethod
    def close_tool(self):
        pass

    @abstractmethod
    def set_wldset(self, wldset):
        """Set the namespace for the wldset in the widget."""
        pass

    @abstractmethod
    def set_wxdset(self, wldset):
        """Set the namespace for the wldset in the widget."""
        pass
