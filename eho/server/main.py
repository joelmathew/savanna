import logging
from eho.server.scheduler import setup_scheduler
from eho.server.storage.defaults import setup_defaults
from eho.server.utils.api import render
from eventlet import monkey_patch

from flask import Flask
from eho.server.api import v01 as api_v01
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException
from eho.server.storage.storage import setup_storage

monkey_patch(os=True, select=True, socket=True, thread=True, time=True)


def make_app(**local_conf):
    """
    Entry point for Elastic Hadoop on OpenStack REST API server
    """
    app = Flask('eho.api')
    #TODO(slukjanov): is it needed?
    app.config.from_pyfile('etc/eho-api.cfg', silent=True)
    app.config.from_pyfile('../etc/eho-api.cfg', silent=True)
    app.config.from_envvar('EHO_API_CFG', silent=True)
    app.config.update(**local_conf)

    rootLogger = logging.getLogger()
    ll = app.config.pop('LOG_LEVEL', 'WARN')
    if ll:
        rootLogger.setLevel(ll)

    app.register_blueprint(api_v01.rest, url_prefix='/v0.1')

    if app.config['DEBUG']:
        print 'Configuration:'
        for k in app.config:
            print '\t%s = %s' % (k, app.config[k])

    setup_storage(app)
    setup_defaults(app)
    setup_scheduler(app)

    def make_json_error(ex):
        status_code = (ex.code
                       if isinstance(ex, HTTPException)
                       else 500)
        description = (ex.description
                       if isinstance(ex, HTTPException)
                       else str(ex))
        return render({'error': status_code, 'error_message': description},
                      status=status_code)

    for code in default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = make_json_error

    return app
