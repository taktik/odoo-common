# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Taktik S.A.
#    Copyright (c) 2015 Taktik S.A. (http://www.taktik.be)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Point of Sale - (Takeaway - Eat-in)",
    "version": "1.0",
    "author": "Taktik S.A.",
    "website": "http://www.taktik.be",
    'summary': "Point of Sale - (Takeaway - Eat-in)",
    "depends": [
        "pos_pricelist",  # OCA/pos for this module
    ],
    "description": """
POS Module
=======================
This module is updating the POS module for to add the ability  to (takeaway and eat-in)

        """,
    "data": [
        "views/tk_pos_takeaway_assets.xml",
        "views/tk_pos_takeaway_views.xml",
    ],
    "qweb": ["static/src/xml/pos.xml"],
    "demo": [],
    "test": [],
    "active": False,
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
}
