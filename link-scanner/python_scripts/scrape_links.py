import sys
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin

visited_links = set()  # To avoid revisiting the same links


def log(message):
    """Custom logger to print messages to stdout."""
    print(f"[LOG] {message}", flush=True)  # Ensure logs are flushed immediately


def clean_url(url):
    """Clean URL to remove unnecessary parts."""
    return url.replace('/panorama', '')


def scrape_links_from_html(html_content, base_url):
    """Extract links using BeautifulSoup."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []

    # Extract all valid <a href> links
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href and not href.startswith(('javascript:', 'mailto:', '#')):  # Filter invalid links
            full_url = urljoin(base_url, href)  # Convert relative URLs to absolute
            links.append(clean_url(full_url))

    unique_links = list(set(links))  # Remove duplicates
    log(f"Extracted {len(unique_links)} unique links from {base_url}")
    return unique_links


def extract_page_content(soup):
    """Extract title, summary, and main content using BeautifulSoup."""
    content = {}

    # Extract title from <p> or <div> with class "stories-title"
    title_tag = soup.find('p', class_="stories-title") or soup.find('div', class_="stories-title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # If title is not found, use the <title> tag as a fallback
    if not title:
        title = soup.title.string if soup.title else 'No title available'
    content['title'] = title

    # Extract the main body text from <p> tags (summary content)
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
    content['summary'] = ' '.join(paragraphs[:3]) if paragraphs else 'No content available'

    log(f"Extracted content: Title='{content['title']}', Summary='{content['summary']}'")
    return content


def scrape_with_selenium(url, depth=1, max_depth=2):
    """Scrape the page using Selenium and process with BeautifulSoup."""
    if url in visited_links:
        log(f"Skipping {url} as it is already visited.")
        return []

    if depth > max_depth:
        log(f"Max depth of {max_depth} reached for {url}. Stopping recursion.")
        return []

    visited_links.add(url)
    log(f"Scraping URL: {url} at depth {depth}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-images")

    # Specify paths for Chromium and Chromedriver
    options.binary_location = "/usr/bin/chromium-browser"
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        log("Initializing WebDriver")
        driver.set_page_load_timeout(30)  # Timeout for page loading

        log(f"Opening URL: {url}")
        driver.get(url)

        # Add explicit wait for body tag to load
        log("Waiting for body tag to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        log(f"Page loaded for {url}")

        # Use Selenium to get the HTML content
        log("Fetching HTML content")
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract content and links using BeautifulSoup
        page_content = extract_page_content(soup)
        links = scrape_links_from_html(html_content, url)

        # Limit the number of links to scrape for safety
        log(f"Processing up to 10 links from {url}")
        links = links[:10]

        result = {
            'url': clean_url(url),
            'content': page_content,
            'links': [
                scrape_with_selenium(link, depth + 1, max_depth) for link in links
            ],
        }

        log(f"Scraped data from {url}: {result}")
        return result

    except Exception as e:
        log(f"Error while scraping {url}: {str(e)}")
        return {'url': url, 'error': str(e), 'links': []}

    finally:
        log(f"Closing driver for {url}")
        driver.quit()


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No URL provided"}))
            sys.exit(1)

        url = sys.argv[1]
        max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 2  # Default max depth is 2

        log(f"Starting scrape for URL: {url} with max depth: {max_depth}")

        result = scrape_with_selenium(url, max_depth=max_depth)
        print(json.dumps(result, indent=2))  # Ensure valid JSON output

        log(f"Scraping completed for URL: {url}")

    except Exception as e:
        log(f"Critical error: {str(e)}")
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
