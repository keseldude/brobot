# BROBOT

## About
brobot is an simple, extensible IRC bot written in Python, created by Michael Keselman.

* IRC library written from scratch, following current python standards
* Easy to use plugin interface that lets you
    * Code functionality for commands
    * Hook into any IRC event
* Open Source
* Flexible YAML settings file
* Uses python's multiprocessing library instead of threads

## How To Use

1. Clone the repository

        $ git clone git://github.com/keseldude/brobot.git brobot
    
2. Copy the example settings file

        $ cp settings.example.yaml settings.yaml
    
3. Modify the settings to connect to the right servers, channels, etc.
4. Optionally write some plugins and put them in the plugins directory
5. Run the script

        $ python brobot.py

## TODO

* Manage users in channel (list of users, which modes they have, etc.)
* SSL support
* Write good responses for most of the codes in the IRC protocol
* Document everything
* Add more "standard" command plugins like
    * Help
    * Users
    * Version
* Recover from ping timeouts
