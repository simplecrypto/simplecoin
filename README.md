Simple Doge
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
taking a look at the uwsgi log can help.

    tail -f websever.log
    
It's also Usually I have this running in a
possible that gunicorn is failing to start completely, in which case you can run it
by hand to see what's going wrong.
    
    gunicorn simplecoin.wsgi_entry:app -p gunicorn.pid -b 0.0.0.0:9400 --access-logfile gunicorn.log
    
If you're running powerpool as well you'll need to start a celery worker to process
the tasks (found shares/blocks/stats etc) that it generates. You can run the worker
like this:
    
    python simplecoin/celery_entry.py -l INFO --beat


==================== Alternate Guide written By LiveChains UK =======================

This makes the following presumptions

	1: Although the install of virtual enviroment is done during this guide, the end product wont be inside it
	2: Ubuntu 12.04.01 Used for This Guide X64 Bit, Dual Core, 2GB RAM, 20GB RAID 10 100Mbps.
	3: You have at least some linux problem solving skills, google is your friend
	4: Your install is CLEAN, ie you only selected SSH during ubuntu server.
	5: You accept this is BETA at best, using it as a production pool comes with huge risks, there are known bugs
	   in the platform. YOU USE THIS GUIDE AND THIS SOFTWARE AT YOUR OWN RISK LIVECHAINS WILL NOT ACCEPT RESPONCIBILITY
	   IN ANYFORM FOR THE ACTIONS THIS GUIDE MAY TAKE. THIS IS 100% AT YOUR OWN RISK 

################################
# Dependancy Installation      #
################################


	apt-get update
	apt-get upgrade
	apt-get install python-software-properties
	apt-add-repository ppa:chris-lea/node.js
	apt-add-repository ppa:bitcoin/bitcoin -y
	apt-get update
	apt-get install git-core nodejs python2.7-dev python-setuptools python2.7 build-essential redis-server postgresql-contrib-9.1 postgresql-9.1 postgresql-server-dev-9.1 rabbitmq-server git python-pip
	apt-get build-dep bitcoin -y
	easy_install pip
	pip install virtualenv
	pip install virtualenvwrapper

That about coveres the dependancys at this point, youll not we include a bitcoin repo and packages
this is there purley to shrink the APT-GET Commands, it will include all the dependancys that are
required but not listed, for instance the ability to compile wallets and daemons for this to use.

Youll note we install virtualenvwrapper this is specified in the SIMPLECOIN GIT and is good practise,
that said we dont actually use it in this guide, in order to be comprehensive lets cover its set here
just incase you choose to use it.

################################
# VitualENV Configuration Steps#
################################

	mkdir -p ~/.virtualenvs
	echo 'export WORKON_HOME=~/.virtualenvs' >> ~/.bashrc
	echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bashrc
	source ~/.bashrc

If you plan on using virtual env you should now do

	mkvirtualenv sd

And follow the rest of this guide!

###################################
# SimpleCoin Time
###################################

You can Copy and paste this bit, this will get simplecoin, install more requirements and
dependancys, compile what needs doing etc, this CAN on slow systems take some time

	git clone https://github.com/simplecrypto/simplecoin.git
	cd simplecoin
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
	npm install -g grunt-cli
	npm install
	./util/reset_db.sh
	cp config.yml.example config.yml
	python manage.py init_db
	python manage.py runserver

Thats it, you will OBVIOUSLY need to check all the config and update as nessasary, like coin RPC Details
system IP, wallet address, pool fees, payout, blockvalues etc etc 


#################################
# Last Step #
#############

Once you have stratum installed and running you will need to execute

 	    python simplecoin/celery_entry.py -l INFO --beat

this will pass the hashrates from stratum to the frontend, along with share stats, worker stats etcetc
