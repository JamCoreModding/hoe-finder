from json import JSONDecodeError
from pathlib import Path
from sys import exit
import requests
from urllib.parse import urlencode
import json
import os

from datastructures import *

MAX_MODS = 2500
MOD_OFFSET = 2500
DEFAULT_HEADERS = {
    'User-Agent': 'JamCoreModding/hoe-finder <james[at]jamalam.tech> <discord:jamalam>'
}

def get_modrinth_project_ids():
    modrinth_mods = []

    for page in range(0, max(MAX_MODS // 100, 1)):
        query_params = {
            'offset': MOD_OFFSET + page * 100,
            'limit': 100,
            'facets': '[["project_type:mod"]]'
        }
        request = requests.get("https://api.modrinth.com/v2/search", params=query_params, headers=DEFAULT_HEADERS)
        if request.status_code != 200:
            print("Failed to fetch mods:", request.text)
            break

        modrinth_mods_json = json.loads(request.text)

        if not modrinth_mods_json['hits']:
            print("Failed to find mods:", modrinth_mods_json)
            break

        modrinth_mods.extend([mod['project_id'] for mod in modrinth_mods_json['hits']])

    return modrinth_mods

def get_project_download_url(project_id):
    query_params = {
        'loaders': ['fabric']
    }
    request = requests.get(f"https://api.modrinth.com/v2/project/{project_id}/version", params=query_params, headers=DEFAULT_HEADERS)

    if request.status_code != 200:
        print(f"Failed to fetch versions for project {project_id}")
        return None

    versions = json.loads(request.text)

    for version in versions:
        if "fabric" not in version['loaders']:
            continue
        return version['files'][0]['url']

    return None

def run():
    if Path('mod-sourcer').exists():
        mods_dir = Path('mod-sourcer/mods')
    else:
        mods_dir = Path('mods')

    if not mods_dir.exists():
        mods_dir.mkdir()

    modrinth_project_ids = get_modrinth_project_ids()
    print(f"Found {len(modrinth_project_ids)} mods")

    for idx, project_id in enumerate(modrinth_project_ids):
        download_url = get_project_download_url(project_id)
        if download_url is None:
            print("Failed to find download for project", project_id)
            continue

        print(f"Downloading {download_url} ({idx + 1}/{len(modrinth_project_ids)})")
        filename = download_url.split('/')[-1]

        try:
            with requests.get(download_url, stream=True) as request:
                request.raise_for_status()
                with open(mods_dir / filename, 'wb') as fh:
                    for chunk in request.iter_content(chunk_size=8192):
                        fh.write(chunk)
        except Exception as e:
            print(f"Failed to download {download_url} ({e})")
            continue

if __name__ == '__main__':
    run()