import requests
from bs4 import BeautifulSoup
import pandas as pd

def fetch_results(team_id, test=False):
    if test:
        url =  "https://wisemanp.github.io/graveyardswiftresults/results.csv"
        data = pd.read_csv(url)
        print('got data from github', data)
        return data.to_dict(orient='records')
    else:
        #url = f"https://results.resultsbase.net/myresults.aspx?CId=8&RId=20854&EId=1&AId={team_id}"
        url = 'dummy'
    print('Fetching results from:', url)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []  # Return empty results if request fails

    soup = BeautifulSoup(html, "html.parser")
    
    # Extract table data
    tables = soup.find_all("table", class_="table table-bordered table-sm small")
    print('Found tables:', len(tables))
    if not tables:
        print("No results table found for this team_id.")
        return []  # Return empty results if no table found

    target_table = tables[0]
    rows = target_table.find_all("tr")
    
    data = []
    for row in rows[1:]:  # Skip header
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        name_raw = cols[0].get_text(separator="\n").strip()
        leg_label, name = name_raw.split("\n") if "\n" in name_raw else (name_raw, "")
        leg_time = cols[2].get_text(strip=True)
        data.append({
            "Lap": leg_label.replace("Lap ", "").strip(),
            "Runner": name.strip("() "),
            "Leg Time": leg_time
        })
    
    print('GOT DATA', data)
    return pd.DataFrame(data).to_dict(orient='records')