# varnish_cache-collectd-plugin - varnish_cache.py
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# Authors:
#   Celedhrim <celed+github at ielf.org>
#
# About this plugin:
#   This plugin uses collectd's Python plugin to record varnish information.
#   Better work with Cgraphz ( specific prefix naming )
#
# collectd:
#   http://collectd.org
# varnish:
#   https://www.varnish-cache.org/
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml

import collectd
from subprocess import Popen, PIPE
from xml.dom.minidom import parse
import xml.dom.minidom
import collections

VARNISH_CONFIG = {
    'Varnishstat' : '/usr/bin/varnishstat',
    'Varnishver' : '4',
    'Verbose': False,
}

Stat = collections.namedtuple('Stat', ('graph', 'name','type' ))
STATS = {}

STATS_V3 = {
	'backend_busy': Stat("backend_traffic", "backend_conn_too_many", "derive"),
	'backend_conn': Stat("backend_traffic", "backend_conn_success", "derive"),
	'backend_unhealthy': Stat("backend_traffic", "backend_conn_not_attempted", "derive"),
	'backend_recycle': Stat("backend_traffic", "backend_conn_recycles", "derive"),
	'backend_fail': Stat("backend_traffic", "backend_conn_failures", "derive"),
	'backend_reuse': Stat("backend_traffic", "backend_conn_reuses", "derive"),
	'backend_req': Stat("backend_traffic", "backend_requests_made", "derive"),
	'backend_retry': Stat("backend_traffic", "backend_conn_retry", "derive"),
	'cache_hit': Stat("hit_rate", "cache_hits", "derive"),
	'cache_miss': Stat("hit_rate", "cache_misses", "derive"),
	'cache_hitpass': Stat("hit_rate", "cache_hits_for_pass", "derive"),
	'transient.g_bytes': Stat("memory_usage", "bytes_outstanding_transient", "gauge"),
	'transient.g_space': Stat("memory_usage", "bytes_available_transient", "gauge"),
	's0.g_bytes': Stat("memory_usage", "bytes_outstanding_s0", "gauge"),
	's0.g_space': Stat("memory_usage", "bytes_available_s0", "gauge"),
	'fetch_failed': Stat("bad", "fetch_failed", "derive"),
	'losthdr': Stat("bad", "http_header_overflows", "derive"),
	'backend_unhealthy': Stat("bad", "backend_conn_not_attempted", "derive"),
	'n_wrk_failed': Stat("bad", "thread_creation_failed", "derive"),
	'backend_busy': Stat("bad", "backend_conn_too_many", "derive"),
	'n_wrk_max': Stat("bad", "threads_hit_max", "derive"),
	'accept_fail': Stat("bad", "session_accept_failures", "derive"),
	'client_drop': Stat("bad", "sessions_dropped", "derive"),
	'n_wrk_drop': Stat("bad", "threads_destroyed", "derive"),
	'n_wrk_lqueue': Stat("bad", "length_of_session_queue", "gauge"),
	'esi_warnings': Stat("bad", "esi_parse_warnings", "derive"),
	'esi_errors': Stat("bad", "esi_parse_errors_", "derive"),
	'n_object': Stat("objects", "number_of_objects", "gauge"),
	'n_expired': Stat("expunge", "number_of_expired objects", "derive"),
	'n_lru_nuked': Stat("expunge", "number_of_lru_nuked_objects", "derive"),
	'cache_hit': Stat("request_rate", "cache_hits", "derive"),
	'cache_hitpass': Stat("request_rate", "cache_hits_for_pass", "derive"),
	'cache_miss': Stat("request_rate", "cache_misses", "derive"),
	'backend_conn': Stat("request_rate", "backend_conn_success", "derive"),
	'backend_unhealthy': Stat("request_rate", "backend_conn_not_attempted", "derive"),
	'client_req': Stat("request_rate", "good_client_requests_received", "derive"),
	's_pass': Stat("request_rate", "total_passed_requests_seen", "derive"),
	's_pipe': Stat("request_rate", "total_pipe_sessions_seen", "derive"),
	'client_conn': Stat("request_rate", "sessions_accepted", "derive"),
	'n_wrk_failed': Stat("threads", "thread_creation_failed", "derive"),
	'n_wrk_max': Stat("threads", "threads_hit_max", "derive"),
	'n_wrk': Stat("threads", "total_number_of_threads", "gauge"),
	'n_wrk_create': Stat("threads", "threads_created", "derive"),
	'n_wrk_drop': Stat("threads", "threads_destroyed", "derive"),
	's_bodybytes': Stat("transfer_rates", "body_traffic", "derive"),
	's_hdrbytes': Stat("transfer_rates", "header_traffic", "derive"),
	'uptime': Stat("uptime", "varnish_uptime", "gauge"),
	'n_ban_dups': Stat("vcl_and_bans", "n_duplicate_bans_removed", "derive"),
	'n_ban_add': Stat("vcl_and_bans", "n_new_bans_added", "derive"),
	'n_backend': Stat("vcl_and_bans", "n_backends", "gauge"),
	'n_vcl': Stat("vcl_and_bans", "n_vcl_total", "derive"),
	'n_ban': Stat("vcl_and_bans", "n_total_active bans", "gauge"),
	'n_ban_retire': Stat("vcl_and_bans", "n_old_bans_deleted", "derive"),
	'n_ban_obj_test': Stat("vcl_and_bans", "n_objects_tested", "derive"),
	'n_vcl_discard': Stat("vcl_and_bans", "n_vcl_discarded", "derive"),
	'n_vcl_avail': Stat("vcl_and_bans", "n_vcl_available", "derive")
}

