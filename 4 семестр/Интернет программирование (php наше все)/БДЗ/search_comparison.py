"""
Сравнение точности поиска Яндекс и Google

Методика:
  - 208 поисковых комбинаций (2 поисковика × 2 языка × запросы по БД)
  - Для каждого запроса собираем: кол-во найденных документов + URL первых 3 страниц
  - Оцениваем URL: полезно / неизвестно / спам
  - Строим гистограммы популярности БД и «поискового шума»
  - Считаем % совпадения выдачи Яндекс и Google

Запуск:
    pip install requests beautifulsoup4 lxml fake_useragent pandas matplotlib seaborn openpyxl tqdm
    python search_comparison.py
"""

import time
import random
import json
import re
import os
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib
# matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from tqdm import tqdm


OUTPUT_DIR = "results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Задержки между запросами, чтобы не получить бан
DELAY_MIN = 4.0
DELAY_MAX = 9.0

PAGES_TO_COLLECT = 3
RESULTS_PER_PAGE = 10  # стандарт для Yandex и Google

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

RELATIONAL_DBS = ["Oracle", "MySQL", "MSSQL", "PostgreSQL"]

# По 5 БД из каждого типа NoSQL
NOSQL_DBS = [
    # Key-value
    "Redis", "Memcached", "Riak", "Voldemort", "DynamoDB",
    # Document
    "MongoDB", "CouchDB", "Couchbase", "RavenDB", "ArangoDB",
    # Column
    "Cassandra", "HBase", "Hypertable", "Accumulo", "ScyllaDB",
    # Graph
    "Neo4j", "OrientDB", "Titan", "InfiniteGraph", "AllegroGraph",
]

ALL_DBS = RELATIONAL_DBS + NOSQL_DBS

# Дополнительные термины
EXTRA_TERMS_RU = ["нереляционные", "не реляционные"]
EXTRA_TERMS_EN = ["Big Data", "NoSQL"]


def make_queries() -> list[dict]:

    queries = []
    engines = ["yandex", "google"]

    for engine in engines:
        # Русские запросы
        for db in ALL_DBS:
            # Вариант 1: слова (Большие данные — два отдельных слова)
            queries.append({
                "engine": engine, "lang": "ru", "mode": "words",
                "db_name": db,
                "query": f"Большие данные {db}",
            })
            # Вариант 2: фраза (точная фраза «Большие данные»)
            queries.append({
                "engine": engine, "lang": "ru", "mode": "phrase",
                "db_name": db,
                "query": f'"Большие данные" {db}',   # кавычки = фраза в обоих поисковиках
            })

        # Дополнительные термины (нереляционные / не реляционные)
        for term in EXTRA_TERMS_RU:
            queries.append({
                "engine": engine, "lang": "ru", "mode": "words",
                "db_name": term,
                "query": f"Большие данные {term}",
            })
            queries.append({
                "engine": engine, "lang": "ru", "mode": "phrase",
                "db_name": term,
                "query": f'"Большие данные" "{term}"',
            })

        # Английские запросы
        for db in ALL_DBS:
            queries.append({
                "engine": engine, "lang": "en", "mode": "words",
                "db_name": db,
                "query": f"Big Data {db}",
            })
            queries.append({
                "engine": engine, "lang": "en", "mode": "phrase",
                "db_name": db,
                "query": f'"Big Data" {db}',
            })

        for term in EXTRA_TERMS_EN:
            queries.append({
                "engine": engine, "lang": "en", "mode": "words",
                "db_name": term,
                "query": f"Big Data {term}",
            })
            queries.append({
                "engine": engine, "lang": "en", "mode": "phrase",
                "db_name": term,
                "query": f'"Big Data" "{term}"',
            })

    print(f"[INFO] Сгенерировано запросов: {len(queries)}")
    return queries


@dataclass
class SearchResult:
    rank: int
    url: str
    title: str
    snippet: str
    is_ad: bool = False
    relevance: str = "unknown"   # 'useful' | 'unknown' | 'spam'


# Случайная пауза, чтобы не забанили
def _sleep():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


