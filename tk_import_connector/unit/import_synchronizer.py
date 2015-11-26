# coding=utf-8
import logging
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import ImportSynchronizer

from ..connector import get_environment


_logger = logging.getLogger(__name__)


class TaktikImportSynchronizer(ImportSynchronizer):
    """ Base importer """

    def _before_import(self):
        """ Hook called before the import, when we have the RBS
        data"""
        return

    def _after_import(self):
        """ Hook called at the end of the import """
        return

    def _run(self, data=None):
        return

    def run(self, data=None):
        """ Run the synchronization
        """
        self._before_import()
        self._run(data)
        self._after_import()


class DelayedBatchImport(TaktikImportSynchronizer):
    """ Import the records , by delaying the jobs. """
    _model_name = None

    def _import_row(self, data):
        """ Delay import """
        description = "Taktik Importer: import row %s" % data[0]
        import_row.delay(self.session, self.backend_record.id, data, max_retries=2, priority=0, description=description)


class TaktikImport(TaktikImportSynchronizer):
    """Import the file"""
    _model_name = None


@job
def import_batch(session, backend_id):
    """ Prepare a batch import of records from file """
    env = get_environment(session, backend_id)
    if isinstance(env.backend, list):
        env.backend = env.backend[0]
    importer = env.get_connector_unit(DelayedBatchImport)
    importer.run()


@job
def import_row(session, backend_id, data):
    """ Import a file from Taktik Importer """
    env = get_environment(session, backend_id)
    if isinstance(env.backend, list):
        env.backend = env.backend[0]
    importer = env.get_connector_unit(TaktikImport)
    importer.run(data)
