# Licensed under a 3-clause BSD style license - see LICENSE.rst
""" sextractor.py:
  Classes to read SExtractor table format

Built on daophot.py:
:Copyright: Smithsonian Astrophysical Observatory (2011)
:Author: Tom Aldcroft (aldcroft@head.cfa.harvard.edu)
"""

from __future__ import absolute_import, division, print_function

import re

from ...extern import six
from . import core


class SExtractor(core.BaseReader):
    """Read a SExtractor file.
       SExtractor is a package for faint-galaxy photometry.
       Bertin & Arnouts 1996, A&A Supp. 317, 393.
       http://www.astromatic.net/software/sextractor

    Example::

      # 1 NUMBER
      # 2 ALPHA_J2000
      # 3 DELTA_J2000
      # 4 FLUX_RADIUS
      # 7 MAG_AUTO
      1 32.23222 10.1211 0.8 1.2 1.4 18.1
      2 38.12321 -88.1321 2.2 2.4 3.1 17.0

    Note the skipped numbers since flux_radius has 3 columns.  The three FLUX_RADIUS
    columns will be named FLUX_RADIUS, FLUX_RADIUS_1, FLUX_RADIUS_2
    """
    _format_name = 'sextractor'
    _io_registry_can_write = False
    _description = 'SExtractor format table'

    def __init__(self):
        core.BaseReader.__init__(self)
        self.header = SExtractorHeader()
        self.inputter = core.ContinuationLinesInputter()
        self.data.splitter.delimiter = ' '
        self.data.start_line = 0
        self.data.comment = r'\s*#'  # Comments embedded in the data start with #

    def read(self, table):
        output = core.BaseReader.read(self, table)
        self.table = output
        self.cols = self.header.cols

        return self.table

    def write(self, table=None):
        raise NotImplementedError


class SExtractorHeader(core.BaseHeader):
    """Read the header from a file produced by SExtractor."""
    def __init__(self):
        core.BaseHeader.__init__(self)
        self.comment = r'^\s*#\s*\S\D.*'  # Find lines that dont have "# digit"

    def get_cols(self, lines):
        """Initialize the header Column objects from the table ``lines`` for a SExtractor
        header.  The SExtractor header is specialized so that we just copy the entire BaseHeader
        get_cols routine and modify as needed.

        :param lines: list of table lines
        :returns: list of table Columns
        """

        # This assumes that the columns are listed in order, one per line with a
        # header comment string of the format: "# 1 ID"
        # However, some may be missing and must be inferred from skipped column numbers
        columns = {}
        re_name_def = re.compile(r'^\s*#\s*([0-9]+).*')  # E.g. '# 1 ID'
        for line in lines:
            if not line.startswith('#'):
                break                   # End of header lines
            else:
                match = re_name_def.search(line)
                if match:
                    words = match.group(0).strip().strip('#').split()
                    colnumber = int(words[0])  # First string is the column number
                    colname = words[1]   # second string is the column name
                    columns[colnumber] = colname
        # Handle skipped column numbers
        colnumbers = sorted(columns)
        previous_column = 0
        for n in colnumbers:
            if n != previous_column + 1:
                for c in range(previous_column+1, n):
                    column_name = columns[previous_column]+"_%d" % (c-previous_column)
                    columns[c] = column_name
            previous_column = n

        # Add the columns in order to self.names
        colnumbers = sorted(columns)
        self.names = []
        for n in colnumbers:
            self.names.append(columns[n])

        if not self.names:
            raise core.InconsistentTableError('No column names found in SExtractor header')

        self._set_cols_from_names()
