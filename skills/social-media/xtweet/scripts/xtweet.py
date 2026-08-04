#!/usr/bin/env python3
"""xtweet - Read any X/Twitter post by ID or URL for free (no API key, no login).

Usage:
    python3 xtweet.py <TWEET_ID_or_URL> [--json] [--media]
"""
import json, subprocess, sys, re

def extract_id(arg):
    m = re.search(r'(\d{10,})', arg)
    return m.group(1) if m else arg.strip()

def fetch(tid):
    r = subprocess.run(["curl","-s","-m15",f"https://api.fxtwitter.com/i/status/{tid}"],
                       capture_output=True, text=True)
    return json.loads(r.stdout)

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    tid = extract_id(sys.argv[1])
    d = fetch(tid)
    if d.get("code") != 200:
        print("ERROR:", d.get("message", "unknown")); sys.exit(1)
    t = d["tweet"]
    if "--json" in sys.argv:
        print(json.dumps(t, indent=2)); return
    a = t["author"]
    print(f"AUTHOR: {a['name']} @{a['screen_name']}")
    print(f"DATE:   {t['created_at']}")
    print(f"LIKES:  {t['likes']} | REPLIES: {t['replies']} | RT: {t['retweets']} | VIEWS: {t['views']}")
    print(f"LANG:   {t.get('lang')}")
    print("--- TEXT ---")
    print(t["text"])
    if "--media" in sys.argv:
        print("--- MEDIA ---")
        for m in t.get("media", {}).get("all", []):
            print(m["type"], m["url"])

if __name__ == "__main__":
    main()
