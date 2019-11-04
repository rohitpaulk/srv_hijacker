import srv_hijacker
import requests
import pytest
from uuid import uuid4
import socket

CONSUL_HOST = "127.0.0.1"
CONSUL_DNS_PORT = "8600"
CONSUL_API_PORT = "8500"
CONSUL_API_URL = f"{CONSUL_HOST}:{CONSUL_API_PORT}"


def test_hijack(consul_test_service_url):
    # Before 'hijack' is run, this request must fail
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get(consul_test_service_url)

    srv_hijacker.hijack(
        host_regex=r'service.consul$',
        srv_dns_host="127.0.0.1",
        srv_dns_port="8600")

    # Now that the monkey patching is done, this should succeed
    response = requests.get(consul_test_service_url)
    assert response.status_code == 200

    # Making sure a normal requests passes even after the patch is done
    response = requests.get("https://httpbin.org/get")
    assert response.status_code == 200

    # Patching again shouldn't cause issues
    srv_hijacker.hijack(
        host_regex=r'service.consul$',
        srv_dns_host="127.0.0.1",
        srv_dns_port="8600")

    response = requests.get(consul_test_service_url)
    assert response.status_code == 200
    response = requests.get("https://httpbin.org/get")
    assert response.status_code == 200

def test_hijack_tcp(consul_test_service_tcp):
    # Attempting to resolve without patching must
    # raise an error
    with pytest.raises(socket.gaierror):
        socket.getaddrinfo(consul_test_service_tcp, 0)

    # patch socket module and try again
    srv_hijacker.hijack_tcp(
        host_regex=r'service.consul$',
        srv_dns_host="127.0.0.1",
        srv_dns_port="8600"
    )

    # This time we should successfully resolve the adderess
    # of tcpbin.org info service
    res = socket.getaddrinfo(consul_test_service_tcp, 0, socket.AF_INET, socket.SOCK_STREAM)
    
    assert len(res) == 1
    
    addr = res[0][4]
    assert addr[0] == "52.20.16.20"
    assert addr[1] == 30001

    # Patching again shouldn't cause any problem
    srv_hijacker.hijack_tcp(
        host_regex=r'service.consul$',
        srv_dns_host="127.0.0.1",
        srv_dns_port="8600"
    )

    # This time we should successfully resolve the adderess
    # of tcpbin.org info service
    res = socket.getaddrinfo(consul_test_service_tcp, 0, socket.AF_INET, socket.SOCK_STREAM)
    
    assert len(res) == 1
    
    addr = res[0][4]
    assert addr[0] == "52.20.16.20"
    assert addr[1] == 30001


@pytest.fixture
def consul_test_service_url():
    # Let's register a service named 'test'  to point back to consul itself
    register_service_on_consul("test", CONSUL_HOST, CONSUL_API_PORT)

    # We can now use a consul endpoint itself for testing.
    return "http://test.service.consul/v1/agent/services"


def register_service_on_consul(service_name, service_host, service_port):
    url = f"http://{CONSUL_API_URL}/v1/agent/service/register"
    response = requests.put(
        url,
        json={
            "Name": service_name,
            "Address": service_host,
            "Port": int(service_port)
        })

    assert response.status_code == 200

@pytest.fixture
def consul_test_service_tcp():
    """
    Register a service that resolves to tcpbin.org with
    well known address 52.20.16.20:40001
    """
    register_service_on_consul("test-tcp", "52.20.16.20", 30001)
    return "test-tcp.service.consul"
