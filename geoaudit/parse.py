#!/usr/bin/env python
"""Parse Ushahidi reports download (csv) and look for discrepancies.

%InsertOptionParserUsage%
"""

# TODO
# Look for locations that are close to each other but with different names
# Calculate consensus location
# List report ids of outliers
# Add support for getting data from the ushahidi web site via api or download form
# testing from ipython: import sys; sys.argv = ['parse.py', '-d', '/home/neal/info/ushahidi/libyacrisismap-reports-1301079295.csv']
# Use real spherical coordinates for distance calculations, etc.

import os
import sys
import optparse
from optparse import make_option
import logging
import csv
import math
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


usage = """Usage: parse.py [options] [file]....

Example:
 geoaudit/parse.py tests/ushahidi-report-test.csv"""

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

class Location(object):
    """
    A group of geographic points that have been identified as a single unique location.
    """
    
    def __init__(self):
        """
        Create an empty Location.
        """

        self.ids = []
        self.names = None
        self.lats = []
        self.lons = []

    def merge(self, report):
        """
        Merge in a new report
        """
        self.ids.append(report['#'])
        if self.names:
            if self.names != report['LOCATION']:
                raise ValueError()
        else:
            self.names = report['LOCATION']

        self.lats.append(float(report['LATITUDE']))
        self.lons.append(float(report['LONGITUDE']))

    def median(self):
        """
        Return the point specified by the median of latitudes and median of longitudes.
        Note this is different from the Geometric Median which is harder to calculate:
          http://en.wikipedia.org/wiki/Geometric_median
        """

        lats = sorted(self.lats)
        lons = sorted(self.lons)
        num = len(lats)
        # Median is the midpoint if odd, or average of 2 points if even
        if num % 2:
            return(lats[num/2], lons[num/2])
        else:
            return ( (lats[num/2 - 1] + lats[num/2]) / 2.0, (lons[num/2 - 1] + lons[num/2]) / 2.0)
        
    def outliers(self, max_distance = .02):
        """
        return points in this Location that are further than "max_distance" from the median of this location.
        """
        
        median = self.median()

        outs = []

        for n in range(len(self.lats)):
            point = (self.lats[n], self.lons[n])
            if distance(median, point) > max_distance:
                outs.append(point)

        return outs

    def __str__(self):
        return "L%s: (%f,%f)\t%s" % (self.ids[0], self.lats[0], self.lons[0], self.names[0])

def distance(pointa, pointb):
    """
    return the distance between pointa and pointb
    """
    return math.sqrt( (pointa[0]-pointb[0]) ** 2 + (pointa[1]-pointb[1]) ** 2)

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

    reports = parse(args, options)

    logging.debug("%s" % ([r for r in sorted(reports)]))

    locations = merge_by_name(reports)

    analyze(locations)

    return locations

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

def parse(args, options):
    "Parse the specified files.  If a directory is specified, parse all files in the directory."

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
            reports.update(parse_csv(file, options))
        else:
            logging.warning("Ignoring %s - unknown extension" % file)
            continue

    logging.info("%s Exit" % (datetime.now().strftime("%H:%M:%S")))
    return reports

def merge_by_name(reports):
    "Return list of Locations based on reports that have the same name"

    locations = {}
    for r in reports.values():
        name = r['LOCATION']
        locations.setdefault(name, Location()).merge(r)
        logging.debug("location: %s" % locations[name])

    logging.debug("Merge each unique location")

    for location in locations.values():
        logging.debug("location: %s" % location)

        location.num = len(location.lats)
        location.minlat = reduce(lambda x,y: min(x, y), location.lats)
        location.minlon = reduce(lambda x,y: min(x, y), location.lons)
        location.maxlat = reduce(lambda x,y: max(x, y), location.lats)
        location.maxlon = reduce(lambda x,y: max(x, y), location.lons)
        location.extent = math.sqrt( (location.maxlat-location.minlat) ** 2 + (location.maxlon-location.minlon) ** 2)

    return locations

def analyze(locations):
    """
    TODO: Look for outliers in the dictionary of Locations
    """
    
    for location in locations.values():
        if location.extent > 0.0:
            printf("%(extent)5f %(num)d\t(%(minlat)f, %(minlon)f)\t(%(maxlat)f, %(maxlon)f)\t%(names)s\n" % location.__dict__)

"""
FIXME: how to add timestamp to front of every logging line?  subclass logging??
vs adding stuff to format line and to vars dictionary....

def debug(format, vars):
    logging
"""

def printf(string):
    sys.stdout.write(string)

if __name__ == "__main__":
    main(parser)
