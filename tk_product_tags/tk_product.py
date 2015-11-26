# coding=utf-8
from openerp import models, fields, api, _, exceptions, SUPERUSER_ID


class TkProduct(models.Model):
    _inherit = "product.product"

    tag_ids = fields.Many2many(comodel_name='tk.product.tag',
                               column1='product_id',
                               column2='tag_id',
                               relation='product_tag_rel',
                               string='Tags')


class TkProductTag(models.Model):
    _name = "tk.product.tag"

    name = fields.Char(size=128, string="Name")
    product_ids = fields.Many2many(comodel_name='product.product',
                                   column1='tag_id',
                                   column2='product_id',
                                   relation='product_tag_rel',
                                   string='Products')
