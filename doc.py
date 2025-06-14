from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# =================== Configuration ===================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

def format_as_paragraph(snippets):
    if not snippets:
        return "No information found."

    intro = f"{snippets[0]}\n"
    bullets = ""
    for i, snippet in enumerate(snippets[1:], start=1):
        bullets += f"- {snippet.strip()}\n"

    return f"{intro}\nKey Points:\n{bullets}"

def main():
    topic = input("Enter topic to search: ").strip().lower()

    print("\nSearching online using Selenium...\n")
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(f"https://www.bing.com/search?q={topic.replace(' ', '+')}")
    time.sleep(3)

    selectors = [
        "li.b_algo p",
        "div.b_caption p",
        "div.b_snippet",
        "div.t_tpc",
        "div.b_vList div.b_vListText"
    ]

    seen = set()
    collected = []
    for selector in selectors:
        snippets = driver.find_elements(By.CSS_SELECTOR, selector)
        for s in snippets:
            text = s.text.strip()
            if text and text not in seen:
                seen.add(text)
                collected.append(text)
            if len(collected) >= 6:
                break
        if len(collected) >= 6:
            break

    driver.quit()

    # Format the collected result as structured answer
    structured_answer = format_as_paragraph(collected)
    print("\nFormatted Answer:\n")
    print(structured_answer)

if __name__ == "__main__":
    main()