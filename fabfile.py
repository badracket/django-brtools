from __future__ import with_statement
from fabric.api import local, settings, abort, env, run, cd
from fabric.contrib.console import confirm

env.hosts = ["badracket@web389.webfaction.com"]

env.apps = {
  'fpf': { 'shadow': "../apps/fpf", 'git_repository': "https://github.com/badracket/django-apps-fpf.git"   }
}

env.sites = {
  'bruat': { 'shadow': "../sites/bruat", 'git_repository': "https://github.com/badracket/django-sites-bruat.git", 'host': "badracket@web389.webfaction.com"  }             
}

def prepare_deploy():
#    test(app)
    commit()
    push()

def test(app):
    with settings(warn_only=True):
        result = local("./manage.py test %s" % app, capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")

def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def deploy_site(site,webapp):
    if (not site in env.sites):
        raise Exception("Site %s not defined in env.sites" % site)
    site_config = env.sites[site]
    code_dir = "~/webapps/%s/myproject" % webapp
    with settings(warn_only=True):
        if run("test -d %s/.git" % code_dir).failed:
            run("git clone %s %s" % (site_config.git_repository, code_dir))
    with cd(code_dir):
        run("git pull")
        run("%s/../apache2/bin/restart" % code_dir)
        
def deploy_app(app,webapp):
    if (not app in env.apps):
        raise Exception("App %s not defined in env.apps" % app)
    app_config = env.apps[app]
    staging_dir = "~/migrations/staging/%s" % app
    code_dir = "~/webapps/%s/myproject/myproject" % webapp
    
    with settings(warn_only=True):
        if run("test -d %s" % staging_dir).failed:
          run("mkdir %s" % staging_dir)
        if run("test -d %s/.git" % staging_dir).failed:
          run("git clone %s %s" % (app_config.git_repository, staging_dir))
        if run("test -d %s/%s/migrations" % (code_dir,app)).failed:
          run("python2.7 %s/../manage.py schemamigration %s --initial" % (code_dir,app))
          run("python2.7 %s/../manage.py migrate %" % (code_dir,app))
    
    with cd(staging_dir):
        run("git pull")      
          
    with cd(code_dir):
        run("cp -r %s/%s/ %s" % (staging_dir, app, code_dir))
        run("python2.7 ../manage.py collectstatic")
        with settings(warn_only=True):
            result = run("python2.7 ../manage.py schemamigration %s --auto" % app)
            if result.return_code == 0:
                run("python2.7 ../manage.py migrate %s" % app)   
            elif not result.return_code == 1:
                raise Exception(result)
                             
        run("%s/../../apache2/bin/restart" % code_dir)
        
def install_package(package_name):
    package_dir = "~/lib/python2.7"
    
    with cd(package_dir):
        run("pip install %s" % package_name)