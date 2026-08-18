from __future__ import annotations

from endurance_agent_lab.utils.hashing import sha256_tree


def test_tree_hash_ignores_python_cache_artifacts(tmp_path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "source.md").write_text("stable\n", encoding="utf-8")
    before = sha256_tree(root)

    cache = root / "__pycache__"
    cache.mkdir()
    (cache / "module.cpython-313.pyc").write_bytes(b"transient")
    (root / ".DS_Store").write_bytes(b"transient")

    assert sha256_tree(root) == before
    (root / "source.md").write_text("changed\n", encoding="utf-8")
    assert sha256_tree(root) != before
