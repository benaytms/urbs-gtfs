# URBS-GTFS

Curitiba has no official GTFS feed, which means the amount of people who can
freely access it is much slimmer than it should. What this feed aims to
achieve is to increase the amount of people that can access, use, and develop using
Curitiba's public transit system information.

For context, the General Transit Feed Specification (GTFS) is the open
source standard used by trip applications such as OpenStreetMaps, OsmAnd, Google Maps
or any open source developer to provide public transit directions. 
Despite the fact that Curitiba has one of the best public transit systems in Brazil, 
there was no GTFS feed. Which means that if any of those applications were to include Curitiba, 
they would have to parse through the data themselves in order to implement the schedules.

This project fills that gap by automatically transforming raw open data published by
C3SL/UFPR into a valid GTFS feed available to anyone.