STATS_V4 = {
	'backend_busy': Stat("backend_traffic", "backend_conn_too_many", "derive"),
	'backend_conn': Stat("backend_traffic", "backend_conn_success", "derive"),
	'backend_unhealthy': Stat("backend_traffic", "backend_conn_not_attempted", "derive"),
	'backend_recycle': Stat("backend_traffic", "backend_conn_recycles", "derive"),
	'backend_fail': Stat("backend_traffic", "backend_conn_failures", "derive"),
	'backend_reuse': Stat("backend_traffic", "backend_conn_reuses", "derive"),
	'backend_req': Stat("backend_traffic", "backend_requests_made", "derive"),
	'backend_retry': Stat("backend_traffic", "backend_conn_retry", "derive"),
	'cache_hit': Stat("hit_rate", "cache_hits", "derive"),
	'cache_miss': Stat("hit_rate", "cache_misses", "derive"),
	'cache_hitpass': Stat("hit_rate", "cache_hits_for_pass", "derive"),
	'transient.g_bytes': Stat("memory_usage", "bytes_outstanding_transient", "gauge"),
	'transient.g_space': Stat("memory_usage", "bytes_available_transient", "gauge"),
	's0.g_bytes': Stat("memory_usage", "bytes_outstanding_s0", "gauge"),
	's0.g_space': Stat("memory_usage", "bytes_available_s0", "gauge"),
	'fetch_failed': Stat("bad", "fetch_failed", "derive"),
	'losthdr': Stat("bad", "http_header_overflows", "derive"),
	'backend_unhealthy': Stat("bad", "backend_conn_not_attempted", "derive"),
	'threads_failed': Stat("bad", "thread_creation_failed", "derive"),
	'backend_busy': Stat("bad", "backend_conn_too_many", "derive"),
	'threads_limited': Stat("bad", "threads_hit_max", "derive"),
	'sess_fail': Stat("bad", "session_accept_failures", "derive"),
	'sess_drop': Stat("bad", "sessions_dropped", "derive"),
	'threads_destroyed': Stat("bad", "threads_destroyed", "derive"),
	'thread_queue_len': Stat("bad", "length_of_session_queue", "gauge"),
	'esi_warnings': Stat("bad", "esi_parse_warnings", "derive"),
	'esi_errors': Stat("bad", "esi_parse_errors_", "derive"),
	'n_object': Stat("objects", "number_of_objects", "gauge"),
	'n_expired': Stat("expunge", "number_of_expired objects", "derive"),
	'n_lru_nuked': Stat("expunge", "number_of_lru_nuked_objects", "derive"),
	'cache_hit': Stat("request_rate", "cache_hits", "derive"),
	'cache_hitpass': Stat("request_rate", "cache_hits_for_pass", "derive"),
	'cache_miss': Stat("request_rate", "cache_misses", "derive"),
	'backend_conn': Stat("request_rate", "backend_conn_success", "derive"),
	'backend_unhealthy': Stat("request_rate", "backend_conn_not_attempted", "derive"),
	'client_req': Stat("request_rate", "good_client_requests_received", "derive"),
	's_pass': Stat("request_rate", "total_passed_requests_seen", "derive"),
	's_pipe': Stat("request_rate", "total_pipe_sessions_seen", "derive"),
	'sess_conn': Stat("request_rate", "sessions_accepted", "derive"),
	'threads_failed': Stat("threads", "thread_creation_failed", "derive"),
	'threads_limited': Stat("threads", "threads_hit_max", "derive"),
	'threads': Stat("threads", "total_number_of_threads", "gauge"),
	'threads_created': Stat("threads", "threads_created", "derive"),
	'threads_destroyed': Stat("threads", "threads_destroyed", "derive"),
	's_resp_bodybytes': Stat("transfer_rates", "body_traffic", "derive"),
	's_resp_hdrbytes': Stat("transfer_rates", "header_traffic", "derive"),
	'uptime': Stat("uptime", "varnish_uptime", "gauge"),
	'bans_dups': Stat("vcl_and_bans", "n_duplicate_bans_removed", "derive"),
	'bans_added': Stat("vcl_and_bans", "n_new_bans_added", "derive"),
	'n_backend': Stat("vcl_and_bans", "n_backends", "gauge"),
	'n_vcl': Stat("vcl_and_bans", "n_vcl_total", "derive"),
	'bans': Stat("vcl_and_bans", "n_total_active bans", "gauge"),
	'bans_deleted': Stat("vcl_and_bans", "n_old_bans_deleted", "derive"),
	'bans_tested': Stat("vcl_and_bans", "n_objects_tested", "derive"),
	'n_vcl_discard': Stat("vcl_and_bans", "n_vcl_discarded", "derive"),
	'n_vcl_avail': Stat("vcl_and_bans", "n_vcl_available", "derive")
}

