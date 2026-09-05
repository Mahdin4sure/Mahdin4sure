#!/usr/bin/env python3
"""
Generate GitHub activity graph as SVG from contribution calendar.
Queries GitHub GraphQL API for last 26 weeks of contributions.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

GITHUB_API = "https://api.github.com/graphql"
TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("USERNAME", "mahdin4sure")

# Tokyo Night Theme Colors
THEME = {
    "background": "#1a1b26",
    "line": "#7aa2f7",           # Blue
    "area_start": "#7aa2f7",     # Blue (start of gradient)
    "area_end": "#7aa2f7",       # Blue (end of gradient)
    "point": "#7aa2f7",          # Blue
    "axis": "#414868",           # Dark gray
    "text": "#a9b1d6",           # Light gray
}

def get_contributions():
    """Fetch contribution data from GitHub GraphQL API."""
    query = """
    query($userName:String!) {
      user(login: $userName) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    
    variables = {"userName": USERNAME}
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "query": query,
        "variables": variables,
    }
    
    try:
        response = requests.post(GITHUB_API, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            print(f"GraphQL Error: {data['errors']}", file=sys.stderr)
            sys.exit(1)
        
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        
        # Flatten weeks into days and aggregate by week
        all_days = []
        for week in weeks:
            for day in week["contributionDays"]:
                all_days.append({
                    "date": day["date"],
                    "count": day["contributionCount"]
                })
        
        return all_days
    
    except requests.RequestException as e:
        print(f"Request Error: {e}", file=sys.stderr)
        sys.exit(1)

def aggregate_by_week(days):
    """Aggregate daily contributions into weekly totals."""
    weeks = {}
    for day in days:
        date = datetime.strptime(day["date"], "%Y-%m-%d")
        week_start = date - timedelta(days=date.weekday())
        week_key = week_start.strftime("%Y-%m-%d")
        
        if week_key not in weeks:
            weeks[week_key] = 0
        weeks[week_key] += day["count"]
    
    return sorted(weeks.items())

def generate_svg(weekly_data):
    """Generate SVG with area chart of weekly contributions."""
    if not weekly_data:
        return generate_empty_svg()
    
    weeks_list = [int(count) for _, count in weekly_data]
    max_contributions = max(weeks_list) if weeks_list else 1
    
    # SVG dimensions
    width = 880
    height = 200
    padding = 40
    chart_width = width - (padding * 2)
    chart_height = height - (padding * 2)
    
    # Calculate points
    num_weeks = len(weeks_list)
    x_step = chart_width / (num_weeks - 1) if num_weeks > 1 else chart_width
    
    points = []
    for i, count in enumerate(weeks_list):
        x = padding + (i * x_step)
        y = height - padding - (count / max_contributions) * chart_height
        points.append((x, y))
    
    # Build path strings
    line_points = " ".join([f"{x},{y}" for x, y in points])
    
    # Area path: line + down to baseline + back
    area_points = " ".join([f"{x},{y}" for x, y in points])
    area_path = f"M {area_points} L {points[-1][0]},{height - padding} L {points[0][0]},{height - padding} Z"
    
    # Generate SVG with tokyo-night theme
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:{THEME['area_start']};stop-opacity:0.3" />
      <stop offset="100%" style="stop-color:{THEME['area_end']};stop-opacity:0.05" />
    </linearGradient>
    <style>
      @keyframes draw {{
        from {{ stroke-dashoffset: 1000; }}
        to {{ stroke-dashoffset: 0; }}
      }}
      .line {{ animation: draw 1.5s ease-in-out; stroke-dasharray: 1000; }}
    </style>
  </defs>
  
  <!-- Background -->
  <rect width="{width}" height="{height}" fill="{THEME['background']}"/>
  
  <!-- Area -->
  <path d="{area_path}" fill="url(#areaGradient)" />
  
  <!-- Line -->
  <polyline points="{line_points}" stroke="{THEME['line']}" stroke-width="2" fill="none" class="line" />
  
  <!-- Points -->
"""
    
    for x, y in points:
        svg += f'  <circle cx="{x}" cy="{y}" r="3" fill="{THEME["point"]}" />\n'
    
    svg += f"""
  <!-- Axes -->
  <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="{THEME['axis']}" stroke-width="1" />
  <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" stroke="{THEME['axis']}" stroke-width="1" />
  
  <!-- Labels -->
  <text x="{width / 2}" y="{height - 10}" text-anchor="middle" fill="{THEME['text']}" font-size="12" font-family="monospace">
    Last 26 weeks of contributions
  </text>
</svg>"""
    
    return svg

def generate_empty_svg():
    """Generate placeholder SVG when no data."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="880" height="200" viewBox="0 0 880 200" xmlns="http://www.w3.org/2000/svg">
  <rect width="880" height="200" fill="{THEME['background']}"/>
  <text x="440" y="100" text-anchor="middle" fill="{THEME['text']}" font-size="14" font-family="monospace">
    Loading contribution data...
  </text>
</svg>"""

def main():
    """Main entry point."""
    print(f"Fetching contributions for {USERNAME}...", file=sys.stderr)
    
    days = get_contributions()
    print(f"Got {len(days)} days of data", file=sys.stderr)
    
    weekly = aggregate_by_week(days)
    print(f"Aggregated into {len(weekly)} weeks", file=sys.stderr)
    
    svg = generate_svg(weekly)
    
    os.makedirs(".", exist_ok=True)
    with open("activity-graph.svg", "w") as f:
        f.write(svg)
    
    print("✓ Generated activity-graph.svg", file=sys.stderr)

if __name__ == "__main__":
    main()
