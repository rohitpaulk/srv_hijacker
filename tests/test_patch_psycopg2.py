import pytest
from .common import StatefulTest
from .common import CONSUL_HOST, CONSUL_DNS_PORT, register_service_on_consul

import srv_hijacker

try:
    import psycopg2
except ImportError:
    raise pytest.skip(
        "psycopg2 is not available, skipping test that patches psycopg2",
        allow_module_level=True,
    )

dsn = "postgresql://srvhijacker:secret@psycopg2.service.consul/srvhijacker"


class TestPatchPsycopg2(StatefulTest):
    def test_hijack_psycopg2(self, consul_pg_hostname):
        with pytest.raises(
            psycopg2.OperationalError,
            match='.*could not translate host name "psycopg2.service.consul" to address.*',
        ):
            psycopg2.connect(dsn)

        srv_hijacker.hijack(
            host_regex=r"service.consul$",
            srv_dns_host=CONSUL_HOST,
            srv_dns_port=CONSUL_DNS_PORT,
            libraries_to_patch=["psycopg2"],
        )

        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("select 1")
                result = cur.fetchone()
                assert (
                    result[0] == 1
                ), f"unexpected query result {result[0]}, expected 1"

    @pytest.fixture
    def consul_pg_hostname(self):
        register_service_on_consul("psycopg2", CONSUL_HOST, 5432)
        return "psycopg2.service.consul"
