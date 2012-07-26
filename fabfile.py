#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from time import sleep
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.utils import abort
from fabfile_local import *
from subprocess import call
from datetime import datetime

# Globals

env.project_name = 'editorsnotes'

# Environments

def beta():
    "Use the beta-testing webserver."
    env.hosts = ['beta.editorsnotes.org']
    env.path = '/db/projects/%(project_name)s-beta' % env
    env.vhosts_path = '/etc/httpd/sites.d'
    env.python = '/usr/bin/python2.7'
    env.site_packages = ['/usr/lib64/python2.7/site-packages',
                         '/usr/lib/python2.7/site-packages']

def pro():
    "Use the production webserver."
    env.hosts = ['editorsnotes.org']
    env.path = '/db/projects/%(project_name)s' % env
    env.vhosts_path = '/etc/httpd/sites.d'
    env.python = '/usr/bin/python2.7'
    env.site_packages = ['/usr/lib64/python2.7/site-packages',
                         '/usr/lib/python2.7/site-packages']

# Tasks

def test():
    "Run the test suite locally."
    local("python manage.py test" % env)
    
def test_remote():
    "Run the test suite remotely."
    require('hosts', provided_by=[dev])
    require('path')
    run('cd %(path)s/releases/current;  ../../bin/python manage.py test' % env)
    
def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then
    run a full deployment.
    """
    require('hosts', provided_by=[dev])
    require('path')
    run('mkdir -p %(path)s' % env)
    with cd(env.path):
        run('virtualenv -p %(python)s --no-site-packages .' % env)
        run('mkdir -p logs; mkdir -p releases; mkdir -p shared; mkdir -p packages' % env)
        run('cd releases; touch none; ln -sf none current; ln -sf none previous')
    deploy()
    
def deploy():
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and then
    restart the webserver.
    """
    require('hosts', provided_by=[dev])
    require('path')
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')
    upload_tar_from_git()
    upload_local_settings()
    upload_deploy_info()
    symlink_system_packages()
    install_requirements()
    install_site()
    symlink_current_release()
    migrate()
    restart_webserver()
    collect_static()
    sleep(2)
    try:
        type(env.gnome)
        local('gnome-open http://%(host)s/' % env)
    except:
        local('open http://%(host)s/' % env)
    
def deploy_version(version):
    "Specify a specific version to be made live."
    require('hosts', provided_by=[dev])
    require('path')
    env.version = version
    with cd(env.path):
        run('rm releases/previous; mv releases/current releases/previous')
        run('ln -s %(version)s releases/current' % env)
    restart_webserver()
    
def rollback():
    """
    Limited rollback capability. Simple loads the previously current
    version of the code. Rolling back again will swap between the two.
    """
    require('hosts', provided_by=[dev])
    require('path')
    with cd(env.path):
        run('mv releases/current releases/_previous;')
        run('mv releases/previous releases/current;')
        run('mv releases/_previous releases/previous;')
    restart_webserver()

def clean():
    "Clean out old packages and releases."
    require('hosts', provided_by=[dev])
    require('path')
    if (confirm('Are you sure you want to delete everything on %(host)s?' % env, 
                default=False)):
        with cd(env.path):
            run('rm -rf packages; rm -rf releases')
            run('mkdir -p packages; mkdir -p releases')
            run('cd releases; touch none; ln -sf none current; ln -sf none previous')
    
# Helpers. These are called by other functions rather than directly.

def upload_tar_from_git():
    "Create an archive from the current Git branch and upload it."
    require('release', provided_by=[deploy, setup])
    local('git archive --format=tar HEAD | gzip > %(release)s.tar.gz' % env)
    run('mkdir -p %(path)s/releases/%(release)s' % env)
    put('%(release)s.tar.gz' % env, '%(path)s/packages/' % env)
    run('cd %(path)s/releases/%(release)s && tar zxf ../../packages/%(release)s.tar.gz' % env)
    local('rm %(release)s.tar.gz' % env)

def upload_local_settings():
    "Upload the appropriate local settings file."
    require('release', provided_by=[deploy, setup])
    put('deploy/settings-%(host)s.py' % env, 
        '%(path)s/releases/%(release)s/%(project_name)s/settings_local.py' % env)

def upload_deploy_info():
    "Upload information about the version and time of deployment."
    require('release', provided_by=[deploy, setup])
    with open('%(project_name)s/templates/version.txt' % env, 'wb') as f:
        call(['git', 'rev-parse', 'HEAD'], stdout=f)
    with open('%(project_name)s/templates/time-deployed.txt' % env, 'wb') as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M'))
    for filename in ['version.txt', 'time-deployed.txt']:
        put(('%(project_name)s/templates/' % env) + filename,
            ('%(path)s/releases/%(release)s/%(project_name)s/templates/' % env) + filename)

def install_requirements():
    "Install the required packages from the requirements file using pip"
    require('release', provided_by=[deploy, setup])
    run('export SAVED_PIP_VIRTUALENV_BASE=$PIP_VIRTUALENV_BASE; unset PIP_VIRTUALENV_BASE; ' +
        'cd %(path)s; ./bin/pip install -E . -r ./releases/%(release)s/requirements.txt; ' % env +
        'export PIP_VIRTUALENV_BASE=$SAVED_PIP_VIRTUALENV_BASE; unset SAVED_PIP_VIRTUALENV_BASE')

def symlink_system_packages():
    "Create symlinks to system site-packages."
    require('site_packages', provided_by=[dev])
    require('path')
    site_packages = env.path + '/lib/python2.7/site-packages'
    with cd(site_packages):
        with open('requirements.txt') as reqs:
            for line in reqs:
                if line.startswith('# symlink: '):
                    found = False
                    for sys_site_packages in env.site_packages:
                        target = sys_site_packages + '/' + line[11:-1]
                        if exists(target):
                            run('ln -f -s %s' % target)
                            found = True
                    if not found:
                        abort('Missing %s' % target)

def install_site():
    "Add the virtualhost file to apache."
    require('release', provided_by=[deploy, setup])
    put('deploy/vhost-%(host)s.conf' % env,
        '%(path)s/vhost-%(host)s.conf.tmp' % env)
    sudo('cd %(path)s; mv -f vhost-%(host)s.conf.tmp %(vhosts_path)s/vhost-%(host)s.conf' % env, pty=True)

def symlink_current_release():
    "Symlink our current release."
    require('release', provided_by=[deploy, setup])
    with cd(env.path):
        run('rm releases/previous; mv releases/current releases/previous;')
        run('ln -s %(release)s releases/current' % env)
    
def migrate():
    "Update the database"
    require('hosts', provided_by=[dev])
    require('path')
    with cd('%(path)s/releases/current' % env):
        run('../../bin/python manage.py syncdb --noinput')
        for app in [ 'main', 'djotero', 'refine', 'reversion' ]:
            run('../../bin/python manage.py migrate --noinput %s' % app)

def collect_static():
    "Collect static files"
    require('hosts', provided_by=[dev])
    require('path')
    with cd('%(path)s/releases/current' % env):
        run('../../bin/python manage.py collectstatic --noinput')
    
def restart_webserver():
    "Restart the web server."
    sudo('apachectl restart', pty=True)
