# #############################################################################
#
# Copyright (c) 2008-2012 NaN Projectes de Programari Lliure, S.L.
# http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# #############################################################################
import os
import glob
import time
import socket
import subprocess
import xmlrpclib
import logging

from openerp.osv import osv
from openerp.tools.translate import _


class JasperServer:
    def __init__(self, port=8090):
        self.port = port
        self.pidfile = None
        url = 'http://localhost:%d' % port
        self.proxy = xmlrpclib.ServerProxy(url, allow_none=True)

    def path(self):
        return os.path.abspath(os.path.dirname(__file__))

    def setPidFile(self, pidfile):
        self.pidfile = pidfile

    def start(self):
        env = {}
        env.update(os.environ)
        libs = os.path.join(self.path(), '..', 'java', 'lib', '*.jar')
        env['CLASSPATH'] = os.path.join(self.path(), '..', 'java:') + ':'.join(glob.glob(libs)) + ':' + os.path.join(
            self.path(), '..', 'custom_reports')
        cwd = os.path.join(self.path(), '..', 'java')
        process = subprocess.Popen(['java', 'com.nantic.jasperreports.JasperServer', unicode(self.port)], env=env,
                                   cwd=cwd)
        if self.pidfile:
            f = open(self.pidfile, 'w')
            f.write(str(process.pid))
            f.close()

    def execute(self, *args):
        try:
            self.proxy.Report.execute(*args)
        except (xmlrpclib.ProtocolError, socket.error), e:
            print "FIRST TRY DIDN'T WORK: ", str(e), str(e.args)
            self.start()
            for x in xrange(40):
                time.sleep(1)
                try:
                    print "TRYING"
                    return self.proxy.Report.execute(*args)
                except (xmlrpclib.ProtocolError, socket.error), e:
                    print "EXCEPTION: ", str(e), str(e.args)
                    pass
