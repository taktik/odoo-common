# coding=utf-8
from openerp import models, fields


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    internal = fields.Boolean(string="Internal")
