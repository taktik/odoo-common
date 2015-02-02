## How to connect with the libtdsodbc.so driver

conn = pyodbc.connect("DRIVER=/opt/local/lib/libtdsodbc.so;DBCNAME=localhost;UID=dvd;PWD=test")

SERVER=

pyodbc.connect("DRIVER=/opt/local/lib/libtdsodbc.so;SERVER=192.168.63.154;UID=taktik;PWD=oscar;PORT=1056;TDS_VERSION=7.0"