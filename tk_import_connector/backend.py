# -*- coding: utf-8 -*-
import openerp.addons.connector.backend as backend

taktik_importer = backend.Backend('taktik_importer')
taktik_importer_backend = backend.Backend(parent=taktik_importer, version='1.0.0')