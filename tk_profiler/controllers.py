# coding=utf-8
import os
import logging
from datetime import datetime
from tempfile import mkstemp
from . import core

import openerp
import openerp.http as http
from openerp.http import request

logger = logging.getLogger(__name__)


class ProfilerController(http.Controller):
    player_state = 'profiler_player_clear'

    """Indicate the state(css class) of the player:

    * profiler_player_clear
    * profiler_player_enabled
    * profiler_player_disabled
    """

    @http.route('/web/profiler/enable', type='json', auth='user')
    def enable(self):
        logger.info("Enabling")
        core.enabled = True
        ProfilerController.player_state = 'profiler_player_enabled'

    @http.route('/web/profiler/disable', type='json', auth='user')
    def disable(self):
        logger.info("Disabling")
        core.enabled = False
        ProfilerController.player_state = 'profiler_player_disabled'

    @http.route('/web/profiler/clear', type='json', auth='user')
    def clear(self):
        core.profile.clear()
        logger.info("Cleared stats")
        ProfilerController.player_state = 'profiler_player_clear'

    @http.route('/web/profiler/dump', type='http', auth='user')
    def dump(self, token):
        """Provide the stats as a file download.

        Uses a temporary file, because apparently there's no API to
        dump stats in a stream directly.
        """
        handle, path = mkstemp(prefix='profiling')
        core.profile.dump_stats(path)
        stream = os.fdopen(handle)
        os.unlink(path)  # TODO POSIX only ?
        stream.seek(0)
        filename = 'openerp_%s.stats' % datetime.now().isoformat()
        # can't close the stream even in a context manager: it'll be needed
        # after the return from this method, we'll let Python's GC do its job
        return request.make_response(
            stream,
            headers=[
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
                ('Content-Type', 'application/octet-stream')
            ], cookies={'fileToken': int(token)})

    @http.route('/web/profiler/initial_state', type='json', auth='user')
    def initial_state(self):
        registry = openerp.modules.registry.RegistryManager.get(request.session.db)
        cr = registry.cursor()
        uid = request.session.uid
        user = registry.get("res.users")
        return {
            'has_player_group': user.has_group(cr, uid, 'tk_profiler.group_profiler_player'),
            'player_state': ProfilerController.player_state,
        }
