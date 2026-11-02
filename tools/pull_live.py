#!/usr/bin/env python3
"""GitHub Actions step: read the live posts JSON from the private Notion page,
check it, lock it with the data key and write live.enc.json.

Env: NOTION_TOKEN, EDV_DATA_KEY (repo secrets), NOTION_PAGE_ID.
Writes live.enc.json and live.sha only when the data changed."""
import hashlib, json, os, sys, tempfile, urllib.request, subprocess

page = os.environ["NOTION_PAGE_ID"].replace("-", "")
req = urllib.request.Request(f"https://api.notion.com/v1/blocks/{page}/children?page_size=100",
    headers={"Authorization": "Bearer " + os.environ["NOTION_TOKEN"], "Notion-Version": "2022-06-28"})
blocks = json.load(urllib.request.urlopen(req, timeout=30))["results"]
code = next((b for b in blocks if b.get("type") == "code"), None)
if not code:
    sys.exit("no code block on the Notion page")
raw = "".join(t.get("plain_text", "") for t in code["code"]["rich_text"]).strip()
data = json.loads(raw)
assert isinstance(data.get("days"), dict), "days must be an object"
for d, v in data["days"].items():
    assert isinstance(v.get("posts", []), list)
    for p in v.get("posts", []):
        assert "dt" in p and "nets" in p, "post needs dt and nets"
        p.pop("u", None)
        for n in p["nets"]:
            n.pop("u", None)  # never publish links
canon = json.dumps(data, sort_keys=True, ensure_ascii=False)
sha = hashlib.sha256(canon.encode()).hexdigest()
old = open("live.sha").read().strip() if os.path.exists("live.sha") else ""
if sha == old:
    print("no change"); sys.exit(0)
with tempfile.TemporaryDirectory() as t:
    k, p = os.path.join(t, "k"), os.path.join(t, "live.json")
    open(k, "w").write(os.environ["EDV_DATA_KEY"].strip())
    open(p, "w").write(canon)
    subprocess.run([sys.executable, "tools/edv.py", "lock", k, p, "live.enc.json"], check=True)
open("live.sha", "w").write(sha + "\n")
print("updated", data.get("updatedAt"))
