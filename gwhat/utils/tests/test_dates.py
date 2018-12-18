# -*- coding: utf-8 -*-

#
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports
import os

# ---- Third party imports
import pytest

# ---- Local imports
from gwhat.utils.dates import qdate_from_xldate


# ---- Tests
def test_qdate_from_xldate():
    """
    Assert that the function to convert a numerical Excel date to a QDate
    object is working as expected.
    """
    for xldate in [43000, 43000.87]:
        qdate = qdate_from_xldate(xldate)
        assert qdate.day() == 22
        assert qdate.month() == 9
        assert qdate.year() == 2017


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
