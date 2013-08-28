from fabric.api import env, local, lcd
from fabric.colors import red, green
from fabric.decorators import task, runs_once
from fabric.utils import abort

import datetime
import fileinput
import importlib
import os
import random
import sys
import time

PROJ_ROOT = os.path.dirname(env.real_fabfile)
env.project_name = 'editorsnotes'

@task
def setup():
    """
    Set up a local development environment

    This command must be run with Fabric installed globally (not inside a
    virtual environment)
    """
    if os.getenv('VIRTUAL_ENV') or hasattr(sys, 'real_prefix'):
        abort(red('Deactivate any virtual environments before continuing.'))
    make_settings()
    make_virtual_env()
    symlink_packages()
    collect_static()
    print ('\nDevelopment environment successfully created.\n' +
           'Create a Postgres database, enter its information into ' +
           'editorsnotes/settings_local.py, and run `fab sync_database` to finish.')

@task
def test():
    "Run the test suite locally."
    with lcd(PROJ_ROOT):
        local('./bin/python manage.py test main admin_custom' % env)

@task
def sync_database():
    "Sync db, make cache tables, and run South migrations"
    with lcd(PROJ_ROOT):
        local('./bin/python manage.py syncdb --noinput')
        create_cache_tables()
        local('./bin/python manage.py migrate --noinput')

@task
def runserver():
    "Run the development server"
    with lcd(PROJ_ROOT):
        local('./bin/python manage.py runserver')

@task
@runs_once
def make_settings():
    """
    Generate a local settings file.

    Without any arguments, this file will go in editorsnotes/settings_local.py.
    If the function is passed an argument that defines env.hosts, this file will
    be placed in the deploy directory with the name settings-{host}.py
    """
    to_create = (['deploy/settings-{}.py'.format(host) for host in env.hosts]
                 or ['editorsnotes/settings_local.py'])

    for settings_file in to_create:
        secret_key = generate_secret_key()
        with lcd(PROJ_ROOT):
            local('if [ ! -f {0} ]; then cp {1} {0}; fi'.format(
                settings_file, 'editorsnotes/example-settings_local.py'))
            for line in fileinput.input(settings_file, inplace=True):
                print line.replace("SECRET_KEY = ''",
                                   "SECRET_KEY = '{}'".format(secret_key)),

@task
def create_cache_tables():
    caches = ['zotero_cache', 'compress_cache']
    tables = local('./bin/python manage.py inspectdb | grep "db_table ="', capture=True)
    for cache in caches:
        if "'{}'".format(cache) in tables:
            continue
        with lcd(PROJ_ROOT):
            local('./bin/python manage.py createcachetable {}'.format(cache))

@task
def watch_static():
    """
    Collect static files as they are modified.

    Reacts to changes of *.css, *.js, and *.less files.
    """
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        abort(red('Install Watchdog python package to watch filesystem files.'))

    EXTS = ['.js', '.css', '.less']

    class ChangeHandler(FileSystemEventHandler):
        def __init__(self, *args, **kwargs):
            super(ChangeHandler, self).__init__(*args, **kwargs)
            self.last_collected = datetime.datetime.now()
        def on_any_event(self, event):
            if event.is_directory:
                return
            if os.path.splitext(event.src_path)[-1].lower() in EXTS:
                now = datetime.datetime.now()
                if (datetime.datetime.now() - self.last_collected).total_seconds() < 1:
                    return
                local('./bin/python manage.py collectstatic --noinput')
                sys.stdout.write('\n')
                self.last_collected = datetime.datetime.now()

    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(
        event_handler, os.path.join(PROJ_ROOT, 'editorsnotes'), recursive=True)
    observer.start()
    print green('\nWatching *.js, *.css, and *.less files for changes.\n')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def make_virtual_env():
    "Make a virtual environment for local dev use"
    with lcd(PROJ_ROOT):
        local('virtualenv .')
        local('./bin/pip install -r requirements.txt')

def symlink_packages():
    "Symlink python packages not installed with pip"
    missing = []
    requirements = (req.rstrip().replace('# symlink: ', '')
                    for req in open('requirements.txt', 'r')
                    if req.startswith('# symlink: '))
    for req in requirements:
        try:
            module = importlib.import_module(req)
        except ImportError:
            missing.append(req)
            continue
        with lcd(os.path.join(PROJ_ROOT, 'lib', 'python2.7', 'site-packages')):
            local('ln -f -s {}'.format(os.path.dirname(module.__file__)))
    if missing:
        abort('Missing python packages: {}'.format(', '.join(missing)))

def collect_static():
    with lcd(PROJ_ROOT):
        local('./bin/python manage.py collectstatic --noinput -v0')

def generate_secret_key():
    SECRET_CHARS = 'abcdefghijklmnopqrstuvwxyz1234567890-=!@#$$%^&&*()_+'
    return ''.join([random.choice(SECRET_CHARS) for i in range(50)])
