import requests
from bs4 import BeautifulSoup
import re

def debug_fetch_chapters():
    """Debug version of the fetch_chapters function"""
    try:
        url = "https://olympustaff.com/team/straw-hat"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"🔍 Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"✅ Response status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Debug: Print different possible selectors
        print("\n🔍 Looking for list items...")
        
        # Try the original selector
        items1 = soup.select("ol.list-group > li")
        print(f"Original selector 'ol.list-group > li': Found {len(items1)} items")
        
        # Try alternative selectors
        items2 = soup.select("ol li")
        print(f"Alternative selector 'ol li': Found {len(items2)} items")
        
        items3 = soup.select("li")
        print(f"All li elements: Found {len(items3)} items")
        
        items4 = soup.select(".list-group li")
        print(f"Selector '.list-group li': Found {len(items4)} items")
        
        # Let's examine the structure
        print("\n🔍 Looking for common manga-related elements...")
        
        # Look for any elements that might contain manga titles
        titles = soup.find_all(text=re.compile(r"Devil|Summoner|Thunder|Fox|Villain", re.IGNORECASE))
        print(f"Text containing manga keywords: {len(titles)} found")
        for i, title in enumerate(titles[:5]):
            print(f"  {i+1}: {title.strip()}")
        
        # Look for chapter-related elements
        chapters = soup.find_all(text=re.compile(r"Chapter|الفصل|ch", re.IGNORECASE))
        print(f"Text containing chapter keywords: {len(chapters)} found")
        for i, chap in enumerate(chapters[:5]):
            print(f"  {i+1}: {chap.strip()}")
        
        # Try to find the main content area
        main_content = soup.find("main") or soup.find("div", class_="container") or soup.find("div", class_="content")
        if main_content:
            print(f"\n🔍 Found main content area")
            # Look for any structured lists within main content
            lists = main_content.find_all(["ol", "ul"])
            print(f"Lists in main content: {len(lists)}")
            for i, lst in enumerate(lists):
                print(f"  List {i+1}: {lst.get('class', 'no class')} - {len(lst.find_all('li'))} items")
        
        return []
        
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
        return []
    except Exception as e:
        print(f"❌ Parsing error: {e}")
        return []

if __name__ == "__main__":
    debug_fetch_chapters()