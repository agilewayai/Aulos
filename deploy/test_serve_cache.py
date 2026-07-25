"""Cache-control rules for the SPA static host."""

from serve import NO_CACHE, SHORT_CACHE, IMMUTABLE_ASSET, cache_control_for


def test_version_json_is_uncached() -> None:
    assert cache_control_for("/version.json") == NO_CACHE
    assert cache_control_for("/version.json?_=1") == NO_CACHE


def test_html_and_hashed_assets() -> None:
    assert cache_control_for("/index.html") == NO_CACHE
    assert cache_control_for("/assets/index-abc123.js") == IMMUTABLE_ASSET
    assert cache_control_for("/favicon.svg") == SHORT_CACHE
