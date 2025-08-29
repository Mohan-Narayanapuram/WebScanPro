import time
import requests
import json
from urllib.parse import urljoin, urldefrag, urlparse
from bs4 import BeautifulSoup

class SimpleCrawler:
    def __init__(self, base_url, max_pages=10, delay=1):
        self.base_url = base_url.rstrip("/")   # normalize
        self.max_pages = max_pages
        self.delay = delay
        self.visited = set()
        self.queue = [self.base_url]
        self.pages = {}
        self.forms = {}

    def fetch(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[-] Failed to fetch {url}: {e}")
            return None

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            link = urljoin(base_url, a["href"])    # make it absolute
            link, _ = urldefrag(link)              # remove #fragment
            if urlparse(link).netloc == urlparse(self.base_url).netloc:
                links.append(link.rstrip("/"))
        return links

    def extract_forms(self, html, page_url):
        soup = BeautifulSoup(html, "html.parser")
        forms = []
        for form in soup.find_all("form"):
            form_details = {
                "action": form.get("action"),
                "method": form.get("method", "get").lower(),
                "inputs": [inp.get("name") for inp in form.find_all("input")]
            }
            forms.append(form_details)
        return forms

    def crawl(self):
        while self.queue and len(self.visited) < self.max_pages:
            url = self.queue.pop(0)
            if url in self.visited:
                continue

            print(f"[+] Crawling: {url}")
            html = self.fetch(url)
            if not html:
                continue

            self.pages[url] = html
            page_forms = self.extract_forms(html, url)
            if page_forms:
                self.forms[url] = page_forms

            for link in self.extract_links(html, url):
                if link not in self.visited and link not in self.queue:
                    self.queue.append(link)

            self.visited.add(url)
            time.sleep(self.delay)

        return {"pages": list(self.pages.keys()), "forms": self.forms}


if __name__ == "__main__":
    crawler = SimpleCrawler("https://books.toscrape.com", max_pages=5, delay=1)
    result = crawler.crawl()

    # Print summary
    print("Pages crawled:", result["pages"])
    print("Forms found:", result["forms"])

    # Save results to JSON file
    with open("crawler_output.json", "w") as f:
        json.dump(result, f, indent=4)

    print("[+] Results saved to crawler_output.json")