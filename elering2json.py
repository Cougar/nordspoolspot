#
#    Convert Elering metering data from CSV to JSON
#    Copyright (C) 2023 Cougar <cougar@random.ee>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

""" Read energy metering data CSV from Elering and generate JSON

For example usage, see at the end of the module.

Command line usage:

    $ cat Tarbimine_elekter.csv | python3 -m elering2json
    $ python3 -m elering2json < Tarbimine_elekter.csv
    $ python3 -m elering2json Tarbimine_elekter.csv
    $ cat Tarbimine_elekter.csv | python3 ./elering2json.py
    $ python3 ./elering2json.py < Tarbimine_elekter.csv
    $ python3 ./elering2json.py Tarbimine_elekter.csv

"""

import sys
import csv
import json
import os
import time
from datetime import datetime, timedelta
from pytz import timezone

import logging

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

__version__ = "0.2"
__all__ = ["EleringUsage", "convert_data"]

TIMEZONE = "Europe/Tallinn"


class EleringUsage(object):
    """Elering usage CSV parser"""

    def __init__(self, csv_file):
        self._usagedata = []
        self.csv_reader = csv.reader(csv_file, delimiter=";")

    def _parse_data(self):
        """Parse original Elering CSV to simple time/price list"""
        os.environ["TZ"] = TIMEZONE
        time.tzset()
        last_starttime = None
        line_count = 0
        for row_ in self.csv_reader:
            line_count += 1
            if line_count < 6:
                continue
            if not row_[1]:
                continue
            ts_ = parsetime(row_[0], row_[0] != last_starttime)
            last_starttime = row_[0]
            self._usagedata.append({
                "timestamp": ts_,
                "val": row_[1].replace(",", ".")
            })

    def get_data(self):
        """Get parsed Elering usage data

        :returns: parsed data
        """
        self._parse_data()
        return self._usagedata


def convert_data():
    """Convert Elering CSV format to simple JSON"""
    if len(sys.argv) == 1:
        infile = sys.stdin
    elif len(sys.argv) == 2:
        infile = open(sys.argv[1], "r")
    else:
        raise SystemExit(sys.argv[0] + " [infile]")
    with infile:
        data = EleringUsage(infile).get_data()
    with sys.stdout:
        json.dump(data, sys.stdout, sort_keys=True, indent=4)
        sys.stdout.write("\n")


def parsetime(timestr, is_dst=True):
    _st = time.strptime(timestr, "%d.%m.%Y %H:%M")
    _dt = datetime(
        _st.tm_year, _st.tm_mon, _st.tm_mday,
        _st.tm_hour, _st.tm_min, _st.tm_sec
    )
    return int(datetime.timestamp(timezone(TIMEZONE).localize(_dt, is_dst=is_dst)))


if __name__ == "__main__":
    convert_data()

# vi: set tabstop=2 expandtab textwidth=70 filetype=python:
