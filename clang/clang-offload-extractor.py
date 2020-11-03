#!/usr/bin/env python3

# This tool extracts the device bundles from clang-offload-bundler. The clang
# tool (found in clang/tools/clang-offload-bundler) does not support any modes
# that extract or enumerate all of the device types contained in the bundle.

import argparse
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument("source", type=argparse.FileType("r+b"),
        help="The source file to extract from")
parser.add_argument("outdir", help="Directory to extract files to")
parser.add_argument("device", nargs="*", help="Device types to extract")
args = parser.parse_args()

# This is the magic string that indicates bundle information.
MAGIC_STR = "__CLANG_OFFLOAD_BUNDLE__"

def parse_text_file(fd, comment="#"):
    LINE_START = f"{comment} {MAGIC_STR}__START__".encode('us-ascii')
    LINE_END = f"{comment} {MAGIC_STR}__END__".encode('us-ascii')
    triple = None
    triples = dict()
    for line in fd:
        if line.startswith(LINE_START):
            assert triple is None
            triple = line[len(LINE_START):].strip().decode('us-ascii')
            cur_section = b""
        elif line.startswith(LINE_END):
            # Strip off the last "\n" in the code.
            triples[triple] = cur_section[:-1]
            check_triple = line[len(LINE_END):].strip().decode('us-ascii')
            assert triple == check_triple
            triple = None
        elif triple is not None:
            cur_section += line
    return triples

with args.source as input:
    triples = parse_text_file(args.source)

if not os.path.exists(args.outdir):
    os.mkdir(args.outdir)

json_metadata = {'devices': {}}
for triple, data in triples.items():
    outfile = os.path.join(args.outdir, triple + ".s")
    with open(outfile, 'w+b') as output:
        output.write(data)
    if triple.startswith('host-'):
        json_metadata['host'] = outfile
    else:
        json_metadata['devices'][triple] = outfile
print(json.dumps(json_metadata))
