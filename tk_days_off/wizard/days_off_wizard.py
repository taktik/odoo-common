# -*- coding: utf-8 -*-

from openerp import fields, models, api, exceptions, _
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from dateutil import easter
import calendar


class ClbDaysOffWizard(models.TransientModel):
    _name = 'training.holiday.year.wizard'

    year = fields.Integer(
        string='Year',
        required=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True
    )

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_apply(self):
        """
        Creates :
            - training.holiday.year
            - training.holiday.period
            - training.holidays.category
        for all the week-ends and days of statutory leave
        for the year set in the wizard.
        :return:
        """
        if not self.id:
            return False
        holiday_year_obj = self.env['training.holiday.year']
        holiday_period_obj = self.env['training.holiday.period']

        category_week_end = self.env['training.holidays.category'].search(
            [('name', '=', 'Week-end')]
        )
        category_legal = self.env['training.holidays.category'].search(
            [('name', '=', 'Legal')]
        )
        if not category_week_end:
            category_we = self.env['training.holidays.category'].create(
                {'name': _('Week-end')}
            )
            category_week_end = [category_we]
        if not category_legal:
            category_leg = self.env['training.holidays.category'].create(
                {'name': _('Legal')}
            )
            category_legal = [category_leg]
        current_wizard = self[0]
        try:
            year_start = datetime.strptime(
                '%04s-01-01' % current_wizard.year,
                DEFAULT_SERVER_DATE_FORMAT
            )
            year_end = datetime.strptime(
                '%04s-12-31' % current_wizard.year,
                DEFAULT_SERVER_DATE_FORMAT
            )
        except:
            raise exceptions.Warning(_('Error!'), _('Please enter valid year'))

        year_id = holiday_year_obj.create({
            'year': current_wizard.year,
            'company_id': current_wizard.company_id.id
        })

        code = current_wizard.company_id.country_id.code
        if not code:
            raise exceptions.Warning(
                _('Error!'),
                _('The selected company doesnt have a country. \n'
                  '(or the country code is not set)'))

        legal_days_list = []

        # compute specific day
        if code == 'BE' or code == 'FR':
            easter_sunday = easter.easter(current_wizard.year)
            easter_monday = datetime.strftime(
                easter_sunday + timedelta(days=1), DEFAULT_SERVER_DATE_FORMAT)
            ascension = datetime.strftime(
                easter_sunday + timedelta(days=39), DEFAULT_SERVER_DATE_FORMAT)
            pentecost = datetime.strftime(
                easter_sunday + timedelta(days=50), DEFAULT_SERVER_DATE_FORMAT)

            legal_days_list_belgium = [
                ['%04s-01-01' % current_wizard.year, _('New Year\'s Days')],
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

            legal_days_list_france = [
                ['%04s-01-01' % current_wizard.year, _('New Year\'s Days')],
                [easter_monday, _('Easter Monday')],
                ['%04s-05-01' % current_wizard.year, _('Labour day')],
                ['%04s-05-08' % current_wizard.year, _('8 mai 1945')],
                [ascension, _('Ascension')],
                [pentecost, _('Pentecost Monday')],
                ['%04s-07-14' % current_wizard.year, _('France National day')],
                ['%04s-08-15' % current_wizard.year, _('Assumption of Mary')],
                ['%04s-11-01' % current_wizard.year, _('All Saints\' Day')],
                ['%04s-11-11' % current_wizard.year, _('Armistice Day')],
                ['%04s-12-25' % current_wizard.year, _('Christmas')]
            ]

            if code == 'BE':
                legal_days_list = legal_days_list_belgium
            else:
                legal_days_list = legal_days_list_france

        if code == 'US':
            c = calendar.Calendar(firstweekday=calendar.SUNDAY)
            month = 1
            month_cal = c.monthdatescalendar(current_wizard.year, month)
            luther_king_birthday = [
                day for week in month_cal for day in week if day.weekday() == calendar.MONDAY and day.month == month
                ][2]
            month = 2
            month_cal = c.monthdatescalendar(current_wizard.year, month)
            washington_birthday = [
                day for week in month_cal for day in week if day.weekday() == calendar.MONDAY and day.month == month
                ][2]
            month = 5
            month_cal = c.monthdatescalendar(current_wizard.year, month)
            memorial_day = [
                day for week in month_cal for day in week if day.weekday() == calendar.MONDAY and day.month == month
                ][-1]
            month = 9
            month_cal = c.monthdatescalendar(current_wizard.year, month)
            labor_day = [
                day for week in month_cal for day in week if day.weekday() == calendar.MONDAY and day.month == month
                ][0]
            month = 10
            month_cal = c.monthdatescalendar(current_wizard.year, month)
            columbus_day = [
                day for week in month_cal for day in week if day.weekday() == calendar.MONDAY and day.month == month
                ][1]
            month = 11
            month_cal = c.monthdatescalendar(current_wizard.year, month)
            thanksgiving_day = [
                day for week in month_cal for day in week if day.weekday() == calendar.THURSDAY and day.month == month
                ][3]

            legal_days_list_usa = [
                ['%04s-01-01' % current_wizard.year, _('New Year\'s Days')],
                ['%04s-07-04' % current_wizard.year, _('Independence Day')],
                ['%04s-11-11' % current_wizard.year, _('Veterans Day')],
                ['%04s-12-25' % current_wizard.year, _('Christmas Day')],
                [str(luther_king_birthday), _('Birthday of Martin Luther King, Jr.')],
                [str(washington_birthday), _('Washington\'s Birthday')],
                [str(memorial_day), _('Memorial Day')],
                [str(labor_day), _('Labor day')],
                [str(columbus_day), _('Columbus day')],
                [str(thanksgiving_day), _('Thanksgiving Day')],
            ]

            legal_days_list = legal_days_list_usa

        if legal_days_list:

            for legal_day in legal_days_list:
                holiday_period_obj.create({
                        'year_id': year_id.id,
                        'date_start': datetime.strptime(
                            legal_day[0], DEFAULT_SERVER_DATE_FORMAT),
                        'date_stop': datetime.strptime(
                            legal_day[0], DEFAULT_SERVER_DATE_FORMAT),
                        'name': _(legal_day[1]),
                        'category_id': category_legal[0].id,
                        'company_id': current_wizard.company_id.id,
                })

        # Generate holiday periods for each week-end of requested year
        # NOTE: we use ISO week number, but if the 1st saturday of the
        #       year is before the 1st thursday we force week-num to 0

        year_rule = rrule.rrule(
            rrule.DAILY,
            dtstart=year_start,
            until=year_end,
            byweekday=rrule.SA
        )
        for saturday in year_rule:
            iso_year, iso_week_num, iso_weekday = saturday.isocalendar()
            week_num = iso_year == current_wizard.year and iso_week_num or 0
            holiday_period_obj.create({
                'year_id': year_id.id,
                'date_start': saturday.strftime(
                    DEFAULT_SERVER_DATE_FORMAT),
                'date_stop': (saturday+relativedelta(days=1)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT),
                'name': _('Week-end %02d') % (week_num,),
                'category_id': category_week_end[0].id,
                'company_id': current_wizard.company_id.id,
            }),

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'training.holiday.year',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': year_id.id,
        }
