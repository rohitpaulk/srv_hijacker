import srv_hijacker
import requests
import pytest

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
