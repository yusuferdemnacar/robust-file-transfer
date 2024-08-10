from testerng.fixtures import *
from pytest_bdd import scenarios, given, when, then
from pytest_bdd.parsers import parse
from testerng.toolbox import Process, LoopbackDevice
import pytest
from pathlib import Path
from socket import socket, AF_INET, AF_INET6, SOCK_DGRAM, IPPROTO_UDP
import logging

scenarios("features/arguments.feature")
scenarios("features/connect.feature")

DEFAULT_PORT = 32323

@pytest.fixture
def executable(pytestconfig):
    return Path(pytestconfig.getoption("--submission-path")).joinpath("rft")

################################### program launch and exit ############################

@given("the program is started without any arguments", target_fixture="process")
def launch_no_arguments(executable):
    process = Process([str(executable)])
    process.run()
    yield process
    process.kill()
    process.close()

@given(parse("the client is started with arguments \"{args}\""), target_fixture="client")
@given(parse("the program is started with arguments \"{args}\""), target_fixture="process")
def launch_with_args(executable: Path, args: str):
    process = Process([str(executable)] + args.split(" "))
    process.run()
    yield process
    process.kill()
    process.close()

@then("the program exits with exit code other than zero")
def assert_non_zero_exit(process: Process):
    exitcode = process.wait(timeout=1)
    if exitcode is None:
        pytest.fail("Expected process to exit, but process did not exit")
    if exitcode == 0:
        pytest.fail(f"Expected process to exit with non-zero exit code, but got {exitcode}")

#################################### basic networking ###############################

@pytest.fixture(autouse=True)
def iface():
    iface = LoopbackDevice()
    iface.up()
    return iface

@given(parse("the interface has a route to address {address}"))
def set_address_route(iface: LoopbackDevice, address: str):
    name = iface.name.decode()
    os.system(f"ip addr add {address} dev {name}")
    os.system(f"ip addr del ::1/128 dev {name}")
    os.system(f"ip addr del 127.0.0.1/8 dev {name}")
    os.system("ip address list")


def make_mock_server(ipversion: str, address: str, port: int):
    if ipversion == "ipv4":
        s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    elif ipversion == "ipv6":
        s = socket(AF_INET6, SOCK_DGRAM, IPPROTO_UDP)
    else:
        raise Exception("ipversion can only be set to \"ipv4\" or \"ipv6\"")
    s.settimeout(5)
    s.bind((address, port))
    return s

@given(parse("a {ipversion} mock server is listening at {address}"), target_fixture="mock_server")
def make_mock_server_localhost_default(ipversion: str, address: str):
    return make_mock_server(ipversion, address, DEFAULT_PORT)

@given(parse("a {ipversion} mock server is listening at {address} on port {port:d}"), target_fixture="mock_server")
def make_mock_server_address_port(ipversion: str, address: str, port: int):
    return make_mock_server(ipversion, address, port)

################################## basic assertions #################################

@then("the client sends a packet to the server")
def assert_client_sends_a_packet(mock_server: socket, iface: LoopbackDevice):
    try:
        data, addrinfo = mock_server.recvfrom(iface.MTU_SIZE)
    except TimeoutError:
        pytest.fail("expected to receive something from client, but got nothing (timed out)")
    if data is None or data == b'':
        pytest.fail(f"expected to receive something from client, but got {data}")
