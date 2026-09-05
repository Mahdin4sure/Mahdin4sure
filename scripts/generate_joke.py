#!/usr/bin/env python3
"""
Generate a random dev joke as SVG.
Fetches from public joke API and renders as SVG with Q&A format.
"""

import os
import requests
import textwrap
from datetime import datetime

JOKE_API = "https://official-joke-api.appspot.com/jokes/programming/random"

def fetch_joke():
    """Fetch a random programming joke from the API."""
    try:
        response = requests.get(JOKE_API, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Handle both single joke and array responses
        if isinstance(data, list):
            data = data[0]
        
        return {
            "setup": data.get("setup", ""),
            "punchline": data.get("punchline", ""),
            "type": data.get("type", "general")
        }
    except requests.RequestException as e:
        print(f"Error fetching joke: {e}")
        return {
            "setup": "Why did the developer go broke?",
            "punchline": "Because he lost his cache!",
            "type": "programming"
        }

def wrap_text(text, max_width=60):
    """Wrap text to fit in SVG."""
    return textwrap.fill(text, width=max_width)

def generate_svg(joke):
    """Generate SVG with joke content."""
    setup = joke["setup"]
    punchline = joke["punchline"]
    
    # Wrap text
    setup_wrapped = wrap_text(setup, max_width=55)
    punchline_wrapped = wrap_text(punchline, max_width=55)
    
    # Count lines for sizing
    setup_lines = setup_wrapped.count('\n') + 1
    punchline_lines = punchline_wrapped.count('\n') + 1
    
    height = 120 + (setup_lines * 25) + (punchline_lines * 25)
    width = 800
    
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .border {{ stroke: #40c463; stroke-width: 2; fill: none; }}
      .setup-text {{ font-family: monospace; font-size: 14px; fill: #79c0ff; font-weight: bold; }}
      .answer-text {{ font-family: monospace; font-size: 14px; fill: #3fb950; }}
      .label {{ font-family: monospace; font-size: 12px; fill: #8b949e; }}
    </style>
  </defs>
  
  <!-- Background -->
  <rect width="{width}" height="{height}" fill="#0d1117"/>
  
  <!-- Border -->
  <rect x="20" y="20" width="{width - 40}" height="{height - 40}" class="border" rx="8"/>
  
  <!-- Q Label -->
  <text x="40" y="55" class="label">Q.</text>
  
  <!-- Setup (Question) -->
"""
    
    y_offset = 55
    for i, line in enumerate(setup_wrapped.split('\n')):
        y_offset += 25
        svg += f'  <text x="70" y="{y_offset}" class="setup-text">{line}</text>\n'
    
    y_offset += 20
    svg += f'  <text x="40" y="{y_offset}" class="label">A.</text>\n'
    
    y_offset += 5
    for i, line in enumerate(punchline_wrapped.split('\n')):
        y_offset += 25
        svg += f'  <text x="70" y="{y_offset}" class="answer-text">{line}</text>\n'
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    svg += f'  <text x="{width - 40}" y="{height - 20}" text-anchor="end" class="label">Updated: {timestamp}</text>\n'
    
    svg += "</svg>"
    
    return svg

def main():
    """Main entry point."""
    print("Fetching dev joke...", flush=True)
    
    joke = fetch_joke()
    print(f"Q: {joke['setup']}", flush=True)
    print(f"A: {joke['punchline']}", flush=True)
    
    svg = generate_svg(joke)
    
    os.makedirs(".", exist_ok=True)
    with open("dev-joke.svg", "w") as f:
        f.write(svg)
    
    print("✓ Generated dev-joke.svg", flush=True)

if __name__ == "__main__":
    main()
