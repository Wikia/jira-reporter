from pathlib import Path

import re
from reporter.bin.update_classifier_config import  _write_to_yaml

if __name__ == '__main__':
    ucp_dir = '../unified-platform/'
    regex = re.compile(r"product_person\s*=\s\"(.+)\"")
    owners = {}

    for path in Path(ucp_dir).rglob('crowdin.conf'):
        relative = path.relative_to(ucp_dir)
        if str(relative).startswith('node_modules/'):
            continue
        contents = Path(path).read_text()
        p = regex.findall(contents, re.MULTILINE)
        if len(p) == 1:
            owners[str(relative.parent)] = p[0]

    _write_to_yaml('ucp_owners', owners)