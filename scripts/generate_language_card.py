"""Generate a GitHub profile language card from public repository language data."""

from collections import Counter
from html import escape
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


USERNAME = "CarefreeHarp"
MAX_LANGUAGES = 12
API_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "CarefreeHarp-profile-readme",
}
if token := os.environ.get("GITHUB_TOKEN"):
    API_HEADERS["Authorization"] = f"Bearer {token}"


def get_json(url: str):
    request = Request(url, headers=API_HEADERS)
    with urlopen(request) as response:  # nosec B310 - GitHub API URL is fixed by this script
        return json.load(response)


def collect_languages() -> Counter:
    repositories = get_json(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner"
    )
    totals = Counter()
    for repository in repositories:
        if repository["fork"] or repository["archived"]:
            continue
        for language, size in get_json(repository["languages_url"]).items():
            totals[language] += size
    return totals


def render_card(totals: Counter) -> str:
    languages = totals.most_common(MAX_LANGUAGES)
    total_size = sum(totals.values()) or 1
    width, height = 900, 110 + len(languages) * 42
    palette = ["#22d3ee", "#c792ea", "#60a5fa", "#34d399", "#fbbf24", "#fb7185"]
    rows = []

    for index, (language, size) in enumerate(languages):
        y = 106 + index * 42
        percentage = size / total_size * 100
        bar_width = max(5, round(percentage * 6.1))
        color = palette[index % len(palette)]
        rows.append(
            f'''<text x="54" y="{y}" class="language">{escape(language)}</text>
  <rect x="245" y="{y - 17}" width="610" height="14" rx="7" fill="#21262d"/>
  <rect x="245" y="{y - 17}" width="{bar_width}" height="14" rx="7" fill="{color}"/>
'''
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">Top Languages</title>
  <desc id="description">Languages used across {USERNAME}'s public, non-forked repositories.</desc>
  <style>
    .title {{ fill: #e6edf3; font: 700 28px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
    .subtitle {{ fill: #8b949e; font: 16px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
    .language {{ fill: #e6edf3; font: 600 17px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
  </style>
  <rect width="100%" height="100%" rx="18" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  <text x="54" y="54" class="title">Top Languages</text>
  <text x="54" y="79" class="subtitle">Across public, non-forked repositories · updated automatically</text>
  {chr(10).join(rows)}
</svg>'''


def main() -> None:
    output = Path("assets/top-languages.svg")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_card(collect_languages()), encoding="utf-8")


if __name__ == "__main__":
    main()
