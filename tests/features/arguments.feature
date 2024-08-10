@arguments.feature
Feature: Command Line Arguments

The rft program can be started in server or client mode, indicated by the -s argument:

Case 1: starting the program in server mode:
rft -s [-p <port>]

Case 2: starting the program in client mode:
rft [-p <port>] <host> <file1> [<file2> ...]

In case of the client, the host and one file are mandatory. Optionally, more files can be listed.

Arguments:
    <host>                  The host to connect to when started as client. Required in client mode.
    <file1> [<file2> ...]   The files to download when started as client. At least one file must be given.
                            Optionally, multiple files can be listed.

Supported options:
    -s, --server            Creates a rft server instead of a client.
    -p, --port              In server mode, specifies the port to listen on for incoming connections.
                            In client mode, specifies the port to connect to.
                            If no port is specified, 32323 is the default port.

Scenario: No arguments are passed to the rft program
    Given the program is started without any arguments
    Then the program exits with exit code other than zero

Scenario: The file argument is missing in client mode
    Given the program is started with arguments "localhost"
    Then the program exits with exit code other than zero

Scenario Outline: Too many arguments are provided in server mode
    Given the program is started with arguments "<args>"
    Then the program exits with exit code other than zero

    Examples:
    | args                 |
    | -s foo               |
    | -s foo bar           |
    | foo --server bar boo |

Scenario Outline: An unknown command line option is provided
    Given the program is started with arguments "<args>"
    Then the program exits with exit code other than zero

    Examples:
    | args           |
    | -k host file   |
    | -s -n          |
    | --boo --server |
