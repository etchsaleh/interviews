"""Execute every Python example in PYTHON_REFERENCE.md.

Blocks with `>>>` are run as doctests (output must match exactly); other python blocks
must run without raising. All blocks share one namespace, top to bottom, like a session.
Usage: python tools/check_reference.py [path]
"""
import doctest
import re
import sys
from pathlib import Path


def main(path):
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    globs = {"__name__": "reference"}
    parser = doctest.DocTestParser()
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    failures = 0
    for i, block in enumerate(blocks, start=1):
        if ">>>" in block:
            test = parser.get_doctest(block, globs, f"block {i}", path, 0)
            result = runner.run(test, clear_globs=False)
            globs.update(test.globs)  # DocTest works on a copy; carry imports/names forward
            failures += result.failed
        else:
            try:
                exec(compile(block, f"block {i}", "exec"), globs)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"block {i} raised {exc!r}:\n{block}")
    print(f"{len(blocks)} blocks, {failures} failures")
    return failures


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1] if len(sys.argv) > 1 else "PYTHON_REFERENCE.md") else 0)
