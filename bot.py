import os
import json
import unicodedata
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Normalize string to safe filename
def normalize_filename(url):
    title = url.split("/")[-1]
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    return title.replace(" ", "_") + ".json"

# Scrape paragraphs from a Wikipedia URL
async def scrape_paragraphs(url, session, semaphore):
    async with semaphore:
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Set headers to mimic a browser and avoid bot detection
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            # Make the async request
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                html = await response.text()
            
            # Parse HTML content
            soup = BeautifulSoup(html, 'html.parser')
            content = soup.select_one("#mw-content-text .mw-parser-output")
            
            if not content:
                logger.warning(f"Main content section not found for URL: {url}")
                return None

            # Extract page title
            page_title = soup.select_one("h1#firstHeading")
            page_title = page_title.get_text(strip=True) if page_title else "Unknown Title"

            # Remove reference/citation elements
            for ref in content.find_all(class_="reference"):
                ref.decompose()

            # Collect paragraphs and clean citations
            paragraphs = []
            citation_pattern = r'\[\d+\](?:\s*\[\d+\])*'
            
            for p_tag in content.find_all('p'):
                paragraph_text = p_tag.get_text(separator=' ', strip=True)
                if paragraph_text:
                    cleaned_text = re.sub(citation_pattern, '', paragraph_text).strip()
                    if cleaned_text:
                        paragraphs.append(cleaned_text)

            logger.info(f"Collected {len(paragraphs)} paragraphs from {url}")

            # Structure data
            if paragraphs:
                data = {
                    "url": url,
                    "title": page_title,
                    "paragraph_count": len(paragraphs),
                    "paragraphs": paragraphs,
                    "scraped_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                }
                return data
            
            logger.warning(f"No paragraphs found for URL: {url}")
            return None

        except aiohttp.ClientError as e:
            logger.error(f"Network error while scraping {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while scraping {url}: {str(e)}")
            return None

# Save data to file
def save_to_file(data, output_dir):
    if not data:
        return
    
    filename = normalize_filename(data["url"])
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved data to: {filepath}")
    except Exception as e:
        logger.error(f"Error saving {filename}: {str(e)}")

# Main async function to process URLs
async def process_urls(urls, output_dir):
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Limit concurrent requests to 5 to avoid rate limiting
    semaphore = asyncio.Semaphore(5)
    
    # Create an aiohttp session
    async with aiohttp.ClientSession() as session:
        # Create tasks for all URLs
        tasks = [scrape_paragraphs(url, session, semaphore) for url in urls]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Save results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {str(result)}")
                continue
            save_to_file(result, output_dir)

# Main entry point
if __name__ == "__main__":
    urls = [
        "https://en.wikipedia.org/wiki/Mahatma_Gandhi",
        "https://en.wikipedia.org/wiki/Jawaharlal_Nehru",
        "https://en.wikipedia.org/wiki/B._R._Ambedkar",
        "https://en.wikipedia.org/wiki/Sardar_Vallabhbhai_Patel",
        "https://en.wikipedia.org/wiki/Subhas_Chandra_Bose",
        "https://en.wikipedia.org/wiki/Rabindranath_Tagore",
        "https://en.wikipedia.org/wiki/Indira_Gandhi",
        "https://en.wikipedia.org/wiki/A._P._J._Abdul_Kalam",
        "https://en.wikipedia.org/wiki/Sachin_Tendulkar",
        "https://en.wikipedia.org/wiki/Lata_Mangeshkar",
        "https://en.wikipedia.org/wiki/A._R._Rahman",
        "https://en.wikipedia.org/wiki/Swami_Vivekananda",
        "https://en.wikipedia.org/wiki/Sri_Aurobindo",
        "https://en.wikipedia.org/wiki/Rani_Lakshmibai",
        "https://en.wikipedia.org/wiki/C._V._Raman",
        "https://en.wikipedia.org/wiki/Satyendra_Nath_Bose",
        "https://en.wikipedia.org/wiki/Jagadish_Chandra_Bose",
        "https://en.wikipedia.org/wiki/Homi_J._Bhabha",
        "https://en.wikipedia.org/wiki/Venkatraman_Ramakrishnan",
        "https://en.wikipedia.org/wiki/Subrahmanyan_Chandrasekhar",
        "https://en.wikipedia.org/wiki/Har_Gobind_Khorana",
        "https://en.wikipedia.org/wiki/Amitabh_Bachchan",
        "https://en.wikipedia.org/wiki/Shah_Rukh_Khan",
        "https://en.wikipedia.org/wiki/Priyanka_Chopra",
        "https://en.wikipedia.org/wiki/Kareena_Kapoor",
        "https://en.wikipedia.org/wiki/Raja_Rammohan_Roy",
        "https://en.wikipedia.org/wiki/Vinoba_Bhave",
        "https://en.wikipedia.org/wiki/Ashoka",
        "https://en.wikipedia.org/wiki/Akbar",
        "https://en.wikipedia.org/wiki/M._S._Swaminathan",
        "https://en.wikipedia.org/wiki/Amartya_Sen",
        "https://en.wikipedia.org/wiki/E._Sreedharan",
        "https://en.wikipedia.org/wiki/Kapil_Dev",
        "https://en.wikipedia.org/wiki/Sunil_Gavaskar",
        "https://en.wikipedia.org/wiki/Viswanathan_Anand",
        "https://en.wikipedia.org/wiki/M._F._Husain",
        "https://en.wikipedia.org/wiki/R._K._Narayan",
        "https://en.wikipedia.org/wiki/R._K._Laxman",
        "https://en.wikipedia.org/wiki/B._K._S._Iyengar",
        "https://en.wikipedia.org/wiki/M._S._Subbulakshmi",
        "https://en.wikipedia.org/wiki/C._Rajagopalachari",
        "https://en.wikipedia.org/wiki/Sam_Manekshaw",
        "https://en.wikipedia.org/wiki/Kamal_Haasan",
        "https://en.wikipedia.org/wiki/N._R._Narayana_Murthy",
        "https://en.wikipedia.org/wiki/Dhirubhai_Ambani",
        "https://en.wikipedia.org/wiki/Mukesh_Ambani",
        "https://en.wikipedia.org/wiki/Savitri_Jindal",
        "https://en.wikipedia.org/wiki/P._T._Usha",
        "https://en.wikipedia.org/wiki/Siddhartha_Gautama",
        "https://en.wikipedia.org/wiki/Anna_Chandy",
        "https://en.wikipedia.org/wiki/Paramahansa_Yogananda",
        "https://en.wikipedia.org/wiki/Babur",
        "https://en.wikipedia.org/wiki/Abhinav_Bindra",
        "https://en.wikipedia.org/wiki/Rishi_Kapoor",
        "https://en.wikipedia.org/wiki/Sathya_Sai_Baba",
        "https://en.wikipedia.org/wiki/Ramana_Maharshi",
        "https://en.wikipedia.org/wiki/Chetan_Bhagat",
        "https://en.wikipedia.org/wiki/Shashi_Tharoor",
        "https://en.wikipedia.org/wiki/Ramachandra_Guha",
        "https://en.wikipedia.org/wiki/Dadabhai_Naoroji",
        "https://en.wikipedia.org/wiki/Ashutosh_Mukherji",
        "https://en.wikipedia.org/wiki/Dhundiraj_Govind_Phalke",
        "https://en.wikipedia.org/wiki/Meghnad_Saha",
        "https://en.wikipedia.org/wiki/Prasanta_Chandra_Mahalanobis",
        "https://en.wikipedia.org/wiki/Vikram_Sarabhai",
        "https://en.wikipedia.org/wiki/Srinivasa_Ramanujan",
        "https://en.wikipedia.org/wiki/Mirabai",
        "https://en.wikipedia.org/wiki/Kabir",
        "https://en.wikipedia.org/wiki/Salman_Khan",
        "https://en.wikipedia.org/wiki/Deepika_Padukone",
        "https://en.wikipedia.org/wiki/Virat_Kohli",
        "https://en.wikipedia.org/wiki/Sania_Mirza",
        "https://en.wikipedia.org/wiki/Mary_Kom",
        "https://en.wikipedia.org/wiki/Dhyan_Chand",
        "https://en.wikipedia.org/wiki/Ravi_Shankar",
        "https://en.wikipedia.org/wiki/Zakir_Hussain_(musician)",
        "https://en.wikipedia.org/wiki/Bal_Gangadhar_Tilak",
        "https://en.wikipedia.org/wiki/Lal_Bahadur_Shastri",
        "https://en.wikipedia.org/wiki/V._V._S._Laxman",
        "https://en.wikipedia.org/wiki/Anil_Ambani",
        "https://en.wikipedia.org/wiki/Sundar_Pichai",
        "https://en.wikipedia.org/wiki/Satya_Nadella",
        "https://en.wikipedia.org/wiki/Lakshmi_Mittal",
        "https://en.wikipedia.org/wiki/Ratan_Tata",
        "https://en.wikipedia.org/wiki/Azim_Premji",
        "https://en.wikipedia.org/wiki/Kiran_Bedi",
        "https://en.wikipedia.org/wiki/Medha_Patkar",
        "https://en.wikipedia.org/wiki/Kailash_Satyarthi",
        "https://en.wikipedia.org/wiki/Arundhati_Roy",
        "https://en.wikipedia.org/wiki/Vikram_Seth",
        "https://en.wikipedia.org/wiki/Jhumpa_Lahiri",
        "https://en.wikipedia.org/wiki/Hariprasad_Chaurasia",
        "https://en.wikipedia.org/wiki/Amrita_Pritam",
        "https://en.wikipedia.org/wiki/Sarojini_Naidu",
        "https://en.wikipedia.org/wiki/Bhagat_Singh",
        "https://en.wikipedia.org/wiki/Chandrashekhar_Azad",
        "https://en.wikipedia.org/wiki/Jiddu_Krishnamurti",
        "https://en.wikipedia.org/wiki/Rajiv_Gandhi",
        "https://en.wikipedia.org/wiki/Sonia_Gandhi",
        "https://en.wikipedia.org/wiki/Narendra_Modi",
        "https://en.wikipedia.org/wiki/Atal_Bihari_Vajpayee",
        "https://en.wikipedia.org/wiki/Manmohan_Singh",
        
    ]

    output_dir = "dataset"
    logger.info("Starting scraping process...")
    
    # Run the async process
    asyncio.run(process_urls(urls, output_dir))
    logger.info("Scraping process completed.")