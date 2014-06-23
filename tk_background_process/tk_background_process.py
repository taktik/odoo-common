from openerp.osv import orm, fields
import threading
import openerp.pooler as pooler
import time, datetime
from openerp.tools.translate import _
import sys, traceback


class tk_background_process(orm.Model):
    _name = 'tk.background.process'
    _order = "start_date desc"

    def __init__(self, pool, cr):
        self.dbname = cr.dbname

        return super(tk_background_process, self).__init__(pool, cr)

    def _get_logs_for_process(self, cr, uid, ids, name, arg, context=None):
        res = {}
        log_obj = self.pool.get('tk_log.log')
        for process in ids:
            res[process] = log_obj.search(cr, uid, [('model', '=', "%s" % (self._name)), ('model_id', '=', process)])
        return res


    __state = [
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    _columns = {
        'name': fields.char('Name', size=128, readonly=False),
        'state': fields.selection(__state, 'State', readonly=True),
        'start_date': fields.datetime('Start Date', readonly=True),
        'end_date': fields.datetime('End Date', readonly=True),
        'user_id': fields.many2one('res.users', 'User', readonly=True),
        'lags_ids': fields.function(_get_logs_for_process, type="many2many", relation="tk_log.log", string="Logs")
    }


    def process(self, *args, **kwargs):
        self.db, self.pool = pooler.get_db_and_pool(self.dbname)
        cr = self.db.cursor(serialized=False)
        uid = kwargs['uid']

        self.log(cr, uid, kwargs['process_id'], "Process start", level="info", name="Process start")

        try:
            self.treat(cr, uid, args, kwargs)
            cr.commit()
        except Exception, e:
            cr.rollback()
            self.process_error(cr, uid, kwargs['process_id'], traceback.format_exc())
            raise e
        finally:

            cr.close()
        return

    def treat(self, cr, uid, args, kwargs):

        return


    def launch_process(self, cr, uid, name, args=[], kwargs={}, context=None):
        vals = {
            'start_date': datetime.datetime.now(),
            'end_date': False,
            'user_id': uid,
            'name': name,
            'state': 'in_progress',
        }
        id = self.create(cr, uid, vals, context)
        for thread in threading.enumerate():
            if thread.getName() == "%s_thread" % self._name:
                self.log(cr, uid, id, "There is already an job running. Please wait for it to terminate before trying to process again.", level="warn", name="Process starting...")
                raise orm.except_orm(_('Error!'), _('There is already an job running. Please wait for it to terminate before trying to process again.'))
                return
        kw_dict = {'uid': uid, 'process_id': id}
        kw_dict.update(kwargs)
        thread = threading.Thread(target=self.process, name="%s_thread" % self._name, args=[], kwargs=kw_dict)
        self.log(cr, uid, id, "Launching thread", level="info", name="Process starting...")
        thread.start()
        return True

    def stop_process(self, cr, uid, ids, context=None):
        """
        This method will stop the process
        """
        for thread in threading.enumerate():
            if thread.getName() == "%s_thread" % self._name:
                thread._Thread__stop()
        return True

    def get_progress(self, cr, uid, ids, context=None):
        """
        This method will return the progress in %
        """
        return True

    def process_error(self, cr, uid, id, exception):
        self.log(cr, uid, id, exception, level="error", name="Process End Error")
        self.write(cr, uid, [id], {'state': 'failed', 'end_date': datetime.datetime.now()})

    def process_done(self, cr, uid, id):
        self.log(cr, uid, id, "The process finish correctly", level="info", name="Process End")
        self.write(cr, uid, [id], {'state': 'done', 'end_date': datetime.datetime.now()})


tk_background_process()