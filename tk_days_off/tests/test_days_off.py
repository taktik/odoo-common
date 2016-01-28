# -*- coding: utf-8 -*-
import openerp.tests.common as common
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class TestDaysOff(common.TransactionCase):
    def test_get_number_of_days(self):
        """
        Create an hr.holiday from the 31/12/2015 to 4/01/2016
        Should return only 2days
        """

        # creates necessary entities
        holiday_year_obj = self.env['training.holiday.year']
        holiday_period_obj = self.env['training.holiday.period']
        category_week_end = self.env['training.holidays.category'].create({'name': 'Week-end'})
        category_legal = self.env['training.holidays.category'].create({'name': 'Legal'})
        year = holiday_year_obj.create({'year': 2015})
        # new year
        new_year = holiday_year_obj.create({'year': 2016})
        holiday_period_obj.create({
                    'year_id': new_year.id,
                    'date_start': datetime.strptime('2016-01-01', DEFAULT_SERVER_DATE_FORMAT),
                    'date_stop': datetime.strptime('2016-01-01', DEFAULT_SERVER_DATE_FORMAT),
                    'name': 'New Year\'s Days',
                    'category_id': category_legal[0].id,
        })
        # first WE of 2016
        holiday_period_obj.create({
                'year_id': new_year.id,
                'date_start': datetime.strptime('2016-01-02', DEFAULT_SERVER_DATE_FORMAT),
                'date_stop': datetime.strptime('2016-01-03', DEFAULT_SERVER_DATE_FORMAT),
                'name': 'Week-end 00',
                'category_id': category_week_end[0].id,
        })

        hr_holiday_obj = self.env['hr.holidays']
        nmb_days = hr_holiday_obj._get_number_of_days('2015-12-31 09:00:00', '2016-01-04 18:00:00')

        self.assertEqual(nmb_days, 2)
