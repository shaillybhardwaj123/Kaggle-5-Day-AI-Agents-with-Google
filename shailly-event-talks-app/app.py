import os
import time
import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, render_template, request
from bs4 import BeautifulSoup

app = Flask(__name__)

# Constants
FEED_URL = "https://docs.cloud.google.com/feeds/bigquery-release-notes.xml"
CACHE_DURATION = 600  # 10 minutes cache

# Simple in-memory cache
cache = {
    "data": None,
    "last_fetched": 0
}

def parse_feed_content(xml_content):
    """
    Parses the BigQuery release notes Atom feed and structures it.
    """
    # Atom namespace
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    
    root = ET.fromstring(xml_content)
    entries = []
    
    for entry_elem in root.findall("atom:entry", ns):
        # Extract metadata
        title = entry_elem.find("atom:title", ns)
        title_text = title.text.strip() if title is not None else "Unknown Date"
        
        updated = entry_elem.find("atom:updated", ns)
        updated_text = updated.text.strip() if updated is not None else ""
        
        link_elem = entry_elem.find("atom:link[@rel='alternate']", ns)
        if link_elem is None:
            link_elem = entry_elem.find("atom:link", ns)
        
        link_href = link_elem.attrib.get("href", "") if link_elem is not None else ""
        
        content_elem = entry_elem.find("atom:content", ns)
        content_html = content_elem.text if content_elem is not None else ""
        
        # Parse the HTML content to extract individual updates
        items = []
        if content_html:
            soup = BeautifulSoup(content_html, "html.parser")
            current_type = "Update"
            current_elements = []
            
            for child in soup.contents:
                # If it's a string, it might just be whitespace, but if it has text we keep it
                if isinstance(child, str):
                    if child.strip():
                        current_elements.append(child)
                    continue
                
                if child.name == "h3":
                    # Save the previous block if we accumulated anything
                    if current_elements:
                        body_html = "".join(str(c) for c in current_elements).strip()
                        if body_html:
                            # Clean text content for tweeting
                            temp_soup = BeautifulSoup(body_html, "html.parser")
                            # Replace link tags with text and href in parentheses for clarity
                            for a_tag in temp_soup.find_all('a'):
                                href = a_tag.get('href', '')
                                if href.startswith('/'):
                                    href = 'https://cloud.google.com' + href
                                a_tag.replace_with(f"{a_tag.get_text()} ({href})")
                            text_content = temp_soup.get_text().strip()
                            
                            items.append({
                                "type": current_type,
                                "content": body_html,
                                "text_content": text_content
                            })
                    # Reset for the new block
                    current_type = child.get_text().strip()
                    current_elements = []
                else:
                    current_elements.append(child)
            
            # Save the final block
            if current_elements:
                body_html = "".join(str(c) for c in current_elements).strip()
                if body_html:
                    temp_soup = BeautifulSoup(body_html, "html.parser")
                    for a_tag in temp_soup.find_all('a'):
                        href = a_tag.get('href', '')
                        if href.startswith('/'):
                            href = 'https://cloud.google.com' + href
                        a_tag.replace_with(f"{a_tag.get_text()} ({href})")
                    text_content = temp_soup.get_text().strip()
                    
                    items.append({
                        "type": current_type,
                        "content": body_html,
                        "text_content": text_content
                    })
        
        entries.append({
            "date": title_text,
            "updated": updated_text,
            "link": link_href,
            "items": items
        })
        
    return entries

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/release-notes")
def get_release_notes():
    force_refresh = request.args.get("refresh", "false").lower() == "true"
    current_time = time.time()
    
    # Check if we should use cache
    if not force_refresh and cache["data"] and (current_time - cache["last_fetched"] < CACHE_DURATION):
        return jsonify({
            "status": "success",
            "source": "cache",
            "last_updated": cache["last_fetched"],
            "data": cache["data"]
        })
        
    try:
        # Fetch external feed
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(FEED_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse xml
        release_notes = parse_feed_content(response.text)
        
        # Update cache
        cache["data"] = release_notes
        cache["last_fetched"] = current_time
        
        return jsonify({
            "status": "success",
            "source": "network",
            "last_updated": current_time,
            "data": release_notes
        })
    except Exception as e:
        # If network call fails but we have cached data, return cache with a warning
        if cache["data"]:
            return jsonify({
                "status": "warning",
                "message": f"Could not refresh feed: {str(e)}. Displaying cached data.",
                "source": "cache_fallback",
                "last_updated": cache["last_fetched"],
                "data": cache["data"]
            })
        return jsonify({
            "status": "error",
            "message": f"Error fetching release notes: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
