# coding=utf-8
{
    "name": "Taktik Worklog Flags",
    "version": "1.0",
    "author": "Taktik S.A.",
    "category": "Generic Modules/Others",
    "website": "http://www.taktik.be",
    "description": """
    Taktik Worklog Flags
    This module allows you to flag worklogs as invoiced or internal.
    """,
    "depends": ['account', 'project', 'hr_timesheet_invoice'],
    "init_xml": [],
    "demo_xml": [],
    "data": [
        "wizard/tk_worklog_invoice_view.xml",
        "wizard/tk_worklog_internal_view.xml",
        "view/tk_hr_timesheet_invoice_view.xml",
    ],
    "active": False,
    "installable": True
}
