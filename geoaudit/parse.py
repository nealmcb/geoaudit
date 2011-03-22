#!/usr/bin/env python
"""Parse Ushahidi reports download (csv) and look for discrepancies.

%InsertOptionParserUsage%
"""

import os
import sys
import optparse
from optparse import make_option
import logging
import csv
from datetime import datetime

"""
from root import settings
from django.core.management import setup_environ
setup_environ(settings)
from django.db import transaction
import electionaudits.models as models
"""

__author__ = "Neal McBurnett <http://neal.mcburnett.org/>"
__copyright__ = "Copyright (c) 2011 Neal McBurnett"
__license__ = "MIT"


usage = """Usage: manage.py parse [options] [file]....

Example:
 manage.py parse -s 001_EV_p001.xml 002_AB_p022.xml 003_ED_p015.xml"""

option_list = (
    make_option("-d", "--debug",
                  action="store_true", default=False,
                  help="turn on debugging output"),
)

parser = optparse.OptionParser(prog="parse", usage=usage, option_list=option_list)

# incorporate OptionParser usage documentation into our docstring
__doc__ = __doc__.replace("%InsertOptionParserUsage%\n", parser.format_help())

def set_options(args):
    """Return options for parser given specified arguments.
    E.g. options = set_options(["-c", "-s"])
    """

    (options, args) = parser.parse_args(args)
    return options

def main(parser):
    """Parse files and do audit"""

    (options, args) = parser.parse_args()

    if options.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel) # format='%(message)s'

    logging.debug("options = %s, args = %s" % (options, list(args)))

    if len(args) == 0:
        args.append(os.path.join(os.path.dirname(__file__), '../tests/ushahidi-report-test.csv'))
        logging.debug("using test file: " + args[0])

    parse(args, options)

def parse(args, options):
    "parse the files"

    files = []

    for arg in args:
        if os.path.isdir(arg):
            files += [os.path.join(arg, f) for f in os.listdir(arg)]
        else:
            files.append(arg)

    logging.debug("files = %s" % list(files))

    logging.info("%s Start processing files" % (datetime.now().strftime("%H:%M:%S")))

    reports = {}

    for file in files:
        logging.info("%s Processing %s" % (datetime.now().strftime("%H:%M:%S"), file))
        if file.endswith(".csv"):
            reports = parse_csv(file, options)
            print [r for r in sorted(reports)]
        else:
            logging.warning("Ignoring %s - unknown extension" % file)
            continue

    logging.info("%s Exit" % (datetime.now().strftime("%H:%M:%S")))

#@transaction.commit_on_success
def parse_csv(file, options):
    """Parse Ushahidi report export file
    a comma-separated .csv file.
    The first line has the column headers:
#,INCIDENT TITLE,INCIDENT DATE,LOCATION,DESCRIPTION,CATEGORY,LATITUDE,LONGITUDE,NEWS LINKS,APPROVED,VERIFIED
"1256","Misrata airport struck by international forces, according to doctor","2011-03-20 01:18:00","Misrata Airport, Misrata, Libya","In Misurata, a rebel-held city in western Libya, a doctor said international forces had struck the airport, where Kadafi's troops had massed, silencing artillery that had been hitting the city for the last four days.","Geo-Located, Air Strike, Media News, ","32.329923","15.062648","http://www.latimes.com/news/nationworld/world/la-fg-libya-fighting-20110320,0,1292435.story, ",YES,NO
    """

    reader = csv.DictReader(open(file), delimiter=",")

    reports = {}

    for r in reader:
        key = r['#']
        if reports.has_key(key):
            logging.error("%s Duplicate key %s on line %s - ignored" % (datetime.now().strftime("%H:%M:%S"), key, reader.reader.line_num))
            continue;
        reports[key] = r

    return reports

"""
FIXME: how to add timestamp to front of every logging line?  subclass logging??
vs adding stuff to format line and to vars dictionary....

def debug(format, vars):
    logging
"""

if __name__ == "__main__":
    main(parser)
