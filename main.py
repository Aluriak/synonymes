

import json
import requests
import itertools
from bs4 import BeautifulSoup

DATAFILE = 'data.json'

def load_graph() -> dict:
    try:
        with open(DATAFILE) as fd:
            return json.loads(fd.read())
    except FileNotFoundError:
        return {}
def save_graph(graph: dict):
    with open(DATAFILE, 'w') as fd:
        graph = {word: sorted(list(graph[word])) for word in sorted(list(graph.keys()))}
        return json.dump(graph, fd, indent=4, ensure_ascii=False)

def get_words(word: str, graph: dict) -> list[str]:
    new = ()
    if word not in graph:
        ans = requests.get('http://www.synonymo.fr/synonyme/' + word)
        ans.encoding = 'utf8'
# ans.encoding = 'utf8'
        assert ans.encoding == 'utf8', ans.encoding
        soup = BeautifulSoup(ans.text, 'html.parser')
        h1s = tuple(elem for elem in soup.find_all('h1'))
        for h1 in h1s:
            if h1.text.startswith('Synonymes de'):
                assocs = set(elem.text for elem in h1.find_next_sibling().find_all(attrs={'class': 'word'}))
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

def enrich_graph(g: dict, force_user_prompt: bool=False):
    unexplored_words = set(itertools.chain.from_iterable(g.values())) - set(g.keys())
    if force_user_prompt or not unexplored_words:
        save_graph(g)
        print('No word to explore. Please provide one.')
        new_word = input('> ').strip().lower()
    else:  # select an unexplored word
        new_word = next(iter(unexplored_words))
    assocs, new_words = get_words(new_word, g)
    print('\r' + f"#new words={len(new_words): 3d}\t\t#unexplored={len(unexplored_words)}\t\t#def words={len(g)}  ({new_word})                ", end='', flush=True)


g = load_graph()
try:
    while True:
        enrich_graph(g)
except KeyboardInterrupt:  # start again, but with user prompt
    try:
        while True:
            enrich_graph(g, force_user_prompt=True)
    except:
        pass
except:  # don't do anything else
    pass
save_graph(g)
complete_graph(g)
stats(g)
print('done')
