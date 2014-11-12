from report import report_sxw
import time
import pooler
import operator
from tk_tools.tk_date_tools import tk_date_tools
import logging
import netsvc
from report_webkit import webkit_report

logger = logging.getLogger(__name__)


class tk_report_parser(report_sxw.rml_parse):
    @staticmethod
    def register(name, table, rml=False, parser=None, header=True, store=False, replace=False, pool=None, cr=None):
        """Convenience method to register the report_sxw with the given parser"""
        webkit_report.WebKitParser(name, table, rml, parser=parser, header=header, store=store)

    def set_context(self, objects, data, ids, report_type=None):
        """
        For now, we don't do nothing, but if you check the super method,
        the data ditionary is put in the localcontext as 'data'.
        So in the reports, we can access datas like so :
        data['key'].
        """
        super(tk_report_parser, self).set_context(objects, data, ids, report_type=report_type)

    def __init__(self, cr, uid, name, context):
        super(tk_report_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'pooler': pooler,
            'pool': pooler.get_pool(cr.dbname),
            'cr': cr,
            'uid': uid,
            'nl2br': self.nl2br,
            'operator': operator,
            'wizard_lang': context.get('wizard_lang', 'fr_nl'),
            'datestring_utc_to_timezone': tk_date_tools.datestring_utc_to_timezone,
            'datetime_to_string': tk_date_tools.datetime_to_string,
            'datestring_to_datetime': tk_date_tools.datestring_to_datetime,
            'datestring_timezone_to_utc': tk_date_tools.datestring_timezone_to_utc,
            'datetime_timezone_to_utc': tk_date_tools.datetime_timezone_to_utc,
            'datetime_utc_to_timezone': tk_date_tools.datetime_utc_to_timezone,
            'page_break': self.page_break,
            'use_watermark': context.get('use_watermark', False),
        })

        copies_done = context.setdefault('copies_done', 0)
        if copies_done == context.get('nb_copies', 0):
            if 'wizard_lang' in context:
                del context['wizard_lang']
            if 'nb_copies' in context:
                del context['nb_copies']
        else:
            copies_done += 1
            context['copies_done'] = copies_done

    def nl2br(self, text):
        """Replaces new lines (nl) with br
        to display new lines in the reports (html)"""
        if not text:
            return ''

        return text.replace('\n', '<br />')

    def page_break(self, i=None, objects=None):
        if not i or not objects:
            return "<div id='pageBreak' style='page-break-after:always'>&nbsp;</div>"
        if i > 1 and i <= len(objects):
            return "<div id='pageBreak' style='page-break-after:always'>&nbsp;</div>"
        return ""
