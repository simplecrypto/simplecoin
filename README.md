Simple Coin
===========

This repo is a generic version of http://simpledoge.com and http://simplevert.com.
This includes all Celery tasks for handling the PowerPool stratum mining servers
output.

Getting Started
===============

Simple Doge makes use of PostgreSQL and Redis, as well as RabbitMQ if you'll
be running a test powerpool instance for end to end testing. Setup is designed
to run on Ubuntu 12.04. If you're doing development you'll also want to install
Node since Grunt is used.

    apt-get install redis-server postgresql-contrib-9.1 postgresql-9.1 postgresql-server-dev-9.1 
    # to install rabbitmq as well
    apt-get install rabbitmq-server
    # add the ppa that includes latest version of nodejs. Ubuntu repos are really out of date
    sudo add-apt-repository ppa:chris-lea/node.js
    sudo apt-get install nodejs

Now you'll want to setup a Python virtual enviroment to run the application in.
This isn't stricly necessary, but not using virtualenv can cause all kinds of 
headache, so it's *highly* recommended. You'll want to setup virtualenvwrapper 
to make this easier.

    # make a new virtual enviroment for simpledoge
    mkvirtualenv sd
    # clone the source code repo
    git clone https://github.com/ericecook/simpledoge.git
    cd simpledoge
    pip install -e .
    # install all python dependencies
    pip install -r requirements.txt
    pip install -r dev-requirements.txt
    # install nodejs dependencies for grunt
    sudo npm install -g grunt-cli  # setup grunt binary globally
    npm install  # setup all the grunt libs local to the project

Initialize an empty PostgreSQL database for simpledoge.

    # creates a new user with password testing, creates the database, enabled
    # contrib extensions
    ./util/reset_db.sh
    # creates the database schema for simpledoge
    python manage.py init_db

Now everything should be ready for running the server. This project uses Grunt
in development to watch for file changes and reload the server.

    grunt watch

This should successfully start the development server if all is well. If not,
taking a look at the webserver log or gunicorn log can help.

    tail -f websever.log
    tail -f gunicorn.log
    
It's also possible that gunicorn is failing to start completely, in which case you can run it
by hand to see what's going wrong.
    
    gunicorn simplecoin.wsgi_entry:app -p gunicorn.pid -b 0.0.0.0:9400 --access-logfile gunicorn.log
    
If you're running powerpool as well you'll need to start a celery worker to process
the tasks (found shares/blocks/stats etc) that it generates. You can run the worker
like this:
    
    python simplecoin/celery_entry.py -l INFO
    
To perform various periodic tasks, run the scheduler program. This computes
various cached values, generates `Payout` entries for solved blocks (records of
what users got paid for the block), and many other vital tasks.

    python simplecoin/scheduler.py
    
Production
===============

> ## NOTE
> These instructions are incomplete and setting up SimpleCoin for
> production will require at least some knowledge of Python, patience, and the
> ability to read through code. I'll be improving this documentation in the near
> future, but as of now it is **INCOMPLETE**.

Paying out users for Mature blocks is done by an RPC system. General system
operation is split into two parts:

1. The server that hosts the website and mining server doesn't hold wallets at
   all. This allows `disablewallet=1` to be used on the mining node making it
   faster (fewer orphans that way), and also provides better security (funds
   are not at a publicly advertised server).
2. Payout wallets, along with a separate instance of simplecoin, are setup to
   be run on a special server (although could run on the same server for
   testing or simplified setup).

SimpleCoin installs a command called `sc_rpc` which allows you to make RPC
calls to perform actions such as:

1. Paying out Mature block rewards to end users.
1. Unlocking locked payouts.
1. Marking payout transactions as "confirmed" after some number of confirms.

The relevant configuration values for the RPC *client* (payout server) are:

1. `trans_confirms` (merge config and normal) both for merged coins and
   non-merged
2. `coinserv` (merge config and normal) which should include the wallet
   "account" to draw funds from, as well as the wallet password (if encrypted)
3. `minimum_payout` This is currently not implemented in a way that works, set
   to 0
4. `payout_fee` this will be the value passed to the `settxfee` command before
   running `sendmany` to payout users.
5. `rpc_signature` This needs to be identical on both client and server. Make
   this STRONG! Like, might as well be stupidly strong, since you never have to
   type it in.
6. `rpc_url` where to access to main webserver

All other config values can be ignored on the RPC client, as they take no effect.

Payout server should probably run RPC using a [cron scheduler](http://kvz.io/blog/2007/07/29/schedule-tasks-on-linux-using-crontab/). Examples include

````
  0,10,20,30,40,50 *  *   *   * /path/to/simplecoin/virtualenv/bin/sc_rpc -l INFO proc_trans -d /path/to/record/locked/payouts/payout_data >> payout.log
  0,10,20,30,40,50 *  *   *   * /path/to/simplecoin/virtualenv/bin/sc_rpc -l INFO confirm_trans >> confirm.log
2 0,4,8,12,16,20  *   *   *     /path/to/simplecoin/virtualenv/bin/sc_rpc -l INFO proc_trans -d /path/to/record/locked/payouts/payout_data -m PTC >> payout.log
2 0,4,8,12,16,20  *   *   *     /path/to/simplecoin/virtualenv/bin/sc_rpc -l INFO proc_trans -d /path/to/record/locked/payouts/payout_data -m TCO >> payout.log
2 0,4,8,12,16,20  *   *   *     /path/to/simplecoin/virtualenv/bin/sc_rpc -l INFO proc_trans -d /path/to/record/locked/payouts/payout_data -m ULTC >> payout.log
````

More help on command arguments can be gotten from:
````
sc_rpc --help
sc_rpc proc_trans --help
sc_rpc confirm_trans --help
````
    
Donate
===============

If you feel so inclined, you can give back to the devs at the below addresses.

DOGE DAbhwsnEq5TjtBP5j76TinhUqqLTktDAnD

BTC 185cYTmEaTtKmBZc8aSGCr9v2VCDLqQHgR

VTC VkbHY8ua2TjxdL7gY2uMfCz3TxMzMPgmRR
