#!/bin/bash


export PATH="/bin:/usr/bin"
export CLASSPATH=$(ls -1 lib/* | grep jar$ | awk '{printf "%s:", $1}')
export CLASSPATH="$CLASSPATH":$scriptdir

FILES=$(find com -iname "*.java")

javac $FILES || exit

rm -f lib/jasper-server.jar
rm -f jasper-server.jar
jar cvf jasper-server.jar com
mv jasper-server.jar lib