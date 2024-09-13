import subprocess
from pathlib import Path
import os
import pytest
import hashlib
import time
import unshare

@pytest.fixture(autouse=True)
def lo_up():
    unshare.unshare(unshare.CLONE_NEWNET)
    os.system("ip link set dev lo up")

@pytest.fixture
def project_path() -> Path:
    return Path(__file__).parent.parent

@pytest.fixture
def executable(project_path: Path) -> str:
    return str(project_path.joinpath("rft"))

@pytest.fixture
def server_dir(project_path: Path):
    server_dir = str(project_path.joinpath("server_dir"))
    os.system(f"mkdir {server_dir}")
    os.system(f"cp {str(project_path.joinpath('LICENSE'))} {server_dir}")
    time.sleep(0.5)
    yield server_dir
    os.system(f"rm -rf {server_dir}")

@pytest.fixture
def client_dir(project_path: Path):
    client_dir = str(project_path.joinpath("client_dir"))
    os.system(f"mkdir {client_dir}")
    yield client_dir
    os.system(f"rm -rf {client_dir}")


def test_send_small_file(executable, server_dir, client_dir):
    server = subprocess.Popen([executable, "-s", "--port", "12345", "--verbose"], cwd=server_dir)
    
    client = subprocess.Popen([executable, "--host", "localhost", "--port", "12345", "LICENSE", "--verbose"], cwd=client_dir)

    exitcode = client.wait(timeout=10)

    if not Path(client_dir).joinpath("LICENSE").exists():
        pytest.fail("Client did not receive LICENSE file")

    input = Path(server_dir).joinpath("LICENSE").read_bytes()
    output = Path(client_dir).joinpath("LICENSE").read_bytes()

    if input != output:
        pytest.fail("File that Client received is not equal to original file")

    if not exitcode == 0:
        pytest.fail(f"Expected exit code 0 but got exit code {exitcode}")

    server.kill()
    client.kill()


def test_file_does_not_exist(executable, server_dir, client_dir):
    server = subprocess.Popen([executable, "-s", "--port", "12346", "--verbose"], cwd=server_dir)
    
    client = subprocess.Popen([executable, "--host", "localhost", "--port", "12346", "LICENCE", "--verbose"], cwd=client_dir)

    exitcode = client.wait(timeout=20)

    if not exitcode == 0:
        pytest.fail(f"Expected exit code 0 but got exit code {exitcode}")

    if Path(client_dir).joinpath("LICENCE").exists():
        output = Path(client_dir).joinpath("LICENCE").read_bytes()
        if len(output) > 0:
            pytest.fail("Client created a LICENCE file even though it should not exist.")

    server.kill()
    client.kill()


def test_larger_file(executable, project_path, client_dir):
    server = subprocess.Popen([executable, "-s", "--port", "12347"], cwd=str(project_path))

    os.system("ls -la tests/")

    os.system(f"mkdir {client_dir}/tests")
    
    client = subprocess.Popen([executable, "--host", "localhost", "--port", "12347", "tests/eno8--2024-09-11--15-38-07.pcap"], cwd=client_dir)

    exitcode = client.wait(timeout=100)

    if not Path(client_dir).joinpath("tests/eno8--2024-09-11--15-38-07.pcap").exists():
        pytest.fail("Client did not receive pcap file")

    input = Path(project_path).joinpath("tests").joinpath("eno8--2024-09-11--15-38-07.pcap").read_bytes()
    output = Path(client_dir).joinpath("tests").joinpath("eno8--2024-09-11--15-38-07.pcap").read_bytes()

    if input != output:
        pytest.fail("File that Client received is not equal to original file")

    if not exitcode == 0:
        pytest.fail(f"Expected exit code 0 but got exit code {exitcode}")

    server.kill()
    client.kill()

def test_send_file_with_loss(executable, server_dir, client_dir):
    server = subprocess.Popen([executable, "-s", "--port", "12348", "--verbose", "-p", "0.1"], cwd=server_dir)
    
    client = subprocess.Popen([executable, "--host", "localhost", "--port", "12348", "LICENSE", "--verbose", "-p", "0.1"], cwd=client_dir)

    exitcode = client.wait(timeout=100)

    if not Path(client_dir).joinpath("LICENSE").exists():
        pytest.fail("Client did not receive LICENSE file")

    input = Path(server_dir).joinpath("LICENSE").read_bytes()
    output = Path(client_dir).joinpath("LICENSE").read_bytes()

    if input != output:
        pytest.fail("File that Client received is not equal to original file")

    if not exitcode == 0:
        pytest.fail(f"Expected exit code 0 but got exit code {exitcode}")

    server.kill()
    client.kill()
