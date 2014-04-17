Pool List Tracker
=================

A simple Flask powered website that will let you track different pools in a Cryptocurrency network.

Installation for Dev
====================

    git clone https://github.com/simplecrypto/pool_list.git
    cd pool_list
    mkvirtualenv pl
    pip install -r requirements; pip install -e .; pip install -r dev-requirements.txt
    npm install
    grunt watch
  
A gunicorn server should now be running on localhost:9400. If not, use the gunicorn command
in the Gruntfile to run it manually and track down the problem.

Installation for Prod on Ubuntu 12.04
=====================================

  git clone https://github.com/simplecrypto/pool_list.git
  cd pool_list
  mkvirtualenv pl
  pip install -r requirements; pip install -e .
  
Add an upstart task for Gunicorn

    vim /etc/init/pool_list.conf
  
&nbsp;
  
    description "vert_pool_list"
  
    start on (filesystem)
    stop on runlevel [016]
    
    respawn
    console log
    setuid vertcoin
    setgid vertcoin
    chdir /home/vertcoin/simplevert
    
    exec /home/vertcoin/web_venv/bin/gunicorn pool_list.wsgi_entry:app -b 127.0.0.1:9005
  
Add an upstart task for celery

    start on started postgresql
    stop on stopping postgresql
    
    exec su -s /bin/sh -c 'exec "$0" "$@"' vertcoin -- /home/vertcoin/pools_venv/bin/python /home/vertcoin/pool_list/pool_list/celery_entry.py -l INFO --beat --schedule=/home/vertcoin/pool_list/celerybeat-schedule
    
    respawn
  
Now use nginx or apache to reverse-proxy the site.
