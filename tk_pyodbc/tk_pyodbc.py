from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp import netsvc
import openerp.pooler
from openerp import tools
import logging
# # Little hack to force decimal_point to be "." and not dependent of locale (see pyodbc pyodbcmodule.cpp)
import locale

locale._override_localeconv.update({'decimal_point': '.'})
## End hack
import pyodbc

locale._override_localeconv = {}

logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Base class for exceptions in this module."""
    pass


class tk_pyodbc(orm.Model):
    _name = "tk_pyodbc"
    _description = ""
    __database_types = [
        ('mssql', 'MS SQL'),
    ]

    def get_connection(self, cr, uid, ids, timeout=None, context=None):
        """
        Example: conn = pyodbc.connect("DRIVER=/opt/local/lib/libtdsodbc.so;SERVER=192.168.63.154;UID=taktik;PWD=oscar;PORT=1056;TDS_VERSION=7.0")
        """
        tk_pyodbc = self.browse(cr, uid, ids)[0]
        if not tk_pyodbc:
            raise orm.except_orm(_('Error !'), _('Bad tk_pyodbc'))
        try:
            logger.debug('Trying to get connection to SERVER %s, PORT %s, USER %s, PWD %s, DRIVER %s' % (tk_pyodbc.server, tk_pyodbc.port, tk_pyodbc.user, tk_pyodbc.pwd, tk_pyodbc.driver))
            logger.debug("DRIVER=%s;SERVER=%s;UID=%s;PWD=%s;PORT=%s;%s" % (tk_pyodbc.driver, tk_pyodbc.server, tk_pyodbc.user, tk_pyodbc.pwd, tk_pyodbc.port, tk_pyodbc.optional_params))
            conn = pyodbc.connect("DRIVER=%s;SERVER=%s;UID=%s;PWD=%s;PORT=%s;%s" % (tk_pyodbc.driver, tk_pyodbc.server, tk_pyodbc.user, tk_pyodbc.pwd, tk_pyodbc.port, tk_pyodbc.optional_params), timeout=timeout or 0)
            logger.debug("Connection acquired")
            return conn
        except Exception, e:
            raise orm.except_orm(_('Error !'), _('Could not get a valid connection. %s') % e)

    def check_download_connection(self, cr, uid, ids, context=None):
        """
        checks the connection to the sql server
        """
        conn = self.get_connection(cr, uid, ids, context)
        conn.close()
        raise orm.except_orm(_('Success'), _('Connection to Oscar was successful!'))

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'database_type': fields.selection(__database_types, 'Database Type'),
        'server': fields.char('Server address', size=256, required=False),
        'database': fields.char('Database name', size=256, required=False),
        'port': fields.integer('Database port'),
        'user': fields.char('Username', size=256, required=False),
        'pwd': fields.char('Password', size=256, required=False),
        'driver': fields.char('Driver location', size=256),
        'optional_params': fields.char('Optional parameters', size=256),
    }


tk_pyodbc()
