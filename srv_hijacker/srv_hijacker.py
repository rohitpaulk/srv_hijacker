import re

import socket
from socket import gaierror as SocketError

import dns
from dns import resolver

import logging

logger = logging.getLogger("srv_hijacker")


def resolve_ip(rrsets, old_host):
    for rrset in rrsets:
        if rrset.rdtype == dns.rdatatype.A:
            # TODO: Is it safe to assume that **any** A record in the
            # response is valid? Should we be matching against name?
            return rrset.items[0].address

    raise SocketError(f"Couldn't find A record for {old_host}")


def resolve_srv_record(old_host, srv_resolver):
    ans = srv_resolver.query(old_host, "SRV")

    new_port = ans[0].port
    new_host = resolve_ip(ans.response.additional, old_host)

    logger.debug(
        "Resolved SRV record for host %s: (%s:%s)", old_host, new_host, new_port
    )

    return new_host, new_port


original_socket_getaddrinfo = socket.getaddrinfo


def patched_socket_getaddrinfo(host_regex, srv_resolver):
    """
    Returns a function that behaves like `socket.getaddrinfo`.

    host_regex:

    The regex to match a host against. If this regex matches the host
    we hit srv_resolver to fetch the new host + port
    """

    def patched_f(host, port, family=0, type=0, proto=0, flags=0):
        if re.search(host_regex, host):
            logger.debug("TCP host %s matched SRV regex, resolving", host)
            host, port = resolve_srv_record(host, srv_resolver)
        else:
            logger.debug("TCP host %s did not match SRV regex, ignoring", host)

        return original_socket_getaddrinfo(host, port, family, type, proto, flags)

    return patched_f


def hijack(host_regex, srv_dns_host=None, srv_dns_port=None):
    """
    Usage:

    ```
    srv_hijacker.hijack(
        host_regex=r'service.consul$',
        srv_dns_host='127.0.0.1',
        srv_dns_port=8600
    )
    ```
    """
    srv_resolver = resolver.Resolver()
    if srv_dns_host:
        srv_resolver.nameservers = [srv_dns_host]
    if srv_dns_port:
        srv_resolver.port = int(srv_dns_port)

    socket.getaddrinfo = patched_socket_getaddrinfo(host_regex, srv_resolver)
