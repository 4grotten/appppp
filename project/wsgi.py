"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


if os.environ.get("prometheus_multiproc_dir"):
    import atexit
    from prometheus_client import multiprocess

    @atexit.register
    def shutdown_process_handler():
        multiprocess.mark_process_dead(os.getpid())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = get_wsgi_application()

