#!/usr/bin/env bash

### 
### Copyright (c) 2022, Antti Tukio
### All rights reserved.
### 
### This source code is licensed under the BSD-style license found in the
### LICENSE file in the root directory of this source tree.
### 

#
# fr24poll.sh
#
# (c) 2022 Antti Tukio (tuksutukio)
#
# This script polls a FlightRadar24 feeder and reports changes
# in aircraft visibility.
#
# An empty exclusion list is created if one is not found. Aircraft can be
# excluded from report by their ModeS ID.
#

# quit on error
set -e

# set flight data polling address
FEEDERURL="http://192.168.1.131:8754/flights.json"

# set poll interval in seconds
POLLINTERVAL=60

# make sure we have an exclusion list file
EXCLIST="fr24mute.txt"
if [ ! -f $EXCLIST ]; then
	echo "Creating exclusion list: $ECXLIST"
	echo "This is an fr24poll exclusion list. Add one 6-digit ModeS ID per row." > $EXCLIST
else
	echo "Found exclusion list: $EXCLIST"
fi

# print something informative
echo "Polling $FEEDERURL for flight data changes every $POLLINTERVAL seconds."
echo "Copy a ModeS code to clipboard and hit 'x' to make a PlaneSpotters search."



### The beef is here:

# loop until signaled
while true
do
	# initialize parsing and output
	DONE=0
	FLIGHTLIST=""

	# fetch flight data json from fr24 box and strip double quotes
	FLIGHTDATA=$(curl -s $FEEDERURL | tr -d \")
	FLIGHTDATA=$(echo $FLIGHTDATA | tr -d \")
	
	# alarms for hijacking, mayday and radio loss
	ALARM=0
	
	# 7600
	if [[ "$FLIGHTDATA" == *",7600,"* ]]; then
		echo "Radio loss squawk detected!"
		ALARM=1
		# three chimes
		SOUND="\007\007\007"
		SPEECH="radio loss"
	fi
	
	# 7700
	if [[ "$FLIGHTDATA" == *",7700,"* ]]; then
		echo "Mayday squawk detected!"
		ALARM=1
		# four chimes
		SOUND="\007\007\007\007"
		SPEECH="mayday [[slnc 500]] mayday [[slnc 500]] mayday"
	fi
	
	# 7800
	if [[ "$FLIGHTDATA" == *",7500,"* ]]; then
		echo "Hijack squawk detected!"
		ALARM=1
		# five chimes
		SOUND="\007\007\007\007\007"
		SPEECH="hijack [[slnc 1000]] hijack [[slnc 1000]] hijack [[slnc 1000]] hijack"
	fi
	
	# alarm sound
	if [ $ALARM -eq 1 ]; then
		echo -en $SOUND
		say -v Samantha $SPEECH
	fi
	
	WORKAREA=$FLIGHTDATA
	# loop until there's nothing more to parse
	while [ $DONE -eq 0 ]
		do
			# search for ':[', modeS ID comes right after that
			TMP=$WORKAREA
			WORKAREA=${TMP#*":["}
			# if truncated is the same as original, there's no more IDs
			if [ "$WORKAREA" == "$TMP" ]; then
				DONE=1
			else
				# extract the modeS ID (6 first chars) and append to output
				ID=${WORKAREA:0:6}
				# but only if it is not on exclusion list file
				if [[ $(grep -c $ID $EXCLIST) -eq 0 ]]; then
					FLIGHTLIST="$FLIGHTLIST, $ID"
				fi

			fi
		done

	# strip the initial space and comma
	FLIGHTLIST=${FLIGHTLIST:2}

	# no change in flights
	if [ "$PREVLIST" == "$FLIGHTLIST" ]; then
		echo -n "."
	# flights have changed
	else
		# print something nice
		echo " "
		echo $(date "+%d-%m-%Y %H:%M:%S")
		echo $FLIGHTLIST
		# chime once
		echo -en "\007"
	fi
	
	# store in order to determine change
	PREVLIST=$FLIGHTLIST
	
	# wait 60 seconds for a key press
	# run planespotter search for clipboard if 'x' pressed
	KEYIN=""
	read -t $POLLINTERVAL -n 1 KEYIN > /dev/null || (true)
	if [ $? == 0 ]; then
    	if [ "$KEYIN" == "x" ]; then
			echo
    		./planespot.sh
    	fi
	fi

done
