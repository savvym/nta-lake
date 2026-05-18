"""cache_key + canonical_config_hash 单元测试
（spec pipeline-orchestrator-mvp-20260518 T-7a，AC-3 / AC-7）。

5 用例：determinism / inputs order independence / config canonicalization /
canonical_config_hash_neq_cache_key（v2 防 regress）/ list-in-config 顺序敏感。
"""

from __future__ import annotations

from dataplat_api.runner.cache import (
    _canonical_config_hash,
    compute_cache_key,
)


def test_cache_key_determinism() -> None:
    k1 = compute_cache_key(["a", "b"], "p", "v", {"k": 1})
    k2 = compute_cache_key(["a", "b"], "p", "v", {"k": 1})
    assert k1 == k2
    assert len(k1) == 64  # sha256 hex


def test_cache_key_inputs_order_independence() -> None:
    k1 = compute_cache_key(["a", "b"], "p", "v", {"k": 1})
    k2 = compute_cache_key(["b", "a"], "p", "v", {"k": 1})
    assert k1 == k2


def test_cache_key_config_key_order_independence() -> None:
    k1 = compute_cache_key(["a"], "p", "v", {"k": 1, "j": 2})
    k2 = compute_cache_key(["a"], "p", "v", {"j": 2, "k": 1})
    assert k1 == k2


def test_canonical_config_hash_neq_cache_key() -> None:
    """v2 SHOULD 防 regress：禁止把 compute_cache_key 整体值当 config_hash。"""
    cfg = {"k": 1, "j": 2}
    cache_key = compute_cache_key(["a"], "p", "v", cfg)
    config_hash = _canonical_config_hash(cfg)
    assert cache_key != config_hash
    assert len(config_hash) == 64


def test_cache_key_list_in_config_order_sensitive() -> None:
    """list 顺序属业务语义，纳入 canonical（不 sort）。"""
    k1 = compute_cache_key(["a"], "p", "v", {"list": [1, 2, 3]})
    k2 = compute_cache_key(["a"], "p", "v", {"list": [3, 2, 1]})
    assert k1 != k2


def test_cache_key_processor_version_in_key() -> None:
    k1 = compute_cache_key(["a"], "p", "0.1", {})
    k2 = compute_cache_key(["a"], "p", "0.2", {})
    assert k1 != k2
