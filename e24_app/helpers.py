import requests
from bs4 import BeautifulSoup
import pandas as pd

def fetch_results(team_id, test=False):
    if test:
        url = "https://results.resultsbase.net/myresults.aspx?CId=8&RId=20442&EId=1&AId=539296"
    else:
        url = f"https://results.resultsbase.net/myresults.aspx?CId=8&RId=20854&EId=1&AId={team_id}"
    print('Fetching results from:', url)
    response = requests.get(url)
    print(response.status_code, response.reason,response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract table data
    tables = soup.find_all("table", class_="table table-bordered table-sm small")
    print('Found tables:', len(tables))
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
    
    # If this is a test, limit the data to simulate halfway-through-the-race
    #if test:
        #halfway_index = len(data) // 2
        #data = data[:halfway_index]
    print('GOT DATA', data)
    return pd.DataFrame(data).to_dict(orient='records')