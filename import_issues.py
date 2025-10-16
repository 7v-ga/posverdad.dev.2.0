#!/usr/bin/env python3
import os, csv, argparse, requests, sys

API = "https://api.github.com"

def gh_headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Falta GITHUB_TOKEN (export GITHUB_TOKEN=...)", file=sys.stderr)
        sys.exit(1)
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

def ensure_labels(owner, repo, labels):
    # Crea labels inexistentes (color fijo si no existe). Quita espacios y vacíos.
    headers = gh_headers()
    existing = set()
    url = f"{API}/repos/{owner}/{repo}/labels?per_page=100"
    while url:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        for lab in r.json():
            existing.add(lab["name"])
        url = r.links.get("next", {}).get("url")
    for name in labels:
        if not name or name in existing: 
            continue
        # crea el label
        data = {"name": name, "color": "0366d6", "description": "auto-import"}
        requests.post(f"{API}/repos/{owner}/{repo}/labels", headers=headers, json=data, timeout=30)

def milestone_number_by_title(owner, repo, title):
    if not title: 
        return None
    headers = gh_headers()
    # Buscar milestone por título (abierto y cerrado)
    for state in ("open","closed"):
        r = requests.get(f"{API}/repos/{owner}/{repo}/milestones",
                         headers=headers, params={"state": state, "per_page": 100}, timeout=30)
        r.raise_for_status()
        for m in r.json():
            if m["title"] == title:
                return m["number"]
    # No encontrado → None (evitamos crearlo automáticamente para no ensuciar)
    return None

def create_issue(owner, repo, title, body, labels, milestone_num):
    headers = gh_headers()
    payload = {"title": title}
    if body: payload["body"] = body
    if labels: payload["labels"] = labels
    if milestone_num is not None: payload["milestone"] = milestone_num
    r = requests.post(f"{API}/repos/{owner}/{repo}/issues", headers=headers, json=payload, timeout=30)
    if r.status_code >= 300:
        print(f"❌ Error creando issue '{title[:60]}...': {r.status_code} {r.text}")
    else:
        url = r.json().get("html_url")
        print(f"✅ Creado: {url}")

def main():
    p = argparse.ArgumentParser(description="Importar issues desde CSV a GitHub")
    p.add_argument("--owner", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("csv_path")
    p.add_argument("--create-missing-labels", action="store_true",
                   help="Crea labels que no existan en el repo.")
    args = p.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Columnas esperadas: Title, Body, Labels, Milestone
        rows = list(reader)

    # Recolecta set de labels
    all_labels = set()
    for row in rows:
        labels = [x.strip() for x in (row.get("Labels") or "").split(",") if x.strip()]
        all_labels.update(labels)

    if args.create_missing_labels and all_labels:
        ensure_labels(args.owner, args.repo, sorted(all_labels))

    # Cache de milestones por título
    ms_cache = {}
    for row in rows:
        title = (row.get("Title") or "").strip()
        if not title:
            continue
        body = row.get("Body") or ""
        labels = [x.strip() for x in (row.get("Labels") or "").split(",") if x.strip()]
        ms_title = (row.get("Milestone") or "").strip()
        if ms_title not in ms_cache:
            ms_cache[ms_title] = milestone_number_by_title(args.owner, args.repo, ms_title)
        create_issue(args.owner, args.repo, title, body, labels, ms_cache[ms_title])

if __name__ == "__main__":
    main()
