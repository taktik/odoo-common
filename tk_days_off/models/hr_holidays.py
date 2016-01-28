# -*- coding: utf-8 -*-

from openerp import api, fields, models, exceptions, _
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'
    _order = 'id desc'

    @api.multi
    @api.depends('number_of_days_temp')
    def _compute_number_of_days(self):
        for holiday in self:
            if holiday.type == 'remove':
                holiday.number_of_days = -holiday.number_of_days_temp
            else:
                holiday.number_of_days = holiday.number_of_days_temp
        return

    def _get_number_of_days(self, date_from, date_to):
        """
        Compute a float equals to the timedelta
        between two dates given as string, without including the days off
        :param date_from:
        :param date_to:
        :return: float
        """
        holiday_year_obj = self.env['training.holiday.year']
        if not holiday_year_obj.search([('year', '=', time.strftime('%Y'))]):
            return False
        date_time_format = "%Y-%m-%d %H:%M:%S"
        from_dt = datetime.strptime(date_from, date_time_format)
        to_dt = datetime.strptime(date_to, date_time_format)
        from_date = from_dt
        # compute the number of days off ( i )
        i = 0
        while from_dt < to_dt:
            day_off = self.env['training.holiday.period'].search([
                ('date_start', '<=', from_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                ('date_stop', '>=', from_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
            ])
            if day_off:
                i += 1
            from_dt = from_dt + relativedelta(days=1)
        # subtract the days off of the total days
        time_delta = to_dt - from_date
        diff_day = time_delta.days + float(time_delta.seconds) / 86400
        diff_day -= i
        diff_day = math.ceil(diff_day)
        return diff_day

    @api.onchange('date_from', 'date_to')
    def onchange_date(self):
        if self.date_from and self.date_to:
            diff_day = self._get_number_of_days(self.date_from, self.date_to)
            if not diff_day:
                raise exceptions.Warning(_('Configuration Error !'),
                                         _('Please, Can you configure the Days off ?'))
            self.number_of_days_temp = diff_day
            return
        self.number_of_days_temp = 0
        return

    date_from = fields.Datetime(
        string='Start Date',
    )
    date_to = fields.Datetime(
        string='End Date',
    )
    number_of_days_temp = fields.Float(
        string='Allocation',

    )
    number_of_days = fields.Float(
        compute=_compute_number_of_days,
        string='Number of Days',
    )
