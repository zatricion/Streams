from __future__ import absolute_import, unicode_literals

from celery.bin import worker as w
from celery import current_app
from celery import task

@task
def test():
    print "hello"

def start():
    app = current_app._get_current_object()
    app.config_from_object('celeryconfig') 

    worker = w.worker(app=app)
    worker.run()