from setuptools import setup
from setuptools import find_packages

setup(
    name="srv_hijacker",
    version="0.0.8",
    description="Patch urllib3 to query a certain DNS server for SRV records",
    url="https://github.com/rohitpaulk/srv_hijacker",
    author="Paul Kuruvilla",
    author_email="paul.kuruvilla@shuttl.com",
    license="MIT",
    packages=find_packages(),
    classifiers=["Programming Language :: Python :: 3.7"],
    install_requires=["dnspython"],
)
