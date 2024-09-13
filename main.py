# main.py
from app import run_client, run_server

import argparse
import textwrap
import sys
import logging
import time
import pathlib

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
        '-v',
        '--verbose',
        action='store_true',
        help='increases the verbosity of the output'
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
        default=0,
        help="specifies the probability of transitioning from the success state to the failure state (default: 0)",
    )
    parser.add_argument(
        '-q',
        action='store',
        type=float,
        default=0,
        help="specifies the probability of transitioning from the failure state back to the failure state (default: 0)",
    )
    parser.add_argument(
        '--ipv6',
        action='store',
        type=bool,
        default=False,
        help="specifies if the program should use ipv6 (default: False)",
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

    if args.verbose:
        logging_level = logging.INFO
    else:
        logging_level = logging.WARNING

    logging.basicConfig(level=logging_level, format="[ %(levelname)s ] %(filename)s:%(funcName)s (%(lineno)d):\t\t %(message)s")

    if args.server:
        run_server(args.port, args.p, args.q, args.ipv6)
    else:
        start = time.time()
        run_client(args.host, args.port, args.file, args.p, args.q, args.ipv6)
        end = time.time()
        print("Time taken: " + str(end - start) + " seconds")
        # check which files were saved
        successful_files = []
        for file in args.file:
            if pathlib.Path(file).exists():
                successful_files.append(file)
        if len(successful_files) == 0:
            logging.error("No files were saved")
        else:
            print("Files saved:")
            file_size = sum([pathlib.Path(successful_file).stat().st_size for successful_file in successful_files])
            print(f"Total file size: {file_size}")
            print(f"Throughput: {file_size / ((end - start)*1e6)} MBs/sec")

if __name__ == "__main__":
    main()
