# -*- coding: utf-8 -*-

from openerp import api, fields, models, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import time
from datetime import datetime


class HolidayYear(models.Model):
    _description = 'Training Holiday Year'
    _name = 'training.holiday.year'
    _rec_name = 'year'

    year = fields.Char(
        string='Year',
        size=64,
        required=True,
        default=datetime.today().year
    )
    period_ids = fields.One2many(
        'training.holiday.period',
        'year_id',
        string='Holiday Periods'
    )
    _sql_constraints = [
        ('uniq_year', 'unique(year)', 'The year must be unique !'),
    ]


class HolidayPeriodCategory(models.Model):
    _description = 'Training Holidays Category'
    _name = 'training.holidays.category'

    name = fields.Char(
        string='Name',
        size=128,
        required=True
    )


class HolidayPeriod(models.Model):
    _description = 'Training Holiday Period'
    _name = 'training.holiday.period'

    @api.multi
    def _check_date_start_stop(self):
        if not self.ids:
            return False
        for period in self:
            return period.date_start <= period.date_stop

    year_id = fields.Many2one(
        'training.holiday.year',
        string='Year',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(
        string='Name',
        size=64,
        required=True
    )
    date_start = fields.Date(
        string='Date Start',
        required=True,
        default=time.strftime(DEFAULT_SERVER_DATE_FORMAT)
    )
    date_stop = fields.Date(
        string='Date Stop',
        required=True,
        default=time.strftime(DEFAULT_SERVER_DATE_FORMAT)
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    category_id = fields.Many2one(
        'training.holidays.category',
        string='Category'
    )

    _constraints = [
        (_check_date_start_stop, "Please, check the start date !", ['date_start', 'date_stop']),
    ]
