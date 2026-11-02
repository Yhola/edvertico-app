#!/usr/bin/env python3
"""GitHub Actions step. Copies the locked update (EDV1....) that the Edvertico
autopilot writes to a Notion page published to the web into live.enc.json.
The robot never unlocks it and needs no key: only the app unlocks it for
signed-in users. Env: NOTION_PAGE_ID."""
import datetime, hashlib, json, os, re, sys, urllib.request

pid = os.environ["NOTION_PAGE_ID"].replace("-", "")
pid = f"{pid[:8]}-{pid[8:12]}-{pid[12:16]}-{pid[16:20]}-{pid[20:]}"
body = json.dumps({"pageId": pid, "limit": 100, "cursor": {"stack": []}, "chunkNumber": 0, "verticalColumns": False}).encode()
req = urllib.request.Request("https://www.notion.so/api/v3/loadPageChunk", data=body,
                             headers={"content-type": "application/json", "user-agent": "edvertico-bot"})
blocks = json.load(urllib.request.urlopen(req, timeout=30)).get("recordMap", {}).get("block", {})
if not blocks:
    sys.exit("Notion page is not published to the web")
text = ""
for b in blocks.values():
    v = b.get("value", {}); v = v.get("value", v)
    if v.get("type") == "code":
        text = "".join(seg[0] for seg in v.get("properties", {}).get("title", []) if seg); break
m = re.search(r"EDV1\.[A-Za-z0-9_\-]{16}\.[A-Za-z0-9_\-\s]{40,}", text)
if not m:
    sys.exit("no EDV1 pack in the code block")
pack = "".join(m.group(0).split())
sha = hashlib.sha256(pack.encode()).hexdigest()
if os.path.exists("live.sha") and open("live.sha").read().strip() == sha:
    print("no change"); sys.exit(0)
json.dump({"v": 2, "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "pack": pack}, open("live.enc.json", "w"))
open("live.sha", "w").write(sha + "\n")
print("updated", len(pack), "chars")
