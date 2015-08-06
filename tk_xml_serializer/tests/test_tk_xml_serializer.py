# -*- coding: utf-8 -*-
##############################################################################
#
# Authors: Lefever David
# Copyright (c) 2015 Taktik SA/NV (http://www.taktik.be)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from anybox.testing.openerp import SharedSetupTransactionCase
from datetime import datetime, timedelta
from openerp.addons.tk_xml_serializer.tk_xml_serializer import serializer
from openerp import pooler
from StringIO import StringIO

try:
    from lxml import etree

    print("running with lxml.etree")
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree

        print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree

            print("running with ElementTree on Python 2.5+")
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree

                print("running with cElementTree")
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree

                    print("running with ElementTree")
                except ImportError:
                    print("Failed to import ElementTree from any known place")


class TestXMLSerializer(SharedSetupTransactionCase):
    _data_files = ()

    _module_ns = 'tk_xml_serializer'

    def setUp(self):
        super(TestXMLSerializer, self).setUp()
        self.json_pattern = self.env['tk.json.pattern']
        self.sale_order = self.env['sale.order']
        self.partner = self.env['res.partner']
        self.product = self.env['product.product']

        self.env['ir.model'].clear_caches()
        self.env['ir.model.data'].clear_caches()

    def test_deserialize(self):
        cr, uid = self.cr, self.uid

        # Create partner
        vals = {
            'name': 'My Partner',
        }
        partner_id = self.partner.create(vals)

        # Create product
        vals = {
            'name': 'Product',
            'type': 'product',
            'purchase_ok': True,
            'default_code': 'P0001',
        }
        product_id = self.product.create(vals)

        # Create tk.json.pattern
        json_pattern = """
{
    "name": "SO Pattern",
    "url": "http://...",
    "realm": "realm",
    "login": "taktikhttp",
    "password": "test",
    "model": "sale.order",
    "xpath": "Doc",
    "date_format": "format",
    "date_format_sent": "format",
    "fields": [
        {
            "xpath": "Doc/date"
        },
        {
            "multi": "True",
            "xpath": "Doc/SO",
            "fields": [
                {
                    "name": "amount_total",
                    "xpath": "Doc/SO/amount_total"
                },
                {
                    "name": "user_id",
                    "xpath": "Doc/SO/user_name",
                    "fields": [
                        {
                            "name": "login",
                            "xpath": "Doc/SO/user_name"
                        }
                    ]
                },
                {
                    "name": "partner_id",
                    "xpath": "Doc/SO/partner",
                    "fields": [
                        {
                            "name": "name",
                            "xpath": "Doc/SO/partner"
                        }
                    ]
                },
                {
                    "name": "currency_id",
                    "xpath": "Doc/SO/currency",
                    "fields": [
                        {
                            "name": "name",
                            "xpath": "Doc/SO/currency"
                        }
                    ]
                },
                {
                    "name": "pricelist_id",
                    "xpath": "Doc/SO/pricelist",
                    "fields": [
                        {
                            "name": "name",
                            "xpath": "Doc/SO/pricelist"
                        }
                    ]
                },
                {
                    "name": "order_line",
                    "xpath": "Doc/SO/lines/line",
                    "fields": [
                        {
                            "name": "price_unit",
                            "xpath": "Doc/SO/lines/line/price_unit"
                        },
                        {
                            "name": "name",
                            "xpath": "Doc/SO/lines/line/name"
                        },
                        {
                            "name": "product_id",
                            "xpath": "Doc/SO/lines/line/default_code",
                            "fields": [
                                {
                                    "name": "default_code",
                                    "xpath": "Doc/SO/lines/line/default_code"
                                }
                              ]
                        }
                    ]
                }
            ]
        }
    ]
}
"""

        so_model_id = self.env['ir.model'].search([('model', '=', 'sale.order')])[0]
        pattern_id = self.json_pattern.create({'name': 'Simple SO Pattern',
                                               'model_id': so_model_id.id,
                                               'json_pattern': json_pattern})

        so_xml = """<Doc>
<SO>
    <amount_total>10</amount_total>
    <user_name>admin</user_name>
    <partner>My Partner</partner>
    <currency>EUR</currency>
    <pricelist>Public Pricelist</pricelist>
    <partner>My Partner</partner>
    <lines>
        <line>
            <name>Product</name>
            <default_code>P0001</default_code>
            <price_unit>5</price_unit>
        </line>
        <line>
            <name>Product</name>
            <default_code>P0001</default_code>
            <price_unit>15</price_unit>
        </line>
        <line>
            <name>Product</name>
            <default_code>P0001</default_code>
            <price_unit>25</price_unit>
        </line>
    </lines>
</SO>
</Doc>
"""

        so_id = serializer(cr, uid, pooler.get_pool(self.cr.dbname), pattern_id=pattern_id.id, xml=so_xml).deserialize_object()
        so = self.sale_order.browse(so_id)
        self.assertEqual(so.user_id.login, 'admin')
        self.assertEqual(len(so.order_line), 3)
        self.assertEqual(so.order_line[0].product_id.name, 'Product')
        self.assertEqual(so.order_line[0].product_id.default_code, 'P0001')

    def test_serialize(self):
        cr, uid = self.cr, self.uid

        # Create partner
        vals = {
            'name': 'My Partner',
        }
        partner_id = self.partner.create(vals)

        # Create product
        vals = {
            'name': 'Product',
            'type': 'product',
            'purchase_ok': True,
            'default_code': 'P0001',
        }
        product_id = self.product.create(vals)

        # SO lines
        line = {
            'name': 'Product',
            'product_id': product_id.id,
        }

        # Create SO
        vals = {
            'partner_id': partner_id.id,
            'order_line': [[0, False, line], [0, False, line], [0, False, line]],
        }
        so = self.sale_order.create(vals)

        # Create tk.json.pattern
        json_pattern = """
{
    "name": "SO Pattern",
    "url": "http://...",
    "realm": "realm",
    "login": "taktikhttp",
    "password": "test",
    "model": "sale.order",
    "xpath": "Doc",
    "date_format": "format",
    "date_format_sent": "format",
    "fields": [
        {
            "xpath": "Doc/date"
        },
        {
            "multi": "True",
            "xpath": "Doc/SO",
            "fields": [
                {
                    "name": "amount_total",
                    "xpath": "Doc/SO/amount_total"
                },
                {
                    "name": "user_id",
                    "xpath": "Doc/SO/user_name",
                    "fields": [
                        {
                            "name": "login",
                            "xpath": "Doc/SO/user_name"
                        }
                    ]
                },
                {
                    "name": "partner_id",
                    "xpath": "Doc/SO/partner",
                    "fields": [
                        {
                            "name": "name",
                            "xpath": "Doc/SO/partner"
                        }
                    ]
                },
                {
                    "name": "currency_id",
                    "xpath": "Doc/SO/currency",
                    "fields": [
                        {
                            "name": "name",
                            "xpath": "Doc/SO/currency"
                        }
                    ]
                },
                {
                    "name": "pricelist_id",
                    "xpath": "Doc/SO/pricelist",
                    "fields": [
                        {
                            "name": "name",
                            "xpath": "Doc/SO/pricelist"
                        }
                    ]
                },
                {
                    "name": "order_line",
                    "xpath": "Doc/SO/lines/line",
                    "fields": [
                        {
                            "name": "price_unit",
                            "xpath": "Doc/SO/lines/line/price_unit"
                        },
                        {
                            "name": "name",
                            "xpath": "Doc/SO/lines/line/name"
                        },
                        {
                            "name": "product_id",
                            "xpath": "Doc/SO/lines/line/default_code",
                            "fields": [
                                {
                                    "name": "default_code",
                                    "xpath": "Doc/SO/lines/line/default_code"
                                }
                              ]
                        }
                    ]
                }
            ]
        }
    ]
}
"""
        so_model_id = self.env['ir.model'].search([('model', '=', 'sale.order')])[0]
        pattern_id = self.json_pattern.create({'name': 'Simple SO Pattern',
                                               'model_id': so_model_id.id,
                                               'json_pattern': json_pattern})
        xml = serializer(cr, uid, pooler.get_pool(self.cr.dbname), pattern_id=pattern_id.id).serialize_object(so.id)
        root = etree.parse(StringIO(xml))
        self.assertEqual(root.find('SO/user_name').text, 'admin')
        self.assertEqual(len(root.findall('SO/lines/line')), 3)
        self.assertEqual(root.findall('SO/lines/line[0]/default_code')[0].text, 'P0001')
