# -*- coding: utf-8 -*-
import openerp.addons.connector.backend as backend

taktik_importer_custom = backend.Backend('taktik_importer_custom')
taktik_importer_backend_custom = backend.Backend(parent=taktik_importer_custom, version='1.0.0')