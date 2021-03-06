"""From an input word, explore the word graph.

Generate a dataframe

"""

import os
import sys
import itertools
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, Iterable, Optional
from collect import load_graph, complete_graph, canonized
from collections import defaultdict

import seaborn as sns

from cli import run_func_from_cli


def get_dataframe(datafile: str, word: str = None) -> pd.DataFrame:
    g = load_graph(datafile)
    complete_graph(g)
    word = word or canonized((input('word to look at> ') if len(sys.argv) < 2 else sys.argv[1]).replace(' ', ''))

    df = defaultdict(list)
    unexplored = {word}  # set of all unexplored words
    walked = set()  # set of all walked words
    idx = 0
    while unexplored:
        idx += 1
        word = unexplored.pop()
        walked.add(word)
        syns = set(g[word])
        unexplored |= syns - walked
        df['unexplored'].append(len(unexplored))
        df['walked'].append(len(walked))
        df['index'].append(idx)
    return pd.DataFrame(df)


def plot(target: str, word: str, df: pd.DataFrame, show_plot: bool = False, plot_size: Tuple[int, int] = (10, 5)) -> Iterable[str]:
    print(df)

    def savefig(obj, name, x, y):
        fname = f"out/mpl-{target}-{word}-{name}-{x}-{y}.png"
        obj.savefig(fname, dpi=400)
        print(f"File {fname} written!")
        if show_plot:
            plt.show()

    if sns is not None:  # seaborn is available, let's draw!

        sns.set(rc={"figure.figsize": plot_size})  # NB: doesn't seems to work in python 3.7
        plt.rcParams["figure.figsize"] = plot_size
        plt.rcParams["xtick.labelsize"] = 5

        # line plot
        plt.figure()
        plot = sns.lineplot(x='index', y='unexplored', data=df)
        plot.set_title('unexplored words')
        plot.set_xlabel('steps')
        plot.set_ylabel('number of unexplored words')
        savefig(plt, "line", 'time', 'unexplored')



def run(target: str, source: str, datafile: str, word: str):
    return plot(target, word, get_dataframe(datafile, word))


if __name__ == '__main__':
    g = run_func_from_cli(run, 'rire')
    print('done')
