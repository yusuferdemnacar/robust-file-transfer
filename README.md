# robust-file-transfer
Robust File Transfer protocol implementation with server and client examples.

The RFC-style specification can be found at [https://github.com/nStangl/robust-file-transfer/](https://github.com/nStangl/robust-file-transfer/).

## Installation

Clone the repository. The main script is also started by executing the `rft` file. Python installation is required, no additional packages are required to run the server/client implementation

## Arguments

* `--port`: specify the port to listen at / to connect to
* `--host`: specify the host to connect to (client)
* `--ipv6`: use ipv6 instead of ipv4 (client). The server can handle both ipv4 and ipv6 client if started in ipv6 mode.
* `--verbose`, `-v`: more debug output
* `--server`, `-s`: start in server mode instead of client mode
* `-p`: probability of entering packet loss burst
* `-q`: probability of leaving packet loss burst

Additionally, if started in client mode, the program is given a list of files to be transmitted.

## Tests

To run the tests, install the packages in requirements.txt.

Run the testcases from project root with the command `unshare --net --user --map-root-user -- pytest -rA` (Linux only).

