"""Get words synonyms from website"""

import json
import requests
import argparse
import itertools
from bs4 import BeautifulSoup

from cli import run_func_from_cli


def load_graph(datafile: str) -> dict:
    try:
        with open(datafile) as fd:
            return json.loads(fd.read())
    except FileNotFoundError:
        return {}


def save_graph(datafile: str, graph: dict):
    with open(datafile, 'w') as fd:
        graph = {word: sorted(list(graph[word])) for word in sorted(list(graph.keys()))}
        return json.dump(graph, fd, indent=4, ensure_ascii=False)


def canonized(word: str) -> str:
    word = word.lower()
    if word.startswith("s'"):
        word = word[2:]
    elif word.startswith("se "):
        word = word[3:]
    return word


def get_words(source: str, word: str, graph: dict) -> list[str]:
    new = ()
    word = canonized(word)
    if word not in graph:
        ans = requests.get(source.rstrip('/') + '/' + word)
        ans.encoding = 'utf8'
# ans.encoding = 'utf8'
        assert ans.encoding == 'utf8', ans.encoding
        soup = BeautifulSoup(ans.text, 'html.parser')
        h1s = tuple(elem for elem in soup.find_all('h1'))
        for h1 in h1s:
            if 'onymes de' in h1.text:
                assocs = set(canonized(elem.text) for elem in h1.find_next_sibling().find_all(attrs={'class': 'word'}))
                new = assocs - set(itertools.chain.from_iterable(graph.values()))
                graph[word] = list(assocs)
                break
        else:  # nothing found
            graph[word] = []
    return graph[word], new


def stats(g, new_def_words:set=set(), new_key_words:set=set()):
    def_words = set(itertools.chain.from_iterable(g.values()))
    key_words = set(g.keys())
    unex = def_words - key_words
    print()
    print(f"#key words: {len(key_words)} (+{len(new_key_words)}) (dont {next(iter(new_key_words), '…')})")
    print(f"#def words: {len(def_words)} (+{len(new_def_words)}) (dont {', '.join(itertools.islice(new_def_words, 0, 5)) or '…'})")
    print(f"unexplored: {len(unex)}")
    return unex


def complete_graph(graph: dict) -> dict:
    "Return the same graph, but where if K->C, then C->K"
    for word in graph.keys():
        for syn in graph[word]:
            if syn in graph and word not in graph[syn]:
                graph[syn].append(word)


def enrich_graph(source: str, datafile: str, g: dict, force_user_prompt: bool=False):
    unexplored_words = set(itertools.chain.from_iterable(g.values())) - set(g.keys())
    if force_user_prompt or not unexplored_words:
        save_graph(datafile, g)
        print('No word to explore. Please provide one.')
        new_word = canonized(input('> '))
    else:  # select an unexplored word
        new_word = next(iter(unexplored_words))
    assocs, new_words = get_words(source, new_word, g)
    print('\r' + f"#new words={len(new_words): 3d}\t\t#unexplored={len(unexplored_words)}\t\t#def words={len(g)}  ({new_word})                ", end='', flush=True)
    for word in new_words:
        assocs, new_words = get_words(source, word, g)
        print('\r' + f"#new words={len(new_words): 3d}\t\t#unexplored={len(unexplored_words)}\t\t#def words={len(g)}  ({new_word}:{word})                ", end='', flush=True)


def collect_everything_and_save(target: str, source: str, datafile: str, force_user_prompt: bool = False):
    g = load_graph(datafile)
    try:
        while True:
            enrich_graph(source, datafile, g)
    except KeyboardInterrupt:  # start again, but with user prompt
        try:
            while True:
                enrich_graph(source, datafile, g, force_user_prompt=force_user_prompt)
        except KeyboardInterrupt:
            pass
        except Exception as err:
            print('ERR', repr(err))
    except KeyboardInterrupt:
        pass
    except Exception as err:
        print('ERR', repr(err))
    save_graph(datafile, g)
    complete_graph(g)
    return g


if __name__ == '__main__':
    g = run_func_from_cli(collect_everything_and_save, force_user_prompt=True)
    stats(g)
    print('done')
