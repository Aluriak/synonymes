"""Tries to identify different meanings for a given word.
"""

import sys
import itertools
from itertools import islice
from main import load_graph, complete_graph, canonized
from pprint import pprint

g = load_graph()
complete_graph(g)
word = canonized((input('word to look at> ') if len(sys.argv) < 2 else sys.argv[1]).replace(' ', ''))

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
print(f"{len(empty_syns)} synonyms of {word} are trivial.")
print(f"{len(useful_syns)} synonyms of {word} will be used.")

import networkx as nx

syngraph = nx.Graph()
with open(f'syngraph-{word}.lp', 'w') as fd:
    for syn in useful_syns:
        for neighbor in {w for w in g[syn] if w in useful_syns}:
            if neighbor != word:
                syngraph.add_edge(syn, neighbor)
                fd.write(f'edge("{syn}","{neighbor}").\n')
    print(f'syngraph-{word}.lp written!')
print('Connected components of syngraph:')
for idx, cc in enumerate(nx.connected_components(syngraph), start=1):
    print(f"CC {idx:02d}: {len(cc)} elements, including {next(iter(cc))}")


def density(nodes) -> float:
    return nx.density(syngraph.subgraph(nodes))

print("Let's try to find meanings…")
def merge_meanings(meanings: set[frozenset[str]], threshold:float=0.5):
    change = True
    merges = 0
    total = 0
    while change:
        change = False
        # find meanings sharing at least threshold of density
        for idx, (mea, meb) in enumerate(itertools.combinations(meanings, r=2)):
            total += 1
            both = mea | meb
            d = density(both)
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

def show_meanings_at(meanings, threshold, sample_size: int = 5):
    merge_meanings(meanings, threshold)
    print(f"Final {len(meanings)} meanings for {threshold=}:")
    imeanings = dict(enumerate(meanings, start=1))
    for idx, meaning in enumerate(meanings, start=1):
        all_other_words = set(itertools.chain.from_iterable(words for words in meanings if words != meaning))
        specifics = meaning - all_other_words
        sample = set(islice(specifics, 0, sample_size))
        try:
            while len(sample) < sample_size:
                sample.add(next(w for w in meaning if w not in sample))
        except StopIteration:
            pass
        print(f"{idx:8d} {', '.join(sample)} and {max(0, len(meaning)-sample_size) or 'no'} others")
    print()

meanings = set(map(frozenset, nx.find_cliques(syngraph)))
show_meanings_at(meanings, threshold=0.5)
show_meanings_at(meanings, threshold=0.45)
show_meanings_at(meanings, threshold=0.4)
show_meanings_at(meanings, threshold=0.3)



if False:
    import powergrasp as pg
    print(f'Calling powergrasp…')
    with open(f'syngraph-{word}.bbl', 'w') as fd:
        for line in pg.routines.compress_by_cc(f'syngraph-{word}.lp'):
            fd.write(line + '\n')
        print(f'syngraph-{word}.bbl written!')
