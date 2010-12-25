.. brobot documentation master file, created by
   sphinx-quickstart on Sun Dec 12 13:07:59 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to brobot's documentation!
==================================

:author: Michael Keselman <mkes@brandeis.edu>

Contents:

.. toctree::
   :maxdepth: 2
   
   todo.rst

Introduction
------------
brobot is an simple, extensible IRC bot written in Python.

* IRC library written from scratch, following current python standards
* Easy to use plugin interface that lets you
    * Code functionality for commands
    * Hook into any IRC event
* Free and Open Source
* Flexible YAML settings file

How to use
----------
1. Clone the repository

        $ git clone git://github.com/keseldude/brobot.git brobot
    
2. Copy the example settings file

        $ cp settings.example.yaml settings.yaml
    
3. Modify the settings to connect to the right servers, channels, etc.
4. Optionally write some plugins and put them in the plugins directory
5. Run the script

        $ python brobot.py


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

