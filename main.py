# main.py
from app import run_client, run_server

import argparse
import textwrap
import sys
import logging

def main():
    parser = argparse.ArgumentParser(
        prog='rft',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
        '''
            The rft program can be started in server or client mode, indicated by the -s argument:

            Case 1: starting the program in server mode:
            rft -s [-p <port>]

            Case 2: starting the program in client mode:
            rft [-p <port>] <host> <file1> [<file2> ...]

            In case of the client, the host and one file are mandatory. Optionally, more files can be listed.
        '''),
        
    )

    parser.add_argument(
        '-s',
        '--server',
        action='store_true',
        default=False,
        help='creates a rft server instead of a client'
    )
    parser.add_argument(
        '--host',
        action='store',
        type=str,
        help="specifies the host to connect to (default: localhost)",
    )
    parser.add_argument(
        '--port',
        action='store',
        type=int,
        default=32323,
        help="specifies the port to listen at or connect to (default: 32323)",
    )
    parser.add_argument(
        '-p',
        action='store',
        type=float,
        default=0.5,
        help="specifies the probability of transitioning from the success state to the failure state (default: 0.5)",
    )
    parser.add_argument(
        '-q',
        action='store',
        type=float,
        default=0.5,
        help="specifies the probability of transitioning from the failure state back to the failure state (default: 0.5)",
    )
    parser.add_argument(
        'file',
        type=str,
        nargs='*'
    )

    args = parser.parse_args()

    if args.server and (args.host or len(args.file) > 0):
        sys.exit("host and/or file name(s) can only be specified in client mode")
    
    if not args.server and (not args.host or len(args.file) == 0):
        sys.exit("in client mode the host and at least one filename must be specified")

    if not 0 <= args.p <= 1 or not 0 <= args.q <= 1:
        sys.exit("p and q probabilities must be between 0 and 1")

    logging.basicConfig(level=logging.INFO, format="[ %(levelname)s ] %(filename)s: %(message)s")

    if args.server:
        run_server(args.port, args.p, args.q)
    else:
        run_client(args.host, args.port, args.file, args.p, args.q)

if __name__ == "__main__":
    main()
