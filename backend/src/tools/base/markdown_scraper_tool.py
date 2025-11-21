import re
import os
import html2text
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse


def scrape_website_to_markdown(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
    }

    # Make the HTTP request
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the URL. Status code: {response.status_code}")

    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")
    html_content = soup.prettify()

    # Convert HTML to markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_tables = True
    markdown_content = h.handle(html_content)

    # Clean up excess newlines
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
    markdown_content = markdown_content.strip()

    return markdown_content


if __name__ == "__main__":
    url = "https://www.dhl.com/gb-en/home/supply-chain.html"
    content = scrape_website_to_markdown(url)
    # Save content to a local .txt file (timestamped, per domain)
    try:
        os.makedirs("Leads_Report", exist_ok=True)
        parsed = urlparse(url)
        host = parsed.netloc or "website"
        safe_host = re.sub(r"[^A-Za-z0-9._-]", "_", host)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_path = os.path.join("Leads_Report", f"{safe_host}_{ts}.txt")
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
    except Exception:
        # Best effort: do not fail scraping if saving fails
        pass
