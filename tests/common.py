import importlib
import requests
import socket

CONSUL_HOST = "127.0.0.1"
CONSUL_DNS_PORT = "8600"
CONSUL_API_PORT = "8500"
CONSUL_API_URL = f"{CONSUL_HOST}:{CONSUL_API_PORT}"


def register_service_on_consul(service_name, service_host, service_port):
    url = f"http://{CONSUL_API_URL}/v1/agent/service/register"
    response = requests.put(
        url,
        json={"Name": service_name, "Address": service_host, "Port": int(service_port)},
    )

    assert response.status_code == 200


class StatefulTest(object):
    cleanup_fns = []

    @classmethod
    def get_mod_attr(cls, mod, name):
        try:
            module = importlib.import_module(mod)
        except ImportError:
            return None

        if hasattr(module, name):
            return getattr(module, name)

    @classmethod
    def set_mod_attr(cls, mod, name, val):
        try:
            module = importlib.import_module(mod)
        except ImportError:
            return None

        setattr(module, name, val)

    @classmethod
    def restore_on_cleanup(cls, mod, attr, val):
        def restore_attr():
            cls.set_mod_attr(mod, attr, val)

        cls.cleanup_fns.append(restore_attr)

    @classmethod
    def setup_class(cls):
        sock_getaddrinfo_fn = cls.get_mod_attr("socket", "getaddrinfo")
        psycopg2_connect_fn = cls.get_mod_attr("psycopg2", "connect")

        cls.restore_on_cleanup("socket", "getaddrinfo", sock_getaddrinfo_fn)
        cls.restore_on_cleanup("psycopg2", "connect", psycopg2_connect_fn)

    @classmethod
    def teardown_class(cls):
        [each() for each in cls.cleanup_fns]
