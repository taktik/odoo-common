from openerp.osv import orm, fields

import logging

_logger = logging.getLogger(__name__)


class tk_cron(orm.Model):
    _inherit = 'ir.cron'

    def action_run(self, cr, uid, ids, context=None):
        _logger.debug("Manually running cron %s" % ids)
        if not isinstance(ids, list):
            ids = [ids]
        for cron in self.browse(cr, uid, ids):
            self.pool.get('ir.cron')._callback(cr, cron['user_id'].id, cron['model'], cron['function'], cron['args'], cron['id'])
        return True


tk_cron()
