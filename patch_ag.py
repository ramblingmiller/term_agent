import argparse
import sys

def test_parse():
    parser = argparse.ArgumentParser(
        description="Vault 3000 - Linux Terminal AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage:
  term_ag.py                    # Run locally, interactive
  term_ag.py <goal>             # Run locally, execute goal directly
  term_ag.py <remote>           # Run remotely via SSH, interactive
  term_ag.py <remote> <goal>    # Run remotely, execute goal directly
  term_ag.py -p, --prompt       # Run Prompt Creator sub-agent
  term_ag.py --help             # Show this help message
        """
    )
    parser.add_argument('positionals', nargs='*', help='Remote host (user@host) and/or direct goal')
    args = parser.parse_args(sys.argv[1:])
    print(args)

if __name__ == '__main__':
    test_parse()
