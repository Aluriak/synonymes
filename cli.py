import argparse


TARGETS = {
    'synonyme': ('http://www.synonymo.fr/synonyme/', 'data/synonymes.json'),
    'antonyme': ('http://www.antonyme.org/antonyme/', 'data/antonymes.json'),
}


def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('target', choices=tuple(TARGETS), help='data to scrap', default=tuple(TARGETS)[0])
    return parser.parse_args()


def run_func_from_cli(func, *args, **kwargs):
    "Run given func with source and datafile associated with CLI, plus given args"
    cli_args = parse_cli()
    source, datafile = TARGETS[cli_args.target]
    return func(cli_args.target, source, datafile, *args, **kwargs)
