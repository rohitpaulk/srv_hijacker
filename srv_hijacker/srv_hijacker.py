import os
import re

from socket import error as SocketError, timeout as SocketTimeout

from urllib3.connection import HTTPConnection
from urllib3.exceptions import (NewConnectionError, ConnectTimeoutError)
from urllib3.util import connection

from dns import resolver


def resolve_srv_record(host, dns_ip, dns_port):
    res = resolver.Resolver()

    res.port = int(dns_port)
    res.nameservers = [dns_ip]

    ans = res.query(host, 'SRV')

    return ans.response.additional[0].items[0].address, ans[0].port


def patched_new_conn(url_regex, srv_dns_host, srv_dns_port):
    """
    Returns a function that does pretty much what
    `urllib3.connection.HTTPConnection._new_conn` does.

    url_regex:

    The regex to match a host against. If this regex matches the host, we
    hit the srv_dns_host to fetch the new host + port

    srv_dns_host, srv_dns_port:

    host and port for the dns server. Example: "127.0.0.1", "8600"
    """

    def new_host_and_port(old_host, old_port):
        if re.search(url_regex, old_host):
            host, port = resolve_srv_record(old_host, srv_dns_host,
                                            srv_dns_port)
        else:
            host = old_host
            port = old_port

        return host, port

    def f(self):
        hostname, port = new_host_and_port(self.host, self.port)

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

    return f


def infect(host_regex, srv_dns_host, srv_dns_port):
    HTTPConnection._new_conn = patched_new_conn(host_regex, srv_dns_host,
                                                srv_dns_port)
