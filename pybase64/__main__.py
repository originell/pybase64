import argparse
import base64
import os
import sys
from timeit import default_timer as timer

import pybase64


if sys.version_info < (3, 0):
    from pybase64._fallback import b64decode as b64decodeValidate
else:
    from base64 import b64decode as b64decodeValidate


def bench_one(data, enc, dec, altchars=None, validate=False):
    number = 0
    time = timer()
    while True:
        encodedcontent = enc(data, altchars=altchars)
        number += 1
        if timer() - time > 0.25:
            break
    iter = number
    time = timer()
    while iter > 0:
        encodedcontent = enc(data, altchars=altchars)
        iter -= 1
    time = timer() - time
    print('{0:<32s} {1:9.3f} MB/s ({2:,d} bytes -> {3:,d} bytes)'.format(
        enc.__module__ + '.' + enc.__name__ + ':',
        ((number * len(data)) / (1024.0 * 1024.0)) / time,
        len(data), len(encodedcontent)))
    number = 0
    time = timer()
    while True:
        decodedcontent = dec(encodedcontent,
                             altchars=altchars,
                             validate=validate)
        number += 1
        if timer() - time > 0.25:
            break
    iter = number
    time = timer()
    while iter > 0:
        decodedcontent = dec(encodedcontent,
                             altchars=altchars,
                             validate=validate)
        iter -= 1
    time = timer() - time
    print('{0:<32s} {1:9.3f} MB/s ({3:,d} bytes -> {2:,d} bytes)'.format(
        dec.__module__ + '.' + dec.__name__ + ':',
        ((number * len(data)) / (1024.0 * 1024.0)) / time,
        len(data), len(encodedcontent)))
    assert decodedcontent == data


def readall(file):
    # Python 3 does not honor the binary flag when using standard streams
    if sys.version_info > (3, 0):
        try:
            fileno = file.fileno()
            if fileno == sys.stdin.fileno():
                with os.fdopen(fileno, 'rb') as f:
                    return f.read()
        except:  # pragma: no cover
            # This is probably not stdin
            pass  # pragma: no cover
    return file.read()


def writeall(file, data):
    # Python 3 does not honor the binary flag when using standard streams
    if sys.version_info > (3, 0):
        try:
            fileno = file.fileno()
            if fileno == sys.stdout.fileno():
                with os.fdopen(fileno, 'wb') as f:
                    f.write(data)
                    return
        except:  # pragma: no cover
            # This is probably not stdout
            pass  # pragma: no cover
    file.write(data)


def benchmark(args):
    print(__package__ + ' ' + pybase64.get_version())
    data = readall(args.input)
    for altchars in [None, b'-_']:
        for validate in [False, True]:
            print('bench: altchars={0:s}, validate={1:s}'.format(
                  repr(altchars), repr(validate)))
            bench_one(data,
                      pybase64.b64encode,
                      pybase64.b64decode,
                      altchars,
                      validate)
            bench_one(data,
                      base64.b64encode,
                      b64decodeValidate,
                      altchars,
                      validate)


def encode(args):
    data = readall(args.input)
    data = pybase64.b64encode(data, args.altchars)
    writeall(args.output, data)


def decode(args):
    data = readall(args.input)
    data = pybase64.b64decode(data, args.altchars, args.validate)
    writeall(args.output, data)


class LicenseAction(argparse.Action):

    def __init__(self,
                 option_strings,
                 license=None,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help="show license information and exit"):
        super(LicenseAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
        self.license = license

    def __call__(self, parser, namespace, values, option_string=None):
        print(self.license)
        parser.exit()


def main(args=None):
    # main parser
    parser = argparse.ArgumentParser(
        prog=__package__,
        description=__package__ + ' command-line tool.')
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=__package__ + ' ' + pybase64.get_version())
    parser.add_argument(
        '--license',
        action=LicenseAction,
        license=pybase64.get_license_text())
    # create sub-parsers
    subparsers = parser.add_subparsers(help='tool help')
    # benchmark parser
    benchmark_parser = subparsers.add_parser('benchmark', help='-h for usage')
    benchmark_parser.add_argument(
        'input',
        type=argparse.FileType('rb'),
        help='input file used for the benchmark')
    benchmark_parser.set_defaults(func=benchmark)
    # encode parser
    encode_parser = subparsers.add_parser('encode', help='-h for usage')
    encode_parser.add_argument(
        'input',
        type=argparse.FileType('rb'),
        help='input file to be encoded')
    group = encode_parser.add_mutually_exclusive_group()
    group.add_argument(
        '-u', '--url',
        action='store_const',
        const=b'-_',
        dest='altchars',
        help='use URL encoding')
    group.add_argument(
        '-a', '--altchars',
        dest='altchars',
        help='use alternative characters for encoding')
    encode_parser.add_argument(
        '-o', '--output',
        dest='output',
        type=argparse.FileType('wb'),
        default=sys.stdout,
        help='encoded output file (default to stdout)')
    encode_parser.set_defaults(func=encode)
    # decode parser
    decode_parser = subparsers.add_parser('decode', help='-h for usage')
    decode_parser.add_argument(
        'input',
        type=argparse.FileType('rb'),
        help='input file to be decoded')
    group = decode_parser.add_mutually_exclusive_group()
    group.add_argument(
        '-u', '--url',
        action='store_const',
        const=b'-_',
        dest='altchars',
        help='use URL decoding')
    group.add_argument(
        '-a', '--altchars',
        dest='altchars',
        help='use alternative characters for decoding')
    decode_parser.add_argument(
        '-o', '--output',
        dest='output',
        type=argparse.FileType('wb'),
        default=sys.stdout,
        help='decoded output file (default to stdout)')
    decode_parser.add_argument(
        '--no-validation',
        dest='validate',
        action='store_false',
        help='disable validation of the input data')
    decode_parser.set_defaults(func=decode)
    # ready, parse
    if args is None:  # pragma: no branch
        args = sys.argv[1:]
    if len(args) == 0:  # pragma: no branch
        args = ['-h']  # pragma: no cover
    args = parser.parse_args(args=args)
    args.func(args)


if __name__ == "__main__":  # pragma: no branch
    main()
