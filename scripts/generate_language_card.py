"""Generate a GitHub profile language card from public repository language data."""

from collections import Counter
from html import escape
import json
import math
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
    width, height = 900, 430
    palette = ["#22d3ee", "#c792ea", "#60a5fa", "#34d399", "#fbbf24", "#fb7185"]
    segments = []
    legend = []
    center_x, center_y, radius = 225, 254, 122
    start_angle = -90

    for index, (language, size) in enumerate(languages):
        percentage = size / total_size * 100
        color = palette[index % len(palette)]
        end_angle = start_angle + percentage * 3.6
        start_radians, end_radians = math.radians(start_angle), math.radians(end_angle)
        x1, y1 = center_x + radius * math.cos(start_radians), center_y + radius * math.sin(start_radians)
        x2, y2 = center_x + radius * math.cos(end_radians), center_y + radius * math.sin(end_radians)
        large_arc = 1 if end_angle - start_angle > 180 else 0
        segments.append(
            f'<path d="M {center_x} {center_y} L {x1:.2f} {y1:.2f} A {radius} {radius} 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z" fill="{color}" stroke="#0d1117" stroke-width="3"/>'
        )
        column, row = divmod(index, 6)
        x, y = 425 + column * 230, 146 + row * 43
        legend.append(
            f'''<circle cx="{x}" cy="{y - 6}" r="7" fill="{color}"/>
  <text x="{x + 16}" y="{y}" class="language">{escape(language)}</text>
  <text x="{x + 202}" y="{y}" class="percentage">{percentage:.1f}%</text>'''
        )
        start_angle = end_angle

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">Top Languages</title>
  <desc id="description">Languages used across {USERNAME}'s public, non-forked repositories.</desc>
  <style>
    .title {{ fill: #e6edf3; font: 700 28px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
    .subtitle {{ fill: #8b949e; font: 16px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
    .language {{ fill: #e6edf3; font: 600 15px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
    .percentage {{ fill: #8b949e; font: 600 14px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; text-anchor: end; }}
  </style>
  <rect width="100%" height="100%" rx="18" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  <text x="54" y="54" class="title">Top Languages</text>
  <text x="54" y="79" class="subtitle">Across public repositories</text>
  {chr(10).join(segments)}
  <circle cx="225" cy="254" r="77" fill="#0d1117"/>
  <text x="225" y="259" class="language" text-anchor="middle">{len(languages)} languages</text>
  {chr(10).join(legend)}
</svg>'''


def main() -> None:
    output = Path("assets/top-languages.svg")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_card(collect_languages()), encoding="utf-8")


if __name__ == "__main__":
    main()
