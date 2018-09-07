#!/usr/bin/python

import collectd
import os
import sys
import time
import httplib
import urllib
import json
from pprint import pprint
from rundeck.client import Rundeck

rd = None

RUNDECK_CONFIG = {
    'Verbose': False,
    'Token': None,
    'Host': None,
    'Project': None
}

def list_jobs(project, group):
    print filter_jobs(project, group)

def count_disabled(project, group):
    from pprint import pprint
    jobs = filter(lambda x: x['group']==group, rd.list_jobs(project))
    return len(filter(lambda x: get_job_metadata(x['id'])['scheduleEnabled']==False, jobs ))

def count_enabled(project, group):
    jobs = filter(lambda x: x['group']==group, rd.list_jobs(project))
    return len(filter(lambda x: get_job_metadata(x['id'])['scheduleEnabled']==True, jobs ))

def filter_jobs(project, group):
    jobs = filter(lambda x: x['group']==group, rd.list_jobs(project))
    return ','.join(map(lambda x: x['id'], jobs))

def get_job_metadata(id):
    return apicall('job/'+id+'/info', 'GET')

def get_recent_executions(project):
    return apicall('project/'+project+'/executions', 'GET')['executions']

def apicall(url, method = 'POST', data = None):
    headers = {"X-Rundeck-Auth-Token" : RUNDECK_CONFIG['Token'], 'Accept':'application/json' }
    conn = httplib.HTTPConnection(RUNDECK_CONFIG['Host']+':80')
    if (data):
        data = '?'+urllib.urlencode(data)
    else:
        data = ''
    conn.request(method, '/api/19/'+url+data, '', headers)
    response = conn.getresponse()
    return json.loads(response.read())

def count_running(project):
    return len(filter(lambda x: x['project'] == project, rd.list_running_executions()))

def dispatch_value(prefix, metric, value, type, type_instance=None):

    log_verbose('Sending value: %s/%s=%s' % (prefix, metric, value))
    value = int(value) # safety check

    val               = collectd.Values(plugin='rundeck', plugin_instance=prefix)
    val.type          = type
    val.type_instance = metric
    val.values        = [value]
    val.dispatch()

def log_verbose(msg):
    if RUNDECK_CONFIG['Verbose'] == False:
        return
    collectd.info('varnish plugin: %s' % msg)

def configure_callback(conf):
    global RUNDECK_CONFIG
    global rd
    for node in conf.children:
        if node.key in RUNDECK_CONFIG:
            RUNDECK_CONFIG[node.key] = node.values[0]
    rd = Rundeck(RUNDECK_CONFIG['Host'], port=80, api_token=RUNDECK_CONFIG['Token'])

def read_callback():
    # jobs enabled
    val_enabled = count_enabled(RUNDECK_CONFIG['Project'], 'cron/active')
    dispatch_value(
        'default-rundeck',
        'jobs_enabled',
        val_enabled,
        'gauge'
    )

    # jobs running
    var_running = count_running(RUNDECK_CONFIG['Project'])
    dispatch_value(
        'default-rundeck',
        'jobs_running',
        var_running,
        'gauge'
    )


    # duration
    executions = get_recent_executions(RUNDECK_CONFIG['Project'])
    jobs = {}
    for execution in executions:
        job_name = execution['job']['name']
        jobs[job_name] = execution['job']['averageDuration']

    for job in jobs:
        dispatch_value(
            'default-rundeck',
            'job_avg_duration_'+job,
            jobs[job],
            'gauge'
        )



collectd.register_read(read_callback)
collectd.register_config(configure_callback)
