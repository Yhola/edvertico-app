#!/usr/bin/env python3
"""GitHub Actions step. Reads the locked update (EDV1....) that the Edvertico
autopilot writes to a Notion page published to the web, unlocks it to check it
is genuine, and re-locks it as live.enc.json for the app.

The Notion page only ever holds locked text, so publishing it is safe.
Env: EDV_DATA_KEY (repo secret), NOTION_PAGE_ID."""
import hashlib, json, os, re, sys, tempfile, urllib.request, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from edv import unpack_text, ub64

pid = os.environ["NOTION_PAGE_ID"].replace("-", "")
pid = f"{pid[:8]}-{pid[8:12]}-{pid[12:16]}-{pid[16:20]}-{pid[20:]}"
body = json.dumps({"pageId": pid, "limit": 100, "cursor": {"stack": []}, "chunkNumber": 0, "verticalColumns": False}).encode()
req = urllib.request.Request("https://www.notion.so/api/v3/loadPageChunk", data=body,
                             headers={"content-type": "application/json", "user-agent": "edvertico-bot"})
rec = json.load(urllib.request.urlopen(req, timeout=30)).get("recordMap", {})
blocks = rec.get("block", {})
if not blocks:
    sys.exit("Notion page is not published to the web (no blocks returned)")
text = ""
for b in blocks.values():
    v = b.get("value", {})
    v = v.get("value", v)
    if v.get("type") == "code":
        text = "".join(seg[0] for seg in v.get("properties", {}).get("title", []) if seg)
        break
m = re.search(r"EDV1\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-\s]+", text)
if not m:
    sys.exit("no EDV1 pack in the code block")
key = ub64(os.environ["EDV_DATA_KEY"].strip())
data = unpack_text(key, m.group(0))  # fails if the text was changed or damaged
assert isinstance(data.get("days"), dict), "days must be an object"
for d in data["days"].values():
    for p in d.get("posts", []):
        assert "dt" in p and "nets" in p, "post needs dt and nets"
        for n in p["nets"]:
            n.pop("u", None)
canon = json.dumps(data, sort_keys=True, ensure_ascii=False)
sha = hashlib.sha256(canon.encode()).hexdigest()
if os.path.exists("live.sha") and open("live.sha").read().strip() == sha:
    print("no change"); sys.exit(0)
with tempfile.TemporaryDirectory() as t:
    k, p = os.path.join(t, "k"), os.path.join(t, "live.json")
    open(k, "w").write(os.environ["EDV_DATA_KEY"].strip()); open(p, "w").write(canon)
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "edv.py"), "lock", k, p, "live.enc.json"], check=True)
open("live.sha", "w").write(sha + "\n")
print("updated", data.get("updatedAt"))
