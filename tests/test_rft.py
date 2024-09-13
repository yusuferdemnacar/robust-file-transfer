import subprocess
from pathlib import Path
import os
import pytest
import hashlib
import time

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
    yield server_dir
    os.system(f"rm -rf {server_dir}")

@pytest.fixture
def client_dir(project_path: Path):
    client_dir = str(project_path.joinpath("client_dir"))
    os.system(f"mkdir {client_dir}")
    yield client_dir
    os.system(f"rm -rf {client_dir}")


def test_run(executable, server_dir, client_dir):
    server = subprocess.Popen([executable, "-s", "--port", "12346"], cwd=server_dir)

    client = subprocess.Popen([executable, "--host", "localhost", "--port", "12346", "LICENSE"], cwd=client_dir)
    
    exitcode = client.wait(timeout=5)

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