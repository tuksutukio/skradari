#!/usr/bin/env bash

### 
### Copyright (c) 2022, Antti Tukio
### All rights reserved.
### 
### This source code is licensed under the BSD-style license found in the
### LICENSE file in the root directory of this source tree.
### 

#
# planespot.sh
#
# (c) 2022 Antti Tukio (tuksutukio)
#
# This script performs a PlaneSpotters search for ModeS ID from clipboard
# on the default browser. 
#

BASEURL="https://www.planespotters.net/search?q="
SERVICENAME="www.planespotters.net"
MODESCODE=$(pbpaste)
URL="$BASEURL$MODESCODE"

if [ ${#MODESCODE} == 6 ]; then
	echo "Searching $SERVICENAME for '$MODESCODE'."
	open $URL
else
	echo "'$MODESCODE' is not a ModeS ID."
fi