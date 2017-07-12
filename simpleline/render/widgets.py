# encoding: utf-8
#
# Widgets for Text UI framework.
#
# Copyright (C) 2016  Red Hat, Inc.
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


import functools
from math import ceil
from textwrap import wrap
from simpleline.utils.i18n import _
from simpleline.utils import ensure_str

__all__ = ["Widget", "TextWidget", "ColumnWidget", "CheckboxWidget",
           "CenterWidget"]


class Widget(object):

    def __init__(self, max_width=None, default=None):
        """Initializes base Widgets buffer.

        :param max_width: serves as a hint about screen size to write method with default arguments
        :type max_width: int

        :param default: string containing the default content to fill the buffer with
        :type default: string
        """
        self._buffer = []
        if default:
            self._buffer = [[c for c in l] for l in default.split("\n")]
        self._max_width = max_width
        self._cursor = (0, 0)  # row, col

    @property
    def height(self):
        """The current height of the internal buffer."""
        return len(self._buffer)

    @property
    def width(self):
        """The current width of the internal buffer (id of the first empty column)."""
        return functools.reduce(lambda acc, l: max(acc, len(l)), self._buffer, 0)

    def clear(self):
        """Clears this widgets buffer and resets cursor."""
        self._buffer = list()
        self._cursor = (0, 0)

    @property
    def content(self):
        """Return a list (rows) of lists (columns) with one character elements."""
        return self._buffer

    def render(self, width):
        """Redraw the widget's self._buffer.

        :param width: the width of buffer requested by the caller
        :type width: int

        Commonly, call render of child widgets and then draw and write
        methods to copy their contents to self._buffer.
        """
        self.clear()

    def get_lines(self):
        """Return lines to write out in order to show this widget.

        :return: lines representing this widget
        :rtype: list(str)
        """
        return [str(u"".join(line)) for line in self._buffer]

    def set_cursor_position(self, row, col):
        """Set cursor position.

        :param row: row id, starts with 0 at the top of the screen
        :type row: int

        :param col: column id, starts with 0 on the left side of the screen
        :type col: int
        """
        self._cursor = (row, col)

    @property
    def cursor(self):
        return self._cursor

    def setend(self):
        """Set the cursor to first column in new line at the end."""
        self._cursor = (self.height, 0)

    def draw(self, w, row=None, col=None, block=False):
        """Copy w widget's content to this widget's buffer at row, col position.

        :param w: widget to take content from
        :type w: class Widget

        :param row: row number to start at (default is at the cursor position)
        :type row: int

        :param col: column number to start at (default is at the cursor position)
        :type col: int

        :param block: when printing newline, start at column col (True) or at column 0 (False)
        :type block: boolean
        """
        # if the starting row is not present, start at the cursor position
        if row is None:
            row = self._cursor[0]

        # if the starting column is not present, start at the cursor position
        if col is None:
            col = self._cursor[1]

        # fill up rows to accommodate for w.height
        if self.height < row + w.height:
            for _i in range(row + w.height - self.height):
                self._buffer.append(list())

        # append columns to accommodate for w.width
        for l in range(row, row + w.height):
            l_len = len(self._buffer[l])
            w_len = len(w.content[l - row])
            if l_len < col + w_len:
                self._buffer[l] += ((col + w_len - l_len) * list(u" "))
            self._buffer[l][col:col + w_len] = w.content[l - row][:]

        # move the cursor to new spot
        if block:
            self._cursor = (row + w.height, col)
        else:
            self._cursor = (row + w.height, 0)

    def write(self, text, row=None, col=None, width=None, block=False, wordwrap=False):
        """Emulate the typing machine writing to this widget's buffer.

        :param text: text to type
        :type text: str

        :param row: row number to start at (default is at the cursor position)
        :type row: int

        :param col: column number to start at (default is at the cursor position)
        :type col: int

        :param width: wrap at "col" + "width" column (default is at self._max_width)
        :type width: int

        :param block: when printing newline, start at column col (True) or at column 0 (False)
        :type block: boolean

        :param wordwrap: wrap by words
        :type wordwrap: boolean
        """
        if not text:
            return

        text = ensure_str(text)
        if row is None:
            row = self._cursor[0]

        if col is None:
            col = self._cursor[1]

        if width is None and self._max_width:
            width = self._max_width - col

        x = row
        y = col

        if wordwrap:
            text = self._wrap_words(text, width)

        # emulate typing machine
        for character in text:
            # process newline
            if character == "\n":
                x += 1
                if block:
                    y = col
                else:
                    y = 0
                continue

            # if the line is not in buffer, create it
            if x >= len(self._buffer):
                for _i in range(x - len(self._buffer) + 1):
                    self._buffer.append(list())

            # if the line's length is not enough, fill it with spaces
            if y >= len(self._buffer[x]):
                self._buffer[x] += ((y - len(self._buffer[x]) + 1) * list(u" "))

            # "type" character
            self._buffer[x][y] = character

            # shift to the next char
            y += 1
            if width is not None and y >= col + width:
                x += 1
                if block:
                    y = col
                else:
                    y = 0

        self._cursor = (x, y)

    def _wrap_words(self, text, width):
        lines = []
        # Wrap each line separately
        for line in text.split('\n'):
            sublines = []
            for subline in wrap(line, width):
                sublines.append(subline)
                if len(subline) < width:
                    # line shorter than width will be wrapped by '\n' we add
                    sublines.append('\n')
                # line with length == width will be wrapped by the width based
                # wrapping logic
            # end of line will be wrapped by '\n' following the line in
            # original text
            if sublines and sublines[-1] == '\n':
                sublines.pop()
            lines.append("".join(sublines))
        return '\n'.join(lines)


