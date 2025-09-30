import os, re, time, pathlib, urllib.parse
import requests
from bs4 import BeautifulSoup

PATH = [
    "http://hdgsnn.gov.vn/tin-tuc/danh-sach-ung-vien-duoc-hdgscs-de-nghi-xet-cong-nhan-dat-tieu-chuan-chuc-danh-gs-pgs-nam-2024_789",
    "http://hdgsnn.gov.vn/tin-tuc/danh-sach-ung-vien-duoc-hdgscs-de-nghi-xet-cong-nhan-dat-tieu-chuan-chuc-danh-gs-pgs-nam-2024-phan-2_791",
    "http://hdgsnn.gov.vn/tin-tuc/danh-sach-ung-vien-duoc-hdgscs-de-nghi-xet-cong-nhan-dat-tieu-chuan-chuc-danh-gs-pgs-nam-2024-phan-3_792",
    "http://hdgsnn.gov.vn/tin-tuc/danh-sach-ung-vien-duoc-hdgscs-de-nghi-xet-cong-nhan-dat-tieu-chuan-chuc-danh-gs-pgs-nam-2024-phan-4_793",
    "http://hdgsnn.gov.vn/tin-tuc/danh-sach-ung-vien-duoc-hdgscs-de-nghi-xet-cong-nhan-dat-tieu-chuan-chuc-danh-gs-pgs-nam-2025_819",
    "http://hdgsnn.gov.vn/tin-tuc/danh-sach-ung-vien-duoc-hdgscs-de-nghi-xet-cong-nhan-dat-tieu-chuan-chuc-danh-gs-pgs-nam-2025-phan-2_820",
    "http://hdgsnn.gov.vn/tin-tuc/danh-sach-ung-vien-duoc-hdgscs-de-nghi-xet-cong-nhan-dat-tieu-chuan-chuc-danh-gs-pgs-nam-2025-phan-3_821",
    "http://hdgsnn.gov.vn/tin-tuc/danh-sach-ung-vien-duoc-hdgscs-de-nghi-xet-cong-nhan-dat-tieu-chuan-chuc-danh-gs-pgs-nam-2025-phan-4_822"
]


OUT = pathlib.Path("./data")
OUT.mkdir(exist_ok=True)

def is_pdf_link(href: str) -> bool:
    """Check if link ends with .pdf"""
    return href and re.search(r"\.pdf(?:$|\?)", href, re.I)

for BASE in PATH:

    html = requests.get(BASE, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    pdf_urls = []
    for a in soup.select("a[href]"):
        href = urllib.parse.urljoin(BASE, a["href"])
        if is_pdf_link(href):
            pdf_urls.append(href)

    for url in sorted(set(pdf_urls)):
        try:
            name = OUT / urllib.parse.unquote(url.split("/")[-1].split("?")[0]) # unquote: encode characters, %20 -> space
            r = requests.get(url, timeout=60)
            if r.status_code == 403:
                print(f"Skip {url} (403 Forbidden)")
                continue
            with open(name, "wb") as f: f.write(r.content)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
        time.sleep(0.5)  
    print(f"Downloaded {len(pdf_urls)} PDFs → {OUT.resolve()}")