def get_xml_stats():
    process = Popen([VARNISH_CONFIG['Varnishstat'], '-x'], stdout=PIPE, stderr=PIPE, env={'LANG':'C'})
    stdout, stderr = process.communicate()
    if stderr:
        log_verbose('Error executing %s (error: %s)' % (VARNISH_CONFIG['Varnishstat'], stderr))
        return {}

    DOMTree = xml.dom.minidom.parseString(stdout)
    collection = DOMTree.documentElement
    itemlist = collection.getElementsByTagName('stat')

    return itemlist

def choose_varnish():
    if VARNISH_CONFIG['Varnishver'] == '4':
        result = STATS_V4
    elif VARNISH_CONFIG['Varnishver'] == '3':
        result = STATS_V3
    else:
        result = STATS_V4
        log_verbose("Varnish version missmatch , fallback to 4")

    return result

def log_verbose(msg):
  if VARNISH_CONFIG['Verbose'] == False:
    return
  collectd.info('varnish plugin: %s' % msg)

def dispatch_value(prefix, metric, value, type, type_instance=None):

  log_verbose('Sending value: %s/%s=%s' % (prefix, metric, value))
  if not value:
    return
  value = int(value) # safety check

  val               = collectd.Values(plugin='varnish_cache', plugin_instance=prefix)
  val.type          = type
  val.type_instance = metric
  val.values        = [value]
  val.dispatch()

def configure_callback(conf):
  global VARNISH_CONFIG
  for node in conf.children:
    if node.key in VARNISH_CONFIG:
      VARNISH_CONFIG[node.key] = node.values[0]

  VARNISH_CONFIG['Verbose'] = bool(VARNISH_CONFIG['Verbose'])

def read_callback():
    itemlist = get_xml_stats()

    STATS = choose_varnish()

    for s in itemlist:
        v_metric = s.getElementsByTagName('name')[0].firstChild.data
        value = s.getElementsByTagName('value')[0].firstChild.data
        try:
            metric = STATS[v_metric].name
            prefix = 'default-%s' % STATS[v_metric].graph
            ds_type = STATS[v_metric].type
            log_verbose('prefix : %s metric : %s value : %s' % ( prefix, metric, value))
            dispatch_value(prefix, metric, value, ds_type)

        except KeyError:
            pass


collectd.register_read(read_callback)
collectd.register_config(configure_callback)
