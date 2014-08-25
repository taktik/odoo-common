#!/bin/bash

myDir=`dirname $0`

export PATH="/bin:/usr/bin"
export CLASSPATH=$(ls -1 $myDir/lib/* | grep jar$ | awk '{printf "%s:", $1}')

java -Xmx1056m com.nantic.jasperreports.JasperServer