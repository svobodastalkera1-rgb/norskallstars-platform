"""Fail explicitly when asked to run an application check not implemented yet."""
import argparse
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('application', choices=('backend', 'web', 'android'))
args = parser.parse_args()
print(f'PENDING: {args.application} runtime/toolchain/checks are not implemented. '
      'Authorize the relevant phase, add real commands and dependencies, then activate the gate.',
      file=sys.stderr)
raise SystemExit(2)
