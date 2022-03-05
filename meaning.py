"""Tries to identify different meanings for a given word.
"""

import sys
import itertools
import networkx as nx
from itertools import islice
from collect import load_graph, complete_graph, canonized
from pprint import pprint

from cli import run_func_from_cli


def get_graph(datafile, word: str) -> (dict, set, set):
    g = load_graph(datafile)
    complete_graph(g)

    if word not in g:
        print(f"unknown word {word}. Abord.")
        exit()

    syns = set(g[word]) - {word}

    empty_syns, useful_syns = set(), set()
    for syn in syns:
        if syn not in g or len(g[syn]) == 1:
            assert next(iter(g[syn])) == word, (syn, g[syn])
            empty_syns.add(syn)
        else:
            useful_syns.add(syn)
    return g, empty_syns, useful_syns


def get_nxgraph(target: str, graph: dict, word: str, useful_syns: set) -> nx.Graph:
    syngraph = nx.Graph()
    fname = f'out/syngraph-{target}-{word}.lp'
    with open(fname, 'w') as fd:
        for syn in useful_syns:
            for neighbor in {w for w in graph[syn] if w in useful_syns}:
                if neighbor != word:
                    syngraph.add_edge(syn, neighbor)
                    fd.write(f'edge("{syn}","{neighbor}").\n')
        print(f'{fname} written!')
    print('Connected components of syngraph:')
    for idx, cc in enumerate(nx.connected_components(syngraph), start=1):
        print(f"CC {idx:02d}: {len(cc)} elements, including {next(iter(cc))}")
    return syngraph


def merge_meanings(syngraph: nx.Graph, meanings: set[frozenset[str]], threshold:float=0.5):
    change = True
    merges = 0
    total = 0
    while change:
        change = False
        # find meanings sharing at least threshold of density
        for idx, (mea, meb) in enumerate(itertools.combinations(meanings, r=2)):
            total += 1
            both = mea | meb
            d = nx.density(syngraph.subgraph(both))
            print(f'\r{idx:8d} {len(meanings)=} {len(mea)=}, {len(meb)=}, {d=}', end='', flush=True)
            if d > threshold or mea >= meb or meb > mea:
                # print(mea, meb, density(mea | meb))
                meanings.add(both)
                meanings.remove(mea)
                meanings.remove(meb)
                merges += 1
                change = True
                break
    print(f"\n{merges} merges for a total of {total} iterations")
    return meanings


def show_meanings_at(syngraph: nx.Graph, meanings: set, threshold, sample_size: int = 5):
    merge_meanings(syngraph, meanings, threshold)
    print(f"Final {len(meanings)} meanings for {threshold=}:")
    for idx, meaning in enumerate(meanings, start=1):
        all_other_words = set(itertools.chain.from_iterable(words for words in meanings if words != meaning))
        assert isinstance(meaning, (frozenset, set)), meaning
        specifics = meaning - all_other_words
        sample = set(islice(specifics, 0, sample_size))
        try:
            while len(sample) < sample_size:
                sample.add(next(w for w in meaning if w not in sample))
        except StopIteration:
            pass
        print(f"{idx:8d} {', '.join(sample)} and {max(0, len(meaning)-sample_size) or 'no'} others")
    print()


def create_powergrasp():
    import powergrasp as pg
    print(f'Calling powergrasp…')
    with open(f'syngraph-{word}.bbl', 'w') as fd:
        for line in pg.routines.compress_by_cc(f'syngraph-{word}.lp'):
            fd.write(line + '\n')
        print(f'syngraph-{word}.bbl written!')


def run(target: str, source: str, datafile: str, word: str, threshold: float = 0.3):
    g, empty_syns, useful_syns = get_graph(datafile, word)
    print(f"{len(empty_syns)} synonyms of {word} are trivial.")
    print(f"{len(useful_syns)} synonyms of {word} will be used.")
    print("Let's try to find meanings…")
    nxgraph = get_nxgraph(target, g, word, useful_syns)

    meanings = set(map(frozenset, nx.find_cliques(nxgraph)))
    show_meanings_at(nxgraph, meanings, threshold=threshold)


if __name__ == '__main__':
    run_func_from_cli(run, word='rire', threshold=0.3)
    print('done')