class TextWidget(Widget):
    """Class to handle wrapped text output."""

    def __init__(self, text):
        """
        :param text: text to format
        :type text: str
        """
        super().__init__()
        self._text = text

    def render(self, width):
        """Renders the text widget limited to width number of columns (wraps to the next line when the text is longer).

        :param width: maximum width allocated to the string
        :type width: int

        :raises
        """
        super().render(width)
        self.write(self._text, width=width, wordwrap=True)


class CenterWidget(Widget):
    """Class to handle horizontal centering of content."""

    def __init__(self, w):
        """
        :param w: widget to center
        :type w: Widget
        """
        super().__init__()
        self._w = w

    def render(self, width):
        """Render the centered widget to internal buffer.

        :param width: maximum width the widget should use
        :type width: int
        """
        super().render(width)
        self._w.render(width)
        # make sure col is an integer
        self.draw(self._w, col=(width - self._w.width) // 2)


class CheckboxWidget(Widget):
    """Widget to show checkbox with (un)checked box, name and description."""

    def __init__(self, key="x", title=None, text=None, completed=None):
        """
        :param key: tick character to be used inside [ ]
        :type key: character

        :param title: the title next to the [ ] box
        :type title: str

        :param text: the description text to be shown on the second row in ()
        :type text: str

        :param completed: is the checkbox ticked or not?
        :type completed: True|False
        """
        super().__init__()
        self._key = key
        self._title = title
        self._text = text
        self._completed = completed

    def render(self, width):
        """Render the widget to internal buffer.

        It should be max width characters wide.
        """
        super().render(width)

        if self.completed:
            checkchar = self._key
        else:
            checkchar = " "

        # prepare the checkbox
        checkbox = TextWidget("[%s]" % checkchar)

        data = []

        # append lines
        if self.title:
            data.append(TextWidget(_(self.title)))

        if self.text:
            data.append(TextWidget("(%s)" % self.text))

        # the checkbox has two columns
        # [x] is one and is 3 chars wide
        # text is second and can occupy width - 3 - 1 (for space) chars
        cols = ColumnWidget([(3, [checkbox]), (width - 4, data)], 1)
        cols.render(width)

        # transfer the column widget rendered stuff to internal buffer
        self.draw(cols)

    @property
    def title(self):
        """Returns the first line (main title) of the checkbox."""
        return self._title

    @property
    def completed(self):
        """Returns the state of the checkbox, checked is True."""
        return self._completed

    @property
    def text(self):
        """Contains the description text from the second line."""
        return self._text


class ColumnWidget(Widget):

    def __init__(self, columns, spacing=0):
        """Create text columns

        :param columns: list containing (column width, [list of widgets to put into this column])
        :type columns: [(int, [...]), ...]

        :param spacing: number of spaces to use between columns
        :type spacing: int
        """
        super().__init__()
        self._spacing = spacing
        self._columns = columns

    def render(self, width):
        """Render the widget to it's internal buffer

        :param width: the maximum width the widget can use
        :type width: int

        :return: nothing
        """
        super().render(width)

        # the leftmost empty column
        col_pos = 0

        # iterate over tuples (column width, column content)
        for col_width, col in self._columns:

            # set cursor to first line and leftmost empty column
            self.set_cursor_position(0, col_pos)

            # if requested width is None, limit the maximum to width
            # and set minimum to 0
            if col_width is None:
                col_max_width = width - self.cursor[1]
                col_width = 0
            else:
                col_max_width = col_width

            # render and draw contents of column
            for item in col:
                item.render(col_max_width)
                self.draw(item, block=True)

            # recompute the leftmost empty column
            col_pos = max((col_pos + col_width), self.width) + self._spacing


class ListRowWidget(Widget):
    """Place widgets in rows. Place widgets for the best spread out."""

    def __init__(self, widgets, columns, columns_width=25, spacing=3):
        """Create ListWidget with specific number of columns.

        :param widgets: Widgets you want to position.
        :type widgets: Array of `Widget` based class.

        :param columns: How many columns we want.
        :type columns: int, bigger than 0

        :param columns_width: Width of every column.
        :type columns_width: int

        :param spacing: Set the spacing between columns.
        :type spacing: int
        """
        super().__init__()
        self._columns = columns
        self._widgets = widgets
        self._columns_width = columns_width
        self._spacing = spacing

    def prepare_list(self):
        """Prepare list for items ordering to rows and columns.

        List will be prepared as ([column 1], [column 2], ...)
        """
        return list(map(lambda x: [], range(0, self._columns)))

    def render(self, width):
        """Render widgets to it's internal buffer.

        :param width: the maximum width the widget can use
        :type width: int

        :return: nothing
        """
        super().render(width)

        ordered_items = self._order_items()
        lines_per_rows = self.render_and_calculate_lines_per_rows(ordered_items)

        # the leftmost empty column
        col_pos = 0

        for col in ordered_items:
            row_pos = 0

            # render and draw contents of column
            for row_id, item in enumerate(col):
                # set cursor to first line and leftmost empty column
                self.set_cursor_position(row_pos, col_pos)

                self.draw(item, block=True)
                row_pos = row_pos + lines_per_rows[row_id]

            # recompute the leftmost empty column
            col_pos = max((col_pos + self._columns_width), self.width) + self._spacing

    def render_and_calculate_lines_per_rows(self, ordered_items):
        self._render_all_items()
        return self._lines_per_every_row(ordered_items)

    def _render_all_items(self):
        for item in self._widgets:
            item.render(self._columns_width)

    def _lines_per_every_row(self, items):
        # call `self._render_and_calculate_lines_per_rows()` method instead
        lines_per_row = []

        # go through all items and find how many lines we need for each row printed (because of wrapping)
        for column_items in items:
            for row_id, item in enumerate(column_items):
                if len(lines_per_row) <= row_id:
                    lines_per_row.append(0)

                lines_per_row[row_id] = max(lines_per_row[row_id], len(item.get_lines()))

        return lines_per_row

    def _order_items(self):
        # create list of columns (lists)
        positioned_items = self.prepare_list()

        for item_id, item in enumerate(self._widgets):
            positioned_items[item_id % self._columns].append(item)

        return positioned_items


class ListColumnWidget(ListRowWidget):

    def _order_items(self):
        positioned_items = self.prepare_list()
        items_in_column = ceil(len(self._widgets) / self._columns)

        for item_id, item in enumerate(self._widgets):
            col_position = int(item_id // items_in_column)
            positioned_items[col_position].append(item)

        return positioned_items
