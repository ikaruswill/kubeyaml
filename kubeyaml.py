import sys
import argparse
from ruamel.yaml import YAML

def parse_args():
    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    image = subparsers.add_parser('image', help='update an image ref')
    image.add_argument('--namespace', required=True)
    image.add_argument('--kind', required=True)
    image.add_argument('--name', required=True)
    image.add_argument('--container', required=True)
    image.add_argument('--image', required=True)
    image.set_defaults(func=update_image)

    def note(s):
        k, v = s.split('=')
        return k, v

    annotation = subparsers.add_parser('annotate', help='update annotations')
    annotation.add_argument('--namespace', required=True)
    annotation.add_argument('--kind', required=True)
    annotation.add_argument('--name', required=True)
    annotation.add_argument('notes', nargs='+', type=note)
    annotation.set_defaults(func=update_annotations)

    return p.parse_args()

def bail(reason):
        sys.stderr.write(reason); sys.stderr.write('\n')
        sys.exit(2)

def update_image(args):
    yaml = YAML()
    yaml.explicit_start = True

    found = False
    for doc in yaml.load_all(sys.stdin):
        if not found:
            for m in manifests(doc):
                c = find_container(args, m)
                if c != None:
                    c['image'] = args.image
                    found = True
                    break
        yaml.dump(doc, sys.stdout)
    if not found:
        bail("Container not found")

def update_annotations(spec):
    yaml = YAML()
    yaml.explicit_start = True

    def ensure(d, *keys):
        for k in keys:
            try:
                d = d[k]
            except KeyError:
                d[k] = dict()
                d = d[k]
        return d

    found = False
    for doc in yaml.load_all(sys.stdin):
        if not found:
            for m in manifests(doc):
                if match_manifest(spec, m):
                    notes = ensure(m, 'metadata', 'annotations')
                    for k, v in spec.notes:
                        notes[k] = v
                    found = True
                    break
        yaml.dump(doc, sys.stdout)
    if not found:
        bail("Container not found")

def manifests(doc):
    if doc['kind'] == 'List':
        for m in doc['items']:
            yield m
    else:
        yield doc

def match_manifest(spec, manifest):
    try:
        # NB treat the Kind as case-insensitive
        if manifest['kind'].lower() != spec.kind.lower():
            return False
        if manifest['metadata']['namespace'] != spec.namespace:
            return False
        if manifest['metadata']['name'] != spec.name:
            return False
    except KeyError:
        return False
    return True
        
def find_container(spec, manifest):
    if not match_manifest(spec, manifest):
        return None
    for c in manifest['spec']['template']['spec']['containers']:
        if c['name'] == spec.container:
            return c
    return None

def main():
    args = parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
