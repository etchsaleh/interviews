"""Test-side helpers for the multi-part problems.

Copied next to the harness for every run, so test snippets can do
`from practice_helpers import ...`. Nothing here is meant to be called by solutions.
"""
import builtins
import contextlib
import io
import os
import random
from collections import defaultdict


# --------------------------------------------------------------------- cluster
def run_cluster(node_cls, tree, root="1", triggers=("count",), order="fifo", duplicate=0.0, seed=0):
    """Build a cluster of `node_cls` machines and deliver messages until it goes quiet.

    tree      : {parent_id: [child_ids...]}; ids missing as keys are leaves
    triggers  : messages delivered to the root from outside (fromNodeId=None), one at a
                time - each waits until the cluster has finished the previous one
    order     : "fifo", "lifo" or "random" message delivery
    duplicate : probability that a sent message is also delivered a second time
    Returns the lines printed by the cluster.
    """
    rng = random.Random(seed)
    parent_of = {c: p for p, kids in tree.items() for c in kids}
    ids = [root] + [c for kids in tree.values() for c in kids]
    queue = []

    def make_sender(sender):
        def send(to, message):
            if not isinstance(message, str):
                raise TypeError(f"messages must be strings, got {type(message).__name__}")
            if to != parent_of.get(sender) and to not in tree.get(sender, []):
                raise ValueError(f"node {sender} can't message {to}: only its parent and children")
            copies = 2 if rng.random() < duplicate else 1
            for _ in range(copies):
                if order == "random":
                    queue.insert(rng.randrange(len(queue) + 1), (sender, to, message))
                else:
                    queue.append((sender, to, message))
        return send

    nodes = {}
    for node_id in ids:
        node = node_cls(node_id, list(tree.get(node_id, [])), parent_of.get(node_id))
        node.sendAsyncMessage = make_sender(node_id)  # the provided API
        nodes[node_id] = node

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        for trigger in triggers:
            nodes[root].receiveMessage(None, trigger)
            steps = 0
            while queue:
                steps += 1
                if steps > 200_000:
                    raise RuntimeError("messages never stopped flowing (infinite loop?)")
                sender, to, message = queue.pop() if order == "lifo" else queue.pop(0)
                nodes[to].receiveMessage(sender, message)
    return [line for line in out.getvalue().splitlines() if line.strip()]


# ----------------------------------------------------------------- file trees
class Symlink:
    def __init__(self, target):
        self.target = target


def make_tree(root, files):
    """files: {"a.txt": "text" | b"bytes" | Symlink("target")}. Paths use "/"."""
    for rel, content in files.items():
        path = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(content, Symlink):
            os.symlink(content.target, path)
        else:
            data = content.encode() if isinstance(content, str) else content
            with open(path, "wb") as f:
                f.write(data)
    return root


def rel_groups(groups, root):
    """Normalise a list of duplicate groups to sorted, root-relative, "/"-separated paths."""
    base = os.path.abspath(root)
    norm = []
    for group in groups:
        rels = [os.path.relpath(os.path.abspath(os.fspath(p)), base).replace(os.sep, "/") for p in group]
        norm.append(sorted(rels))
    return sorted(norm)


class _CountingFile:
    """Wraps a file object and counts the bytes read through it."""

    def __init__(self, f, counter, key):
        self._f, self._counter, self._key = f, counter, key

    def _count(self, data):
        self._counter[self._key] += len(data) if data else 0
        return data

    def read(self, *a):
        return self._count(self._f.read(*a))

    def read1(self, *a):
        return self._count(self._f.read1(*a))

    def readline(self, *a):
        return self._count(self._f.readline(*a))

    def readinto(self, b):
        n = self._f.readinto(b)
        self._counter[self._key] += n or 0
        return n

    def __iter__(self):
        for line in self._f:
            yield self._count(line)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._f.close()

    def __getattr__(self, name):
        return getattr(self._f, name)


@contextlib.contextmanager
def track_file_reads(root):
    """Record which files under `root` get opened and how many bytes are read from each.

    Yields (opened, bytes_read): a set and a dict keyed by root-relative "/" paths.
    """
    base = os.path.abspath(root)
    opened, bytes_read = set(), defaultdict(int)
    real_open = builtins.open

    def tracking_open(file, mode="r", *args, **kwargs):
        f = real_open(file, mode, *args, **kwargs)
        if isinstance(file, int):
            return f
        rel = os.path.relpath(os.path.abspath(os.fspath(file)), base).replace(os.sep, "/")
        if rel.startswith(".."):
            return f
        opened.add(rel)
        return _CountingFile(f, bytes_read, rel)

    builtins.open = io.open = tracking_open
    try:
        yield opened, bytes_read
    finally:
        builtins.open = io.open = real_open
