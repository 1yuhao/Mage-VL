import json, os, pathlib, subprocess, urllib.request
from huggingface_hub import snapshot_download
repo = pathlib.Path(__file__).resolve().parents[1]
base = pathlib.Path(os.environ['MAGE_WORK_DIR'])
base.mkdir(parents=True, exist_ok=True)
revision = 'd88b153285f1633a61b2f693c59c8576693af185'
url = f'https://huggingface.co/api/models/microsoft/Mage-VL/revision/{revision}?blobs=true'
with urllib.request.urlopen(url, timeout=60) as response:
    manifest = json.load(response)
assert manifest['sha'] == revision
(base / 'source-manifest.json').write_text(json.dumps(manifest))
snapshot_download('microsoft/Mage-VL', revision=revision, local_dir=base / 'model', max_workers=4)
subprocess.run(['python', str(repo / 'scripts/package_model.py')], check=True)
subprocess.run(['python', str(repo / 'restore.py'), '--verify-only'], check=True)

def git(*args):
    subprocess.run(['git', '-C', str(repo), *args], check=True)

# Keep every push comfortably below GitHub's per-push size limit.
git('config', 'user.name', 'github-actions[bot]')
git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
git('config', 'pack.threads', '2')
git('config', 'pack.window', '0')
git('config', 'gc.auto', '0')
parts = sorted((repo / 'parts').glob('mage-vl.tar.part*'))
for offset in range(0, len(parts), 8):
    batch = parts[offset:offset+8]
    git('add', *[str(p.relative_to(repo)) for p in batch])
    if subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--quiet']).returncode:
        git('commit', '-m', f'Add model parts {offset+1}-{offset+len(batch)} of {len(parts)}')
        git('push', 'origin', 'HEAD:main')
    print(f'Uploaded {offset+len(batch)}/{len(parts)} parts', flush=True)
git('add', 'manifest.json', 'SHA256SUMS')
if subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--quiet']).returncode:
    git('commit', '-m', 'Publish verified model manifest and checksums')
    git('push', 'origin', 'HEAD:main')
print('All model parts and manifest published.', flush=True)
