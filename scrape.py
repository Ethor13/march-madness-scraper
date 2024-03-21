from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import pandas as pd
import datetime as dt

URL = "https://fantasy.espn.com/games/tournament-challenge-bracket-2024/group?id=c1064818-9468-4f96-8790-0059bca6d386"


def get_entries(wd):
    entry_table = wd.find_element(By.CLASS_NAME, "Table__TBODY")

    entries = []
    for entry in entry_table.find_elements(By.TAG_NAME, "tr"):
        entry_info = [td.text for td in entry.find_elements(By.TAG_NAME, "td")]
        entries.append(entry_info)

    return entries


driver_path = EdgeChromiumDriverManager(path=".").install()
driver = webdriver.Edge(service=Service(driver_path))

driver.get(URL)
driver.implicitly_wait(10)
entries = get_entries(driver)
driver.close()

df = pd.DataFrame(
    entries,
    columns=[
        "rank",
        "champ",
        "entry_id",
        "current_points",
        "percentile",
        "maximum",
        "round_score",
    ],
)

split = df.entry_id.str.split("\n")
df.loc[:, "entry_name"] = split.map(lambda lst: lst[0])
df.loc[:, "entry_user"] = split.map(lambda lst: lst[1])

now = dt.datetime.now().strftime(r"%Y-%m-%d %H:00:00")
df.loc[:, "time"] = now

fname = dt.datetime.now().strftime(r"%Y_%m_%d_%H")
df.loc[
    :,
    [
        "time",
        "entry_name",
        "entry_user",
        "current_points",
        "maximum",
        "round_score",
        "rank",
        "percentile",
    ],
].to_csv(f"outputs/{fname}.csv", index=False)
