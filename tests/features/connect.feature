@connect.feature
Feature: the client connects to the server

For this feature we don't care what the client sends. This feature only tests that
the client sends some payload to the right port at the right address.

Scenario Outline: The client connects to localhost at the default port
    Given a <ipversion> mock server is listening at localhost
    And the client is started with arguments "<args>"

    Then the client sends a packet to the server

    Examples:
    | ipversion | args           |
    | ipv4      | localhost file |
    | ipv4      | 127.0.0.1 file |
    | ipv6      | ::1 file       |

Scenario Outline: The client connects to the specified port
    Given a <ipversion> mock server is listening at localhost on port <port>
    And the client is started with arguments "<args>"

    Then the client sends a packet to the server

    Examples:
    | ipversion | args                    | port  |
    | ipv4      | 127.0.0.1 -p 33333 file | 33333 |
    | ipv6      | --port 12345 ::1 file   | 12345 |

Scenario Outline: The client connects to IP addresses other than localhost
    Given the interface has a route to address <address>
    And a <ipversion> mock server is listening at <address>
    And the client is started with arguments "<args>"

    Then the client sends a packet to the server

    Examples:
    | ipversion | args              | address      |
    | ipv4      | 192.168.42.1 file | 192.168.42.1 |
    | ipv6      | de51::ee file     | de51::ee     |