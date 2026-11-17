from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
import re
from subprocess import check_output
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


FEED_URL = "https://guanlili.github.io/feed.xml"
BLOG_HOST = urlsplit(FEED_URL).netloc
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- recent-writing:start -->"
END = "<!-- recent-writing:end -->"
POST_COUNT = 3


def recent_writing():
    xml = check_output(["curl", "-fsSL", "--max-time", "20", FEED_URL])
    feed = ET.fromstring(xml)

    posts = {}
    for item in feed.findall("./channel/item"):
        title = " ".join(item.findtext("title", "").split())
        link = item.findtext("link", "").strip()
        date = item.findtext("pubDate", "").strip()
        url = urlsplit(link)
        if not title or not date or url.scheme != "https" or url.netloc != BLOG_HOST:
            continue
        if any(char.isspace() or char in "<>" for char in link):
            continue

        posts[link] = (parsedate_to_datetime(date).date(), title)

    if len(posts) < POST_COUNT:
        raise ValueError(f"Expected at least {POST_COUNT} articles from {FEED_URL}")

    lines = []
    newest = sorted(posts.items(), key=lambda post: post[1][0], reverse=True)[:POST_COUNT]
    for link, (date, title) in newest:
        title = re.sub(r"([\\\[\]*_~\x60])", r"\\\1", escape(title, quote=False))
        lines.append(f"- {date.isoformat()} · [{title}](<{link}>)")
    return "\n".join(lines)


def main():
    original = README_PATH.read_text(encoding="utf-8")
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError("README must have one pair of recent-writing markers")
    before, _, region = original.partition(START)
    _, separator, after = region.partition(END)
    if not separator:
        raise ValueError("Recent-writing markers are out of order")

    updated = f"{before}{START}\n{recent_writing()}\n{END}{after}"
    if updated != original:
        README_PATH.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
