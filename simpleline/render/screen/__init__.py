# Base class for text window screens.
#
# Copyright (C) 2017  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Author(s): Jiri Konecny <jkonecny@redhat.com>
#

from simpleline.base import App
from simpleline.render.prompt import Prompt
from simpleline.render.screen.signal_handler import SignalHandler
from simpleline.render.widgets import Widget
from simpleline.utils.i18n import _


class UIScreen(SignalHandler):
    """Base class representing one TUI Screen.

    Shares some API with anaconda's GUI to make it easy for devs to create similar UI
    with the familiar API.
    """
    # title line of the screen
    title = u"Screen.."

    def __init__(self, screen_height=25):
        """ Constructor of the TUI screen.

        :param screen_height: height of the screen (useful for printing long widgets)
        :type screen_height: int (the value must be bigger than 4)
        """
        self._screen_height = screen_height
        self._ready = False

        # list that holds the content to be printed out
        self._window = []

        # should the input be required after draw
        self._input_required = True

        # index of the page (subset of screen) shown during show_all
        # indexing starts with 0
        self._page = 0

    @property
    def ready(self):
        """This screen is ready for use."""
        return self._ready

    @ready.setter
    def ready(self, ready):
        """Set ready status for this screen."""
        self._ready = ready

    @property
    def input_required(self):
        """Return if the screen requires input."""
        return self._input_required

    @input_required.setter
    def input_required(self, input_required):
        """Set if the screen should require input."""
        self._input_required = input_required

    @property
    def window(self):
        """Return list of widgets for rendering."""
        return self._window

    @window.setter
    def window(self, window):
        """Set list of widgets for rendering."""
        self._window = window

    def setup(self, args):
        """Do additional setup right before this screen is used.

        It is mandatory to call this ancestor method in the child class to set ready status.

        :param args: arguments for the setup
        :type args: array of values
        :return: whether this screen should be scheduled or not
        :rtype: bool
        """
        self._ready = True
        App.event_loop().register_signal_source(self)
        return True

    def refresh(self, args=None):
        """Method which prepares the content desired on the screen to `self.window`.

        :param args: optional argument passed from switch_screen calls
        :type args: anything
        """
        self.window = [_(self.title), u""]
        return

    def _print_widget(self, widget):
        """Prints a widget (could be longer than the screen height) with user interaction (when needed).

        :param widget: widget to print
        :type widget: Widget instance
        """
        # TODO: Work even for lower screen_height than 4
        pos = 0
        lines = widget.get_lines()
        num_lines = len(lines)

        if num_lines < self._screen_height - 2:
            # widget plus prompt are shorter than screen height, just print the widget
            print(u"\n".join(lines))
            return

        # long widget, print it in steps and prompt user to continue
        last_line = num_lines - 1
        while pos <= last_line:
            if pos + self._screen_height - 2 > last_line:
                # enough space to print the rest of the widget plus regular
                # prompt (2 lines)
                for line in lines[pos:]:
                    print(line)
                pos += self._screen_height - 1
            else:
                # print part with a prompt to continue
                for line in lines[pos:(pos + self._screen_height - 2)]:
                    print(line)
                custom_prompt = Prompt(_("\nPress %s to continue") % Prompt.ENTER)
                App.renderer().io_manager.get_user_input(custom_prompt)
                pos += self._screen_height - 1

    def show_all(self):
        """Prepares all elements of self.window for output and then prints them on the screen."""
        for w in self.window:
            if hasattr(w, "render"):
                w.render(App.renderer().width)  # pylint: disable=no-member
            if isinstance(w, Widget):
                self._print_widget(w)
            elif isinstance(w, bytes):
                print(w)
            else:
                # not a widget or string, just print its string representation
                print(str(w))

    def input(self, args, key):
        """Method called to process input. If the input is not handled here, return it.

        :param key: input string to process
        :type key: str
        :param args: optional argument passed from switch_screen calls
        :type args: anything
        :return: return INPUT_PROCESSED if key was handled,
                 INPUT_DISCARDED if the screen should not process input on the renderer and
                 key if you want it to.
        :rtype: `simpleline.render.INPUT_PROCESSED`|`simpleline.render.INPUT_DISCARDED`|str
        """
        return key

    def prompt(self, args=None):
        """Return the text to be shown as prompt or handle the prompt and return None.

        :param args: optional argument passed from switch_screen calls
        :type args: anything
        :return: returns an instance of Prompt with text to be shown next to the prompt
                 for input or None to skip further input processing
        :rtype: Prompt instance|None
        """
        prompt = Prompt()
        prompt.add_refresh_option()
        prompt.add_continue_option()
        prompt.add_quit_option()
        return prompt

    def closed(self):
        """Callback when this screen is closed."""
        pass
