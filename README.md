# collectd

[![Build Status](https://travis-ci.com/iroquoisorg/ansible-role-collectd.svg?branch=master)](https://travis-ci.com/iroquoisorg/ansible-role-memcached)

Ansible role for collectd

This role was prepared and tested for Ubuntu 16.04.

# Installation

`$ ansible-galaxy install iroquoisorg.collectd`

# Default settings

```
collectd_configs: []
collectd_rabbitmq: false
collectd_rundeck: false
collectd_customtypes: []
collectd_nginx_status_url: "http://localhost/nginx_status"

```
