import pytest
import requests

import srv_hijacker

CONSUL_HOST = "127.0.0.1"
CONSUL_DNS_PORT = "8600"
CONSUL_API_PORT = "8500"
CONSUL_API_URL = f"{CONSUL_HOST}:{CONSUL_API_PORT}"


def test_hijack(consul_http_service_url):
    def test_http(url):
        response = requests.get(url)
        assert response.status_code == 200

    def test_http_direct():
        test_http("https://httpbin.org/get")

    def test_http_hijacked():
        test_http(consul_http_service_url)

    # Before 'hijack' is run, direct requests must pass
    test_http_direct()

    # Before 'hijack' is run, hijacked requests must fail
    with pytest.raises(requests.exceptions.ConnectionError):
        test_http_hijacked()

    srv_hijacker.hijack(
        host_regex=r"service.consul$",
        srv_dns_host=CONSUL_HOST,
        srv_dns_port=CONSUL_DNS_PORT,
    )

    # Now that the monkey patching is done, both should succeed
    test_http_direct()
    test_http_hijacked()

    # Patching again shouldn't cause issues
    srv_hijacker.hijack(
        host_regex=r"service.consul$",
        srv_dns_host=CONSUL_HOST,
        srv_dns_port=CONSUL_DNS_PORT,
    )

    test_http_direct()
    test_http_hijacked()


@pytest.fixture
def consul_http_service_url():
    # Let's register a service named 'test'  to point back to consul itself
    register_service_on_consul("test-http", CONSUL_HOST, CONSUL_API_PORT)

    # We can now use a consul endpoint itself for testing.
    return "http://test-http.service.consul/v1/agent/services"


def register_service_on_consul(service_name, service_host, service_port):
    url = f"http://{CONSUL_API_URL}/v1/agent/service/register"
    response = requests.put(
        url,
        json={"Name": service_name, "Address": service_host, "Port": int(service_port)},
    )

    assert response.status_code == 200
