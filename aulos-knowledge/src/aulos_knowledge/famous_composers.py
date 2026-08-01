"""Famous composers used as crawl / explore seed network (allowlisted Wikidata QIDs).

Product entry points for Explore (META-001 §3.4): human names first, QIDs derived server-side.
Only CC0 Wikidata + ODbL MusicBrainz + internal catalog — no arbitrary scrapes.
"""

from __future__ import annotations

from typing import Any


def _c(
    composer_id: str,
    name_en: str,
    qid: str,
    *,
    short: str = "",
    name_zh: str = "",
    era: str = "",
    wikipedia_title: str = "",
    featured: bool = True,
) -> dict[str, Any]:
    title = wikipedia_title or name_en
    letter_src = short or name_en
    # Prefer surname initial for A–Z browse (short_name)
    letter = (letter_src[:1] if letter_src else "#").upper()
    if not letter.isalpha():
        letter = "#"
    return {
        "composer_id": composer_id,
        "name_en": name_en,
        "name_zh": name_zh,
        "short_name": short or name_en.split()[-1],
        "era": era,
        "wikidata_qid": qid,
        "wikipedia_title": title,
        "musicbrainz_query": f'artist:"{name_en}" AND type:person',
        "work_query": f'artist:"{name_en}"',
        "featured": featured,
        "sort_key": (short or name_en).casefold(),
        "letter": letter,
    }


# Curated seed network — featured classical composers for A–Z browse (META-001 §3.4)
FAMOUS_COMPOSERS: list[dict[str, Any]] = [
    _c("isaac-albeniz", "Isaac Albéniz", "Q188972", short="Albéniz", name_zh="阿尔贝尼斯", era="Romantic"),
    _c("johann-sebastian-bach", "Johann Sebastian Bach", "Q1339", short="Bach", name_zh="巴赫", era="Baroque"),
    _c("ludwig-van-beethoven", "Ludwig van Beethoven", "Q255", short="Beethoven", name_zh="贝多芬", era="Classical–Romantic"),
    _c("hector-berlioz", "Hector Berlioz", "Q1145", short="Berlioz", name_zh="柏辽兹", era="Romantic"),
    _c("johannes-brahms", "Johannes Brahms", "Q7294", short="Brahms", name_zh="勃拉姆斯", era="Romantic"),
    _c("frederic-chopin", "Frédéric Chopin", "Q1268", short="Chopin", name_zh="肖邦", era="Romantic"),
    _c("claude-debussy", "Claude Debussy", "Q4700", short="Debussy", name_zh="德彪西", era="Impressionist"),
    _c("antonin-dvorak", "Antonín Dvořák", "Q7298", short="Dvořák", name_zh="德沃夏克", era="Romantic"),
    _c("edward-elgar", "Edward Elgar", "Q180789", short="Elgar", name_zh="埃尔加", era="Romantic"),
    _c("gabriel-faure", "Gabriel Fauré", "Q180730", short="Fauré", name_zh="福雷", era="Romantic"),
    _c("george-frideric-handel", "George Frideric Handel", "Q7302", short="Handel", name_zh="亨德尔", era="Baroque"),
    _c("joseph-haydn", "Joseph Haydn", "Q7349", short="Haydn", name_zh="海顿", era="Classical"),
    _c("franz-liszt", "Franz Liszt", "Q41309", short="Liszt", name_zh="李斯特", era="Romantic"),
    _c("gustav-mahler", "Gustav Mahler", "Q7304", short="Mahler", name_zh="马勒", era="Late Romantic"),
    _c("felix-mendelssohn", "Felix Mendelssohn", "Q46096", short="Mendelssohn", name_zh="门德尔松", era="Romantic"),
    _c("wolfgang-amadeus-mozart", "Wolfgang Amadeus Mozart", "Q254", short="Mozart", name_zh="莫扎特", era="Classical"),
    _c("sergei-prokofiev", "Sergei Prokofiev", "Q83576", short="Prokofiev", name_zh="普罗科菲耶夫", era="Modern"),
    _c("giacomo-puccini", "Giacomo Puccini", "Q7311", short="Puccini", name_zh="普契尼", era="Romantic"),
    _c("sergei-rachmaninoff", "Sergei Rachmaninoff", "Q131861", short="Rachmaninoff", name_zh="拉赫玛尼诺夫", era="Late Romantic"),
    _c("maurice-ravel", "Maurice Ravel", "Q1178", short="Ravel", name_zh="拉威尔", era="Impressionist"),
    _c("camille-saint-saens", "Camille Saint-Saëns", "Q150445", short="Saint-Saëns", name_zh="圣桑", era="Romantic"),
    _c("erik-satie", "Erik Satie", "Q187192", short="Satie", name_zh="萨蒂", era="Modern"),
    _c("franz-schubert", "Franz Schubert", "Q7312", short="Schubert", name_zh="舒伯特", era="Romantic"),
    _c("robert-schumann", "Robert Schumann", "Q7351", short="Schumann", name_zh="舒曼", era="Romantic"),
    _c("dmitri-shostakovich", "Dmitri Shostakovich", "Q80135", short="Shostakovich", name_zh="肖斯塔科维奇", era="Modern"),
    _c("bedrich-smetana", "Bedřich Smetana", "Q48173", short="Smetana", name_zh="斯美塔那", era="Romantic"),
    _c("igor-stravinsky", "Igor Stravinsky", "Q7314", short="Stravinsky", name_zh="斯特拉文斯基", era="Modern"),
    _c("pyotr-ilyich-tchaikovsky", "Pyotr Ilyich Tchaikovsky", "Q7315", short="Tchaikovsky", name_zh="柴可夫斯基", era="Romantic"),
    _c("giuseppe-verdi", "Giuseppe Verdi", "Q7317", short="Verdi", name_zh="威尔第", era="Romantic"),
    _c("antonio-vivaldi", "Antonio Vivaldi", "Q1340", short="Vivaldi", name_zh="维瓦尔第", era="Baroque"),
    _c("richard-wagner", "Richard Wagner", "Q1511", short="Wagner", name_zh="瓦格纳", era="Romantic"),
]


def famous_by_id() -> dict[str, dict[str, Any]]:
    return {c["composer_id"]: c for c in FAMOUS_COMPOSERS}


def famous_by_qid() -> dict[str, dict[str, Any]]:
    return {c["wikidata_qid"]: c for c in FAMOUS_COMPOSERS}


# Headline featured strip (product home for Explore) — keep short
FEATURED_COMPOSER_IDS: tuple[str, ...] = (
    "johann-sebastian-bach",
    "wolfgang-amadeus-mozart",
    "ludwig-van-beethoven",
    "frederic-chopin",
    "pyotr-ilyich-tchaikovsky",
    "claude-debussy",
    "franz-schubert",
    "johannes-brahms",
)
