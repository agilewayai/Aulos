"""Ambient playlist pack resolution."""

from pathlib import Path

from aulos_skills.ambient_playlist import load_playlist_pack, resolve_ambient_audio


def test_open_goldberg_playlist_resolves_32_tracks() -> None:
    root = Path(__file__).resolve().parents[1]
    corpus = root / "skills" / "aulos-listening-corpus" / "assets" / "corpus"
    pack = load_playlist_pack(corpus, "open-goldberg-ishizaka")
    assert pack.get("id") == "open-goldberg-ishizaka"
    ambient = resolve_ambient_audio({"playlist_id": "open-goldberg-ishizaka"}, corpus_dir=corpus)
    assert ambient["mode"] == "playlist"
    assert ambient["loop_playlist"] is True
    assert len(ambient["tracks"]) == 32
    assert ambient["tracks"][0]["title"] == "Aria"
    assert "Special:FilePath" in ambient["tracks"][0]["url"]
    assert ambient["tracks"][-1]["title"] == "Aria da capo"
    assert "/v1/media/audio" in ambient["tracks"][5]["cache_src"]
