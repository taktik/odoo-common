from openerp.osv import orm, fields, osv


class tk_res_company(orm.Model):
    _inherit = 'res.company'

    def get_parent_company_id(self, cr, uid, child_company_id):

        """
        Return the company a the highest level of the companies hierarchy
        """
        res_company_obj = self.pool.get('res.company')
        child_company = res_company_obj.browse(cr, uid, child_company_id)
        parent_company = child_company.parent_id
        while parent_company:
            child_company = parent_company
            parent_company = child_company.parent_id

        return child_company.id
