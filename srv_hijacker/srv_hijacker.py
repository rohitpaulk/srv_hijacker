# Python Imports
import os
from socket import error as SocketError, timeout as SocketTimeout

# 3rd Party Imports
from dns import resolver
from urllib3.connection import HTTPConnection
from urllib3.exceptions import (NewConnectionError, ConnectTimeoutError)
from urllib3.util import connection


def resolve_srv_record(host):
    consul_dns_ip_port = os.environ['CONSUL_DNS_IP_PORT']
    consul_dns_ip, consul_dns_port = consul_dns_ip_port.split(':')

    res = resolver.Resolver()

    res.port = int(consul_dns_port)
    res.nameservers = [consul_dns_ip]

    ans = res.query(host, 'SRV')

    return ans.response.additional[0].items[0].address, ans[0].port


def patched_new_conn(self):
    if self.host.endswith('.service.consul'):
        hostname, port = resolve_srv_record(self.host)
    else:
        hostname = self.host
        port = self.port

    extra_kw = {}

    if self.source_address:
        extra_kw['source_address'] = self.source_address

    if self.socket_options:
        extra_kw['socket_options'] = self.socket_options

    try:
        conn = connection.create_connection((hostname, port), self.timeout,
                                            **extra_kw)

    except SocketTimeout as e:
        raise ConnectTimeoutError(
            self, "Connection to %s timed out. (connect timeout=%s)" %
            (self.host, self.timeout))

    except SocketError as e:
        raise NewConnectionError(
            self, "Failed to establish a new connection: %s" % e)

    return conn


def infect(dns_host, dns_port):
    os.environ["CONSUL_DNS_IP_PORT"] = f"{dns_host}:{dns_port}"
    HTTPConnection._new_conn = patched_new_conn