def _get(url: str, params: dict | None = None) -> requests.Response | None:

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"  [WARN] Запрос не выполнен: {e}")
        return None


def parse_yandex(query: str, page: int = 0) -> tuple[int, list[SearchResult]]:
    params = {
        "text": query,
        "p": page,
        "lang": "ru",
    }
    resp = _get("https://yandex.ru/search/", params)
    if resp is None:
        return 0, []

    soup = BeautifulSoup(resp.text, "lxml")

    # Количество найденных документов
    total = 0
    count_elem = soup.select_one(".serp-info__found, .b-pager__info")
    if count_elem:
        nums = re.findall(r"[\d\s]+", count_elem.get_text())
        total_str = "".join(nums[0].split()) if nums else "0"
        try:
            total = int(total_str)
        except ValueError:
            total = 0

    # Органические результаты
    results = []
    rank_offset = page * RESULTS_PER_PAGE
    items = soup.select(".serp-item")
    for i, item in enumerate(items):

        is_ad = bool(item.select_one(".label_color_yellow, [data-fast-name='direct']"))

        url_elem = item.select_one("a.link_theme_outer, a.OrganicTitle-Link")
        url = url_elem["href"] if url_elem else ""
        if not url.startswith("http"):
            continue

        title_elem = item.select_one(".OrganicTitle-LinkText, .organic__title-wrapper")
        title = title_elem.get_text(strip=True) if title_elem else ""

        snippet_elem = item.select_one(".text-container, .OrganicText")
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

        results.append(SearchResult(
            rank=rank_offset + i + 1,
            url=url, title=title, snippet=snippet,
            is_ad=is_ad,
        ))

    return total, results


def parse_google(query: str, page: int = 0) -> tuple[int, list[SearchResult]]:
    """
    Парсит страницу выдачи Google.
    page=0 → первая страница (start=0), page=1 → (start=10), и т.д.
    """
    params = {
        "q": query,
        "start": page * RESULTS_PER_PAGE,
        "hl": "ru",
        "num": RESULTS_PER_PAGE,
    }
    resp = _get("https://www.google.com/search", params)
    if resp is None:
        return 0, []

    soup = BeautifulSoup(resp.text, "lxml")

    # Количество найденных документов
    total = 0
    stat_elem = soup.select_one("#result-stats")
    if stat_elem:
        nums = re.findall(r"[\d,\s]+", stat_elem.get_text())
        if nums:
            try:
                total = int(nums[0].replace(",", "").replace(" ", "").strip())
            except ValueError:
                total = 0

    # Органические результаты
    results = []
    rank_offset = page * RESULTS_PER_PAGE
    items = soup.select("div.g, div[jscontroller]")
    rank = rank_offset
    for item in items:
        # Проверяем на рекламу
        is_ad = bool(item.select_one("[data-text-ad], .ads-ad"))

        link = item.select_one("a[href]")
        if not link:
            continue
        url = link["href"]
        if not url.startswith("http") or "google." in url:
            continue

        title_elem = item.select_one("h3")
        title = title_elem.get_text(strip=True) if title_elem else ""

        snippet_elem = item.select_one(".VwiC3b, .s3v9rd, span[data-ved]")
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

        rank += 1
        results.append(SearchResult(
            rank=rank,
            url=url, title=title, snippet=snippet,
            is_ad=is_ad,
        ))

    return total, results


# ──────────────────────────────────────────────
# 5. АВТОМАТИЧЕСКАЯ ОЦЕНКА РЕЛЕВАНТНОСТИ
# ──────────────────────────────────────────────

SPAM_PATTERNS = [
    r"купить", r"цена", r"скачать бесплатно", r"casino", r"ставки",
    r"отзывы\s+\d", r"интернет-магазин",
]

USEFUL_PATTERNS = [
    r"big\s*data", r"большие\s+данные", r"nosql", r"hadoop", r"spark",
    r"база\s+данных", r"database", r"данные", r"аналитика", r"analytics",
]


