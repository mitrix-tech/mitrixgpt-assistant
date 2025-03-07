import os
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

START_URL = "https://mitrix.biz"
DOMAIN = "mitrix.biz"

visited = set()
to_crawl = [START_URL]

os.makedirs("../storage/output", exist_ok=True)
index_csv_path = os.path.join("../storage/output", "index.csv")

with open(index_csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["url", "document", "section"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    while to_crawl:
        current_url = to_crawl.pop()
        if current_url in visited:
            continue
        visited.add(current_url)

        print(f"Crawling: {current_url}")
        try:
            response = requests.get(current_url, timeout=10)
            if response.status_code != 200:
                continue
        except requests.exceptions.RequestException:
            continue

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for script_or_style in soup(["script", "style", "noscript"]):
            script_or_style.extract()

        page_text = soup.get_text(separator=" ", strip=True)
        page_text = " ".join(page_text.split())

        parsed = urlparse(current_url)
        path_slug = parsed.path.strip("/")

        # Determine the "section" based on the first path segment, if any
        if path_slug:
            section = path_slug.split("/")[0]
        else:
            section = "homepage"

        # Build path for writing out the text file
        if path_slug == "":
            path_slug = "index"

        path_parts = path_slug.split("/")
        filename = path_parts[-1] + ".txt"
        subfolder_path = os.path.join("../storage/output", *path_parts[:-1])
        os.makedirs(subfolder_path, exist_ok=True)

        text_file_path = os.path.join("../storage/output", *path_parts) + ".txt"

        with open(text_file_path, mode="w", encoding="utf-8") as f:
            f.write(page_text)

        writer.writerow({"url": current_url, "document": text_file_path, "section": section})

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            joined_url = urljoin(current_url, href)
            parsed_joined_url = urlparse(joined_url)
            if parsed_joined_url.netloc == DOMAIN:
                cleaned_url = parsed_joined_url._replace(fragment="", query="").geturl()
                if cleaned_url not in visited and cleaned_url not in to_crawl:
                    to_crawl.append(cleaned_url)

print("\nCrawling completed. Check the 'output' folder for results.")

