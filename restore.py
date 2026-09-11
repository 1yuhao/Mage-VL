#!/usr/bin/env python3
"""Verify all parts and restore Mage-VL, using only Python's standard library."""
import argparse, hashlib, io, json, pathlib, shutil, tarfile
ROOT = pathlib.Path(__file__).resolve().parent

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

class PartsReader(io.RawIOBase):
    def __init__(self, parts):
        self.parts = iter(parts)
        self.current = None
    def read(self, size=-1):
        if size < 0:
            raise ValueError('Streaming reads must be bounded')
        result = bytearray()
        while len(result) < size:
            if self.current is None:
                path = next(self.parts, None)
                if path is None:
                    break
                self.current = path.open('rb')
            block = self.current.read(size - len(result))
            if block:
                result.extend(block)
            else:
                self.current.close()
                self.current = None
        return bytes(result)
    def close(self):
        if self.current:
            self.current.close()
        super().close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=pathlib.Path, default=ROOT / 'restored')
    parser.add_argument('--verify-only', action='store_true', help='Verify parts and archive contents without extracting')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for part in manifest['parts']:
        path = ROOT / part['path']
        if path.stat().st_size != part['size'] or digest(path) != part['sha256']:
            raise ValueError(f'Corrupt part: {path}')
    print('All parts verified.', flush=True)
    expected = {'Mage-VL/' + f['path']: f for f in manifest['files']}
    seen = set()
    if not args.verify_only:
        args.output.mkdir(parents=True, exist_ok=True)
        if (args.output / 'Mage-VL').exists():
            raise FileExistsError('Output Mage-VL directory already exists; choose a new --output directory')
    with PartsReader([ROOT / p['path'] for p in manifest['parts']]) as reader:
        with tarfile.open(fileobj=reader, mode='r|') as archive:
            for member in archive:
                pure = pathlib.PurePosixPath(member.name)
                if member.name not in expected or member.name in seen or not member.isfile() or pure.is_absolute() or '..' in pure.parts:
                    raise ValueError(f'Unexpected archive entry: {member.name}')
                record = expected[member.name]
                if member.size != record['size']:
                    raise ValueError(f'Wrong size: {member.name}')
                target = args.output.joinpath(*pure.parts)
                out = None
                try:
                    if not args.verify_only:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        out = target.open('xb')
                    h = hashlib.sha256()
                    with archive.extractfile(member) as source:
                        for block in iter(lambda: source.read(8 * 1024 * 1024), b''):
                            h.update(block)
                            if out:
                                out.write(block)
                    if h.hexdigest() != record['sha256']:
                        raise ValueError(f'Corrupt model file: {member.name}')
                finally:
                    if out:
                        out.close()
                seen.add(member.name)
    if seen != set(expected):
        raise ValueError('Archive is incomplete')
    print(f'All {len(seen)} model files verified.' if args.verify_only else f'Restored and verified: {args.output.resolve() / "Mage-VL"}')

if __name__ == '__main__':
    main()
