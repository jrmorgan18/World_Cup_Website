#!/usr/bin/env python3
"""Validate the generated Dual Eights site without external dependencies."""

from __future__ import annotations

import argparse
import posixpath
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse


SITE_HOSTS = {"dualeights.com", "www.dualeights.com"}
REQUIRED_ROUTES = (
    "/",
    "/404.html",
    "/robots.txt",
    "/sitemap.xml",
    "/soccer/",
    "/soccer/project-2030/",
    "/orioles/",
    "/orioles/brandon-young-breakout/",
    "/ravens/",
    "/usmnt/why-the-usmnt-will-never-be-argentina/",
    "/usmnt/why-the-usmnt-will-never-be-argentina-part-2/",
)
PROHIBITED_OUTPUT_DIRS = ("articles", "designs", "scripts", "worker")
PROHIBITED_HTML_TEXT = ("id=\"wcg-chat\"", "world-cup-chat.jrmorgan16.workers.dev")


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str]] = []
        self.canonicals: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value for name, value in attrs if value is not None}
        for attribute in ("href", "src", "poster"):
            value = values.get(attribute)
            if value:
                self.references.append((attribute, value.strip()))

        if tag.lower() == "link" and "canonical" in values.get("rel", "").lower().split():
            canonical = values.get("href")
            if canonical:
                self.canonicals.append(canonical.strip())


def route_to_candidates(site_dir: Path, route: str) -> tuple[Path, ...]:
    clean = unquote(route).replace("\\", "/")
    clean = posixpath.normpath("/" + clean.lstrip("/"))
    relative = clean.lstrip("/")

    if clean.endswith("/") or not relative:
        return (site_dir / relative / "index.html",)

    candidate = site_dir / relative
    if Path(relative).suffix:
        return (candidate,)

    return (candidate, site_dir / f"{relative}.html", candidate / "index.html")


def route_exists(site_dir: Path, route: str) -> bool:
    return any(candidate.is_file() for candidate in route_to_candidates(site_dir, route))


def page_url(html_file: Path, site_dir: Path) -> str:
    relative = html_file.relative_to(site_dir).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[: -len("index.html")]
    return "/" + relative


def validate(site_dir: Path) -> list[str]:
    errors: list[str] = []

    if not site_dir.is_dir():
        return [f"Build directory does not exist: {site_dir}"]

    for directory in PROHIBITED_OUTPUT_DIRS:
        if (site_dir / directory).exists():
            errors.append(f"Testing/source directory was published: /{directory}/")

    for route in REQUIRED_ROUTES:
        if not route_exists(site_dir, route):
            errors.append(f"Required launch route is missing: {route}")

    html_files = sorted(site_dir.rglob("*.html"))
    if not html_files:
        errors.append("No HTML files were generated")
        return errors

    for html_file in html_files:
        source_url = page_url(html_file, site_dir)
        content = html_file.read_text(encoding="utf-8")

        for prohibited in PROHIBITED_HTML_TEXT:
            if prohibited in content:
                errors.append(f"Disabled chat markup remains in {source_url}: {prohibited}")

        parser = PageParser()
        parser.feed(content)

        if len(parser.canonicals) != 1:
            errors.append(
                f"Expected one canonical URL in {source_url}; found {len(parser.canonicals)}"
            )
        elif urlparse(parser.canonicals[0]).hostname != "dualeights.com":
            errors.append(
                f"Canonical URL does not use dualeights.com in {source_url}: "
                f"{parser.canonicals[0]}"
            )

        for attribute, reference in parser.references:
            if not reference or reference.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                continue

            parsed = urlparse(reference)
            if parsed.scheme in {"http", "https"} and parsed.hostname not in SITE_HOSTS:
                continue
            if parsed.scheme and parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc and parsed.hostname not in SITE_HOSTS:
                continue

            resolved = urlparse(urljoin(f"https://dualeights.com{source_url}", reference))
            route = resolved.path or "/"
            if not route_exists(site_dir, route):
                errors.append(
                    f"Broken internal {attribute} in {source_url}: {reference} -> {route}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site_dir", type=Path)
    args = parser.parse_args()

    errors = validate(args.site_dir.resolve())
    if errors:
        print(f"Site validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Site validation passed: {args.site_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
