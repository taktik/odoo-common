# -*- coding: utf-8 -*-

from openerp import fields, models, api, exceptions, _
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from dateutil import easter


class ClbDaysOffWizard(models.TransientModel):
    _name = 'training.holiday.year.wizard'

    year = fields.Integer(
        string='Year',
        required=True,
    )

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_apply(self):
        """
        Creates training.holiday.year - training.holiday.period - training.holidays.category
        for all the week-ends and days of statutory leave
        for the year set in the wizard.
        :return:
        """
        if not self.id:
            return False
        holiday_year_obj = self.env['training.holiday.year']
        holiday_period_obj = self.env['training.holiday.period']
        category_week_end = self.env['training.holidays.category'].search([('name', '=', 'Week-end')])
        category_legal = self.env['training.holidays.category'].search([('name', '=', 'Legal')])
        if not category_week_end:
            category_we = self.env['training.holidays.category'].create({'name': _('Week-end')})
            category_week_end = [category_we]
        if not category_legal:
            category_leg = self.env['training.holidays.category'].create({'name': _('Legal')})
            category_legal = [category_leg]
        current_wizard = self[0]
        try:
            year_start = datetime.strptime('%04s-01-01' % current_wizard.year, DEFAULT_SERVER_DATE_FORMAT)
            year_end = datetime.strptime('%04s-12-31' % current_wizard.year, DEFAULT_SERVER_DATE_FORMAT)
        except:
            raise exceptions.Warning(_('Error!'), _('Please enter valid year'))

        year_id = holiday_year_obj.create({'year': current_wizard.year})

        # Generate days of statutory leave in Belgium
        easter_sunday = easter.easter(current_wizard.year)
        easter_monday = datetime.strftime(easter_sunday + timedelta(days=1), DEFAULT_SERVER_DATE_FORMAT)
        ascension = datetime.strftime(easter_sunday + timedelta(days=39), DEFAULT_SERVER_DATE_FORMAT)
        pentecost = datetime.strftime(easter_sunday + timedelta(days=50), DEFAULT_SERVER_DATE_FORMAT)
        legal_days_list = [['%04s-01-01' % current_wizard.year, _('New Year\'s Days')],
                           [easter_monday, _('Easter Monday')],
                           ['%04s-05-01' % current_wizard.year, _('Labour day')],
                           [ascension, _('Ascension')],
                           [pentecost, _('Pentecost Monday')],
                           ['%04s-07-21' % current_wizard.year, _('Belgian National day')],
                           ['%04s-08-15' % current_wizard.year, _('Assumption of Mary')],
                           ['%04s-11-01' % current_wizard.year, _('All Saints\' Day')],
                           ['%04s-11-11' % current_wizard.year, _('Armistice Day')],
                           ['%04s-12-25' % current_wizard.year, _('Christmas')]
                           ]

        for legal_day in legal_days_list:
            holiday_period_obj.create({
                    'year_id': year_id.id,
                    'date_start': datetime.strptime(legal_day[0], DEFAULT_SERVER_DATE_FORMAT),
                    'date_stop': datetime.strptime(legal_day[0], DEFAULT_SERVER_DATE_FORMAT),
                    'name': _(legal_day[1]),
                    'category_id': category_legal[0].id,
            })

        # Generate holiday periods for each week-end of requested year
        # NOTE: we use ISO week number, but if the 1st saturday of the
        #       year is before the 1st thursday we force week-num to 0

        year_rule = rrule.rrule(rrule.DAILY, dtstart=year_start, until=year_end, byweekday=rrule.SA)
        for saturday in year_rule:
            iso_year, iso_week_num, iso_weekday = saturday.isocalendar()
            week_num = iso_year == current_wizard.year and iso_week_num or 0
            holiday_period_obj.create({
                'year_id': year_id.id,
                'date_start': saturday.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'date_stop': (saturday+relativedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                'name': _('Week-end %02d') % (week_num,),
                'category_id': category_week_end[0].id,
            }),

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'training.holiday.year',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': year_id.id,
        }
