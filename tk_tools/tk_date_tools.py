import pytz
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class tk_date_tools():
    @staticmethod
    def datetime_timezone(date, timezone=None):
        """
        Convenience method you can call from an email_template
        to return a date from the db (UTC) in the correct timezone.
        To call from the temlpate, just do :
        from tk_email_template.tk_email_template import tk_email_template
        tk_email_template.datetime_timezone
        Default timezone is Europe/Brussels
        """
        if not date:
            return ""
        if not timezone:
            timezone = pytz.timezone("Europe/Brussels")
        utc = pytz.timezone('UTC')
        utc_timestamp = utc.localize(date, is_dst=False)  # UTC = no DST
        date = utc_timestamp.astimezone(timezone)
        return date


    @staticmethod
    def datestring_timezone(date, timezone=None):
        """
        Convenience method to return the correct date in the specified timezone,
        when the date is a string (formatted by OpenERP).
        This method will call datetime_timezone.
        """
        if not date:
            return ""
        date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") if date else None
        return tk_date_tools.datetime_timezone(date, timezone)


    @staticmethod
    def datetime_to_string(datetime_value, format=None):
        if not datetime_value:
            return ""
        if not format:
            format = "%d-%m-%Y %H:%M:%S"
        return datetime.strftime(format)


    @staticmethod
    def datetime_timezone_to_utc(date, timezone=None):
        """
        Convert the specified date from specified timezone to UTC.
        """
        if not date:
            return ""
        if not timezone:
            timezone = pytz.timezone("Europe/Brussels")
        utc = pytz.timezone('UTC')
        timezone_timestamp = timezone.localize(date, is_dst=False)
        date = timezone_timestamp.astimezone(utc)
        return date

    @staticmethod
    def datestring_timezone_to_utc(date_param, timezone=None):
        """
        Convenience method that will call datetime_timezone_to_utc.
        """
        if not date_param:
            return ""
        new_date = datetime.strptime(date_param, "%Y-%m-%d %H:%M:%S")
        return tk_date_tools.datetime_timezone_to_utc(new_date, timezone)

    @staticmethod
    def datetime_utc_to_timezone(date_param, timezone=None):
        """
        Convert the specified date from UTC to the specified timezone.
        Convenience method you can call from an email_template
        to return a date from the db (UTC) in the correct timezone.
        To call from the temlpate, just do :
        from tk_tools.tk_date_tools import tk_date_tools
        tk_date_tools.datetime_timezone
        Default timezone is Europe/Brussels
        """
        if not date_param:
            return ""
        if not timezone:
            timezone = pytz.timezone("Europe/Brussels")
        utc = pytz.timezone('UTC')
        utc_timestamp = utc.localize(date_param, is_dst=False)  # UTC = no DST
        new_date = utc_timestamp.astimezone(timezone)
        return new_date


    @staticmethod
    def datestring_utc_to_timezone(date_param, timezone=None):
        """
        Convenience method to return the correct date in the specified timezone,
        when the date is a string (formatted by OpenERP).
        This method will call datetime_utc_to_timezone.
        """
        if not date_param:
            return ""
        if not timezone:
            timezone = pytz.timezone("Europe/Brussels")
        try:
            date = datetime.strptime(date_param, "%Y-%m-%d %H:%M:%S")
            return tk_date_tools.datetime_utc_to_timezone(date, timezone)
        except Exception, e:
            logger.warning("Cannot convert date %s" % date_param)
            logger.warning(e)
            return ""

    @staticmethod
    def datestring_to_datetime(datestring, format=None):
        if not datestring:
            return False
        if not format:
            format = "%Y-%m-%d %H:%M:%S"
        try:
            return datetime.strptime(datestring, format)
        except Exception, e:
            logger.warning("Cannot convert string %s to date with format %s" % (datestring, format))
            logger.warning(e)
            return False


    @staticmethod
    def get_string_from_float(value):
        """
        Get hour and min from time_float used in float field with the widget float_time
        """
        if not value:
            return False
        min = float(value) - int(value)
        hour = str(int(value))
        min = str(int(round(min * 60)))
        if len(hour) < 2:
            hour = "0" + hour
        if len(min) < 2:
            min = "0" + min
        return hour, min


    @staticmethod
    def get_time_string_from_float_time(value):
        """
        Get the time string (HH:MM) from time_float
        """
        hour, min = tk_date_tools.get_string_from_float(value)
        return '%s:%s' % (hour, min)