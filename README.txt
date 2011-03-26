Parse Ushahidi reports download (csv) and look for discrepancies.

Right now it just takes a download of the full list of reports,
andlooks for outliers among reports that share exactly the same
location name.

Here are some quick hints on the calculations and the currently 
cryptic output format. 
 
I group each set of locations that share the same name into a 
"LocationCluster".  For each one, I calculate a "median" location, 
which is just the median of latitudes and median of the longitudes. 
The lat and lon may come from different reports, and is averaged when 
there is an even number of points, so it is quite possibly not an 
actual point from a report, but should be in the middle in some 
relatively robust sense. 
 
For each LocationCluster I find the bounding box of the set of points, 
and calculate the length of the diagonal of the bounding box (the "extent"). 
If the extent is more than 0.2 degrees, I print something out. 
 
7.46928 7  ll   (32.0640 12.7365)  ur   (32.7850 20.1709)       Zawiya, Libya 
        median  (32.7630 12.7365) 
                (32.0640 20.1709)       http://cal.libyacrisismap.net/admin/reports/edit/397 
                (32.7850 12.7441)       http://cal.libyacrisismap.net/admin/reports/edit/21 
 
The first line has the extent, the number of points, the lower left ("ll" and  
upper right ("ur") points of the bounding box, and the name. 
Then comes the median, and then one outlier per line, with a link to 
the report. 

