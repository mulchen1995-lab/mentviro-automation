#!/usr/bin/env python3
"""
Run this script LOCALLY (from your home network, NOT from a server or VPN)
to generate a saved Instagram session that GitHub Actions can reuse.

Usage:
    pip install instagrapi
    python automation/generate_session.py

Then copy the printed JSON and add it as GitHub Secret 'IG_SESSION'.
"""
import json, getpass, sys
from instagrapi import Client

username = input("Instagram username [mentviro]: ").strip() or "mentviro"
password = getpass.getpass("Instagram password: ")

print(f"\nLogging in as @{username} ...")
cl = Client()
cl.delay_range = [1, 3]

try:
    cl.login(username, password)
except Exception as e:
    print(f"Login failed: {e}")
    sys.exit(1)

session = cl.get_settings()
session_json = json.dumps(session)

print("\n" + "=" * 60)
print("SUCCESS — copy the line below as GitHub Secret 'IG_SESSION':")
print("=" * 60)
print(session_json)
print("=" * 60 + "\n")

out_path = "ig_session.json"
with open(out_path, "w") as f:
    json.dump(session, f, indent=2)
print(f"Also saved to {out_path}  ← DO NOT commit this file!")
print("Add ig_session.json to .gitignore if it isn't already.")
