"""Famous composers used as crawl entry points (allowlisted Wikidata QIDs).

Only CC0 Wikidata + ODbL MusicBrainz + internal catalog — no arbitrary scrapes.
"""

from __future__ import annotations

# Stable Wikidata QIDs (verified common knowledge / EntityData API)
FAMOUS_COMPOSERS: list[dict[str, str]] = [
    {
        "composer_id": "johann-sebastian-bach",
        "name_en": "Johann Sebastian Bach",
        "wikidata_qid": "Q1339",
        "musicbrainz_query": "artist:\"Johann Sebastian Bach\" AND type:person",
        "work_query": "artist:\"Johann Sebastian Bach\" AND work:\"Goldberg\"",
    },
    {
        "composer_id": "wolfgang-amadeus-mozart",
        "name_en": "Wolfgang Amadeus Mozart",
        "wikidata_qid": "Q254",
        "musicbrainz_query": "artist:\"Wolfgang Amadeus Mozart\" AND type:person",
        "work_query": "artist:\"Wolfgang Amadeus Mozart\" AND work:\"Requiem\"",
    },
    {
        "composer_id": "ludwig-van-beethoven",
        "name_en": "Ludwig van Beethoven",
        "wikidata_qid": "Q255",
        "musicbrainz_query": "artist:\"Ludwig van Beethoven\" AND type:person",
        "work_query": "artist:\"Ludwig van Beethoven\" AND work:\"Symphony No. 9\"",
    },
    {
        "composer_id": "frederic-chopin",
        "name_en": "Frédéric Chopin",
        "wikidata_qid": "Q1268",
        "musicbrainz_query": "artist:\"Frédéric Chopin\" AND type:person",
        "work_query": "artist:\"Frédéric Chopin\" AND work:\"Nocturne\"",
    },
    {
        "composer_id": "franz-schubert",
        "name_en": "Franz Schubert",
        "wikidata_qid": "Q7312",
        "musicbrainz_query": "artist:\"Franz Schubert\" AND type:person",
        "work_query": "artist:\"Franz Schubert\" AND work:\"Winterreise\"",
    },
    {
        "composer_id": "johannes-brahms",
        "name_en": "Johannes Brahms",
        "wikidata_qid": "Q7294",
        "musicbrainz_query": "artist:\"Johannes Brahms\" AND type:person",
        "work_query": "artist:\"Johannes Brahms\" AND work:\"Symphony No. 1\"",
    },
    {
        "composer_id": "pyotr-ilyich-tchaikovsky",
        "name_en": "Pyotr Ilyich Tchaikovsky",
        "wikidata_qid": "Q7315",
        "musicbrainz_query": "artist:\"Pyotr Ilyich Tchaikovsky\" AND type:person",
        "work_query": "artist:\"Pyotr Ilyich Tchaikovsky\" AND work:\"Nutcracker\"",
    },
    {
        "composer_id": "gustav-mahler",
        "name_en": "Gustav Mahler",
        "wikidata_qid": "Q7304",
        "musicbrainz_query": "artist:\"Gustav Mahler\" AND type:person",
        "work_query": "artist:\"Gustav Mahler\" AND work:\"Symphony No. 5\"",
    },
    {
        "composer_id": "claude-debussy",
        "name_en": "Claude Debussy",
        "wikidata_qid": "Q4700",
        "musicbrainz_query": "artist:\"Claude Debussy\" AND type:person",
        "work_query": "artist:\"Claude Debussy\" AND work:\"Clair de lune\"",
    },
    {
        "composer_id": "igor-stravinsky",
        "name_en": "Igor Stravinsky",
        "wikidata_qid": "Q7314",
        "musicbrainz_query": "artist:\"Igor Stravinsky\" AND type:person",
        "work_query": "artist:\"Igor Stravinsky\" AND work:\"Rite of Spring\"",
    },
]
