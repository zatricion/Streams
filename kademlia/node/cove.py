from __future__ import absolute_import, unicode_literals

from celery.bin import worker
from celery import current_app

@task
def test():
    print "hello"

def start(self):
    self.app = current_app._get_current_object()
    self.app.config_from_object('celeryconfig') 

    self.worker = worker.worker(app=self.app)
    self.worker.run()
