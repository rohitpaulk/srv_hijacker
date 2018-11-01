# srv_hijacker

A python module that patches [`urllib3`](https://urllib3.readthedocs.io/en/latest/)
to query a certain DNS server for SRV records when creating connections.

### Usage

This module exposes exactly one function:

```python
import srv_hijacker

srv_hijacker.hijack(
    host_regex=r'service.consul$',
    srv_dns_host='127.0.0.1',
    srv_dns_port=8600
)
```

Note: Only connections that match the `host_regex` are patched. All other
connections are the same as before.

### Compatibility

Only confirmed to work with Python 3.7. Tests use `requests`, which uses
`urllib3` internally.

### Background

The use case this was designed for is to transparently patch `requests` so that
calls to endpoints like `your_service.service.consul` hit consul's DNS server
and use the host + port given in the SRV query.