def auto_classify(result: SearchResult, db_name: str) -> str:
    """
    Автоматически классифицирует результат поиска.
    Возвращает: 'useful' | 'spam' | 'unknown'
    """
    text = f"{result.title} {result.snippet} {result.url}".lower()
    db_lower = db_name.lower()

    # Спам-признаки
    for pat in SPAM_PATTERNS:
        if re.search(pat, text, re.I):
            return "spam"

    # Документ упоминает и БД, и большие данные → полезный
    has_db = db_lower in text
    has_bigdata = any(re.search(p, text, re.I) for p in USEFUL_PATTERNS)
    if has_db and has_bigdata:
        return "useful"

    return "unknown"


# ──────────────────────────────────────────────
# 6. ОСНОВНОЙ СБОРЩИК ДАННЫХ
# ──────────────────────────────────────────────

def collect_data(queries: list[dict], save_file: str = "results/raw_data.json") -> list[dict]:
    """
    Проходит по всем запросам, собирает результаты, сохраняет JSON.
    Если файл уже существует — загружает из него (кэш).
    """
    if os.path.exists(save_file):
        print(f"[INFO] Найден кэш '{save_file}', загружаем...")
        with open(save_file, encoding="utf-8") as f:
            return json.load(f)

    all_data = []

    for q in tqdm(queries, desc="Сбор данных"):
        engine = q["engine"]
        query_str = q["query"]
        row = {**q, "total_count": 0, "results": []}

        total = 0
        all_results = []

        for page in range(PAGES_TO_COLLECT):
            _sleep()
            if engine == "yandex":
                t, r = parse_yandex(query_str, page)
            else:
                t, r = parse_google(query_str, page)

            if page == 0:
                total = t
            # Классифицируем результаты
            for res in r:
                res.relevance = auto_classify(res, q["db_name"])
            all_results.extend([asdict(res) for res in r if not res.is_ad])

        row["total_count"] = total
        row["results"] = all_results
        all_data.append(row)

    with open(save_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Данные сохранены в '{save_file}'")
    return all_data


# ──────────────────────────────────────────────
# 7. ДЕМО-ДАННЫЕ (когда реальный сбор недоступен)
# ──────────────────────────────────────────────

def generate_demo_data(queries: list[dict]) -> list[dict]:
    """
    Генерирует реалистичные демонстрационные данные для 208 запросов.
    Позволяет тестировать аналитику и визуализацию без реальных запросов.
    """
    rng = random.Random(42)

    # Реалистичные базы популярности (больше у известных БД)
    popularity = {
        "Oracle": 9, "MySQL": 10, "MSSQL": 8, "PostgreSQL": 9,
        "MongoDB": 10, "Redis": 9, "Cassandra": 8, "HBase": 7,
        "Couchbase": 6, "CouchDB": 6, "Neo4j": 7, "DynamoDB": 8,
        "Memcached": 6, "Riak": 4, "Voldemort": 3, "RavenDB": 4,
        "ArangoDB": 5, "Hypertable": 3, "Accumulo": 4, "ScyllaDB": 5,
        "Titan": 3, "OrientDB": 4, "InfiniteGraph": 2, "AllegroGraph": 2,
        "нереляционные": 7, "не реляционные": 6,
        "Big Data": 10, "NoSQL": 9,
    }

    sample_urls = [
        "https://habr.com/ru/articles/{id}/",
        "https://docs.{db}.com/bigdata/",
        "https://medium.com/{db}-big-data-{id}",
        "https://stackoverflow.com/questions/{id}",
        "https://ru.wikipedia.org/wiki/{db}",
        "https://www.cloudera.com/{db}-guide",
        "https://aws.amazon.com/{db}/bigdata",
        "https://cloud.google.com/{db}-analytics",
        "https://dzone.com/articles/{db}-bigdata",
        "https://towardsdatascience.com/{db}-{id}",
    ]

    all_data = []
    for q in queries:
        db = q["db_name"]
        engine = q["engine"]
        pop = popularity.get(db, 5)

        # Общее кол-во результатов (Google обычно даёт больше)
        base = pop * 1_000_000
        noise_factor = 1.3 if engine == "google" else 1.0
        total = int(base * noise_factor * rng.uniform(0.7, 1.4))

        results = []
        n_results = PAGES_TO_COLLECT * RESULTS_PER_PAGE
        for i in range(n_results):
            url_tmpl = rng.choice(sample_urls)
            url = url_tmpl.format(db=db.lower().replace(" ", "-"), id=rng.randint(100000, 999999))

            # Распределение полезности: у популярных БД — больше полезных
            r_val = rng.random()
            useful_prob = 0.3 + pop * 0.05   # 0.35–0.80
            spam_prob = 0.05 + (10 - pop) * 0.03

            if r_val < useful_prob:
                relevance = "useful"
            elif r_val < useful_prob + spam_prob:
                relevance = "spam"
            else:
                relevance = "unknown"

            results.append({
                "rank": i + 1,
                "url": url,
                "title": f"{db} Big Data использование — статья {i + 1}",
                "snippet": f"Как использовать {db} для работы с большими данными...",
                "is_ad": False,
                "relevance": relevance,
            })

        all_data.append({**q, "total_count": total, "results": results})

    print(f"[INFO] Сгенерированы демо-данные для {len(all_data)} запросов")
    return all_data


# ──────────────────────────────────────────────
# 8. АНАЛИТИКА
# ──────────────────────────────────────────────

def build_dataframes(data: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Возвращает два датафрейма:
      df_queries  – один ряд на запрос (total_count, % useful/unknown/spam)
      df_urls     – один ряд на URL
    """
    query_rows = []
    url_rows = []

    for entry in data:
        results = entry.get("results", [])
        n = len(results)
        useful = sum(1 for r in results if r["relevance"] == "useful")
        spam   = sum(1 for r in results if r["relevance"] == "spam")
        unknown= n - useful - spam

        query_rows.append({
            "engine":   entry["engine"],
            "lang":     entry["lang"],
            "mode":     entry["mode"],
            "db_name":  entry["db_name"],
            "query":    entry["query"],
            "total":    entry["total_count"],
            "n_results": n,
            "useful":   useful,
            "unknown":  unknown,
            "spam":     spam,
            "pct_useful":  useful  / n * 100 if n else 0,
            "pct_unknown": unknown / n * 100 if n else 0,
            "pct_spam":    spam    / n * 100 if n else 0,
        })

        for r in results:
            url_rows.append({
                **{k: entry[k] for k in ("engine", "lang", "mode", "db_name")},
                **r,
            })

    df_q = pd.DataFrame(query_rows)
    df_u = pd.DataFrame(url_rows)
    return df_q, df_u


def compute_overlap(df_urls: pd.DataFrame) -> pd.DataFrame:
    """
    Считает % совпадения URL в выдаче Яндекс и Google
    по каждому запросу (db_name, lang, mode).
    """
    rows = []
    groups = df_urls.groupby(["lang", "mode", "db_name"])
    for (lang, mode, db), grp in groups:
        yandex_urls = set(grp[grp["engine"] == "yandex"]["url"])
        google_urls = set(grp[grp["engine"] == "google"]["url"])
        union = yandex_urls | google_urls
        inter = yandex_urls & google_urls
        pct = len(inter) / len(union) * 100 if union else 0
        rows.append({"lang": lang, "mode": mode, "db_name": db,
                     "overlap_pct": pct, "common": len(inter), "total_unique": len(union)})
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# 9. ВИЗУАЛИЗАЦИИ
# ──────────────────────────────────────────────

PALETTE = {"yandex": "#FC3F1D", "google": "#4285F4"}
FIG_SIZE = (14, 6)
DPI = 120


def _save(fig, name: str):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Сохранено: {path}")


def plot_popularity(df_q: pd.DataFrame):
    """Гистограмма популярности БД (кол-во результатов)."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=False)
    langs = [("ru", "Русские запросы"), ("en", "English queries")]

    for ax, (lang, title) in zip(axes, langs):
        sub = df_q[df_q["lang"] == lang].groupby(["db_name", "engine"])["total"].mean().reset_index()
        pivot = sub.pivot(index="db_name", columns="engine", values="total").fillna(0)
        pivot = pivot.sort_values("google" if "google" in pivot.columns else pivot.columns[0],
                                  ascending=False).head(20)

        x = range(len(pivot))
        w = 0.35
        cols = pivot.columns.tolist()
        for i, eng in enumerate(cols):
            ax.bar([v + i * w for v in x], pivot[eng], width=w,
                   label=eng.capitalize(), color=PALETTE.get(eng, "gray"), alpha=0.85)

        ax.set_xticks([v + w / 2 for v in x])
        ax.set_xticklabels(pivot.index, rotation=45, ha="right", fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M"))
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_ylabel("Кол-во найденных документов (млн)")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Популярность БД по поисковым запросам", fontsize=14, fontweight="bold", y=1.02)
    _save(fig, "1_popularity.png")


def plot_noise(df_q: pd.DataFrame):
    """Гистограмма «поискового шума» (% спам-документов)."""
    fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE, sharey=True)
    langs = [("ru", "Русские запросы"), ("en", "English queries")]

    for ax, (lang, title) in zip(axes, langs):
        sub = df_q[df_q["lang"] == lang].groupby(["db_name", "engine"])[["pct_spam"]].mean().reset_index()
        pivot = sub.pivot(index="db_name", columns="engine", values="pct_spam").fillna(0)
        pivot = pivot.sort_values("yandex" if "yandex" in pivot.columns else pivot.columns[0],
                                  ascending=False).head(20)
        x = range(len(pivot))
        w = 0.35
        for i, eng in enumerate(pivot.columns):
            ax.bar([v + i * w for v in x], pivot[eng], width=w,
                   label=eng.capitalize(), color=PALETTE.get(eng, "gray"), alpha=0.85)

        ax.set_xticks([v + w / 2 for v in x])
        ax.set_xticklabels(pivot.index, rotation=45, ha="right", fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_ylabel("% спам-документов")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Поисковой шум: % спам-документов", fontsize=14, fontweight="bold", y=1.02)
    _save(fig, "2_spam_noise.png")


def plot_relevance_comparison(df_q: pd.DataFrame):
    """Сравнение средних % полезных / неизвестных / спам для Яндекс и Google."""
    summary = df_q.groupby("engine")[["pct_useful", "pct_unknown", "pct_spam"]].mean()
    fig, ax = plt.subplots(figsize=(8, 5))
    summary.T.plot(kind="bar", ax=ax, color=[PALETTE["yandex"], PALETTE["google"]], alpha=0.85)
    ax.set_xticklabels(["Полезно", "Неизвестно", "Спам"], rotation=0)
    ax.set_ylabel("Среднее значение (%)")
    ax.set_title("Сравнение качества выдачи: Яндекс vs Google", fontsize=13, fontweight="bold")
    ax.legend(["Яндекс", "Google"])
    ax.grid(axis="y", alpha=0.3)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f%%", fontsize=9, padding=3)
    _save(fig, "3_relevance_comparison.png")


def plot_overlap(df_overlap: pd.DataFrame):
    """% совпадения URL между Яндекс и Google."""
    avg = df_overlap.groupby("db_name")["overlap_pct"].mean().sort_values(ascending=False).head(24)
    fig, ax = plt.subplots(figsize=(14, 5))
    bars = ax.bar(avg.index, avg.values, color="#5C6BC0", alpha=0.85)
    ax.set_xticklabels(avg.index, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("% совпадения URL")
    ax.set_title("Совпадение поисковой выдачи Яндекс и Google по БД", fontsize=13, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.grid(axis="y", alpha=0.3)
    ax.axhline(avg.mean(), linestyle="--", color="red", linewidth=1.2, label=f"Среднее: {avg.mean():.1f}%")
    ax.legend()
    _save(fig, "4_overlap.png")


def plot_heatmap(df_q: pd.DataFrame):
    """Тепловая карта: полезность выдачи (Яндекс) по БД и типу запроса."""
    for engine in ["yandex", "google"]:
        sub = df_q[(df_q["engine"] == engine) & (df_q["lang"] == "ru")]
        pivot = sub.pivot_table(index="db_name", columns="mode", values="pct_useful", aggfunc="mean")
        if pivot.empty:
            continue
        fig, ax = plt.subplots(figsize=(8, 10))
        sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGn",
                    linewidths=0.5, ax=ax, cbar_kws={"label": "% полезных"})
        ax.set_title(f"{engine.capitalize()}: % полезных документов (рус. запросы)",
                     fontsize=12, fontweight="bold")
        ax.set_xlabel("Режим запроса")
        ax.set_ylabel("База данных")
        _save(fig, f"5_heatmap_{engine}.png")


# ──────────────────────────────────────────────
# 10. ЭКСПОРТ РЕЗУЛЬТАТОВ
# ──────────────────────────────────────────────

def export_excel(df_q: pd.DataFrame, df_overlap: pd.DataFrame):
    """Сохраняет результаты в Excel."""
    path = os.path.join(OUTPUT_DIR, "search_results.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_q.to_excel(writer, sheet_name="Все запросы", index=False)
        df_overlap.to_excel(writer, sheet_name="Совпадение URL", index=False)

        # Сводная по движкам
        summary = df_q.groupby("engine")[["pct_useful", "pct_unknown", "pct_spam"]].mean().round(2)
        summary.to_excel(writer, sheet_name="Сводка")

    print(f"  Сохранено: {path}")


def export_csv(df_q: pd.DataFrame):
    path = os.path.join(OUTPUT_DIR, "search_results.csv")
    df_q.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  Сохранено: {path}")


def print_summary(df_q: pd.DataFrame, df_overlap: pd.DataFrame):
    print("\n" + "=" * 60)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)

    for engine in ["yandex", "google"]:
        sub = df_q[df_q["engine"] == engine]
        print(f"\n{'Яндекс' if engine == 'yandex' else 'Google'}:")
        print(f"  Среднее кол-во результатов: {sub['total'].mean():,.0f}")
        print(f"  Полезные:    {sub['pct_useful'].mean():.1f}%")
        print(f"  Неизвестные: {sub['pct_unknown'].mean():.1f}%")
        print(f"  Спам:        {sub['pct_spam'].mean():.1f}%")

    print(f"\nСреднее совпадение URL (Яндекс vs Google): {df_overlap['overlap_pct'].mean():.1f}%")
    print("=" * 60)


# ──────────────────────────────────────────────
# 11. ТОЧКА ВХОДА
# ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Сравнение точности поиска: Яндекс vs Google")
    print("БДЗ по Интернет-программированию, 2025–2026")
    print("=" * 60)

    # Генерируем список запросов
    queries = make_queries()

    # Выбор режима: реальный сбор или демо
    use_demo = True  # ← поменяйте на False для реального сбора (нужен VPN/прокси)

    print(f"\n[MODE] {'Демо-данные (без реальных HTTP-запросов)' if use_demo else 'Реальный сбор данных'}")

    if use_demo:
        raw_data = generate_demo_data(queries)
    else:
        raw_data = collect_data(queries, save_file=os.path.join(OUTPUT_DIR, "raw_data.json"))

    # Строим датафреймы
    print("\n[INFO] Обработка данных...")
    df_queries, df_urls = build_dataframes(raw_data)
    df_overlap = compute_overlap(df_urls)

    # Статистика в консоль
    print_summary(df_queries, df_overlap)

    # Визуализации
    print("\n[INFO] Генерация графиков...")
    plot_popularity(df_queries)
    plot_noise(df_queries)
    plot_relevance_comparison(df_queries)
    plot_overlap(df_overlap)
    plot_heatmap(df_queries)

    # Экспорт
    print("\n[INFO] Экспорт данных...")
    export_excel(df_queries, df_overlap)
    export_csv(df_queries)

    print(f"\n✅ Все результаты сохранены в папку '{OUTPUT_DIR}/'")
    print("   Графики: 1_popularity.png, 2_spam_noise.png,")
    print("            3_relevance_comparison.png, 4_overlap.png, 5_heatmap_*.png")
    print("   Таблицы: search_results.xlsx, search_results.csv")


if __name__ == "__main__":
    main()
