
import pytz
import datetime
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
        utc_timestamp = utc.localize(date, is_dst=False) # UTC = no DST
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
        date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S") if date else None
        return tk_date_tools.datetime_timezone(date, timezone)


    @staticmethod
    def datetime_to_string(datetime, format=None):
        if not datetime:
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
    def datestring_timezone_to_utc(date, timezone=None):
        """
        Convenience method that will call datetime_timezone_to_utc.
        """
        if not date:
            return ""
        date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S") if date else None
        return tk_date_tools.datetime_timezone_to_utc(date, timezone)

    @staticmethod
    def datetime_utc_to_timezone(date, timezone=None):
        """
        Convert the specified date from UTC to the specified timezone.
        Convenience method you can call from an email_template
        to return a date from the db (UTC) in the correct timezone.
        To call from the temlpate, just do :
        from tk_tools.tk_date_tools import tk_date_tools
        tk_date_tools.datetime_timezone
        Default timezone is Europe/Brussels
        """
        if not date:
            return ""
        if not timezone:
            timezone = pytz.timezone("Europe/Brussels")
        utc = pytz.timezone('UTC')
        utc_timestamp = utc.localize(date, is_dst=False) # UTC = no DST
        date = utc_timestamp.astimezone(timezone)
        return date


    @staticmethod
    def datestring_utc_to_timezone(date, timezone=None):
        """
        Convenience method to return the correct date in the specified timezone,
        when the date is a string (formatted by OpenERP).
        This method will call datetime_utc_to_timezone.
        """
        if not date:
            return ""
        if not timezone:
            timezone = pytz.timezone("Europe/Brussels")
        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S") if date else None
            return tk_date_tools.datetime_utc_to_timezone(date, timezone)
        except Exception, e:
            logger.warning("Cannot convert date %s" % date)
            logger.warning(e)
            return ""

    @staticmethod
    def datestring_to_datetime(datestring, format=None):
        if not datestring:
            return False
        if not format:
            format = "%Y-%m-%d %H:%M:%S"
        try:
            return datetime.datetime.strptime(datestring, format)
        except Exception, e:
            logger.warning("Cannot convert string %s to date with format %s" % (datestring, format))
            logger.warning(e)
            return False