# encoding_workflow #

The project is composed from various celery tasks in the adaptation python package. One should only call high level task encoding_workflow in the commons.py module. An example of use of this task can be found in "MyCommand.txt"

## Context ##

The context dict is the only arg that is passed from task task. It has various helper functions that help computing eg. resources path.

## installation ##

### Celery on Debian ###

sudo apt-get install python-pip mediainfo ffmpeg gpac
sudo pip install celery pymediainfo

### Celery As a Daemon ###

follow instructions given at http://celery.readthedocs.org/en/latest/tutorials/daemonizing.html#generic-init-scripts

## Deployment ##

To deploy the hv adaptation worker, run the "deploy.sh", if it does not work, use chmod.

Once this is done the worker can be used.

### Configuration, Run ### 

An example of command to run the code is located in "Mycommand.txt". All the parameters are explained in this file. Choose a video, an output folder and you can launch a task. If it does not work, use chmod.

Configuration options are in the settings.py file. You can configure the broker url

```python
    BROKER_URL = 'amqp://guest:guest@172.16.1.1' #connection to the message broker
    CELERY_RESULT_BACKEND = 'amqp://guest:guest@172.16.1.1' #that's to connect to result backend
```

Note :

if your worker is called worker 1, logs are located in 

    /var/log/celery/worker1.log

## A Task Scenario ##

* A task is given the context by *args
* Some named arguments that are retrieved by **kwargs. 
* All named arguments should be added to the context dict. 
* Context fields should be used in the task business. 
* Context should be returned by the task to be used by the next task.


## Workflow ##

Here is a description on how the encoding workflow tasks work. Some long stating task run in parallel on different workers thanks to a celery chord

    _________________   _______________   ____________________   _________________
    | DOWNLOAD FILE |___|GET VIDEO SIZE|__|GET VIDEO THUMBNAIL|__| CREATE YUV FILE|______________     
    |_______________|   |______________|  |___________________|  |________________|              |
                                                                                                 |
                                                                                                 |
                                                                                _________________|__________________ 
                                                                                |       For the low, medium         \
                                                                                |       and high bitrates           |\
                                                                                |       _____________________       | \
                                                                                |       |COMPUTE TARGET SIZE |      | |\
                                                                                |       |____________________|      | | \
                                                                                |                |                  | | |
                                                                                |        ________|_____________     | | |
                                                                                |        |  TRANSCODE          |    | | |
                                                                                |        |_____________________|    | | |
                                                                                |                |                  | | |
                                                                                |________________|__________________| | |
                                                                                  \______________|___________________\| |
                                                                                    \____________|___________________ \_|
                                                                                                 |
                                                                                                 | 
                                                                                         ________|____________
                                                                                        | CREATE DESCRIPTIONS |
                                                                                        |_____________________|     
                                                                                                 |
                                                                                                 |
                                                                                _________________|_________________          
                                                                                |       For each description        \
                                                                                |                                   |\
                                                                                |       _____________________       | \
                                                                                |       |   CONVERT TO MP4   |      | |\
                                                                                |       |____________________|      | | \
                                                                                |               |                   | | |
                                                                                |        _______|______________     | | |
                                                                                |        |  CHUNK DASH         |    | | |
                                                                                |        |_____________________|    | | |
                                                                                |              |                    | | |
                                                                                |        ______|_________________   | | |
                                                                                |       |   ZIP THE DESCRIPTIONS |  | | |
                                                                                |       |________________________|  | | | 
                                                                                |        ______|________________    | | |
                                                                                |        |  ZIP THE MPDS        |   | | |
                                                                                |        |______________________|   | | |
                                                                                |______________|____________________| | |
                                                                                  \____________|____________________\| |
                                                                                    \__________|____________________  \_|
                                                                                        _______|____________
                                                                                        | SEND THE VIDEO ID |
                                                                                        | TO THE MANAGER    |  
                                                                                        |___________________|
                                                                                        _______|_________________
                                                                                        | DELETE USELESS FOLDERS |
                                                                                        |________________________|
                                                                                               |
                                                                                               |
                                                                                               |
                                                                                        _______|_________________
                                                                                        |   NOTIFICATION         |
                                                                                        |________________________|
## Notifications ##

A notification task, which is passed the highest level task_id, is called when required and update the status, which triggers a json message sent to the result backend. A consumer should listen to the queue named after the task_id given at creation time
