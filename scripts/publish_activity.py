"""Validate the whole refresh before replacing any last-known-good assets."""
from datetime import datetime, timezone
from pathlib import Path
import re
import xml.etree.ElementTree as ET
root = Path(__file__).resolve().parents[1]
staged = {}
for name in ('stats.svg', 'snake.svg'):
    source = (root / '.generated' / name).read_text(encoding='utf-8')
    doc = ET.fromstring(source)
    if doc.tag != '{http://www.w3.org/2000/svg}svg':
        raise ValueError(f'{name}: not SVG')
    if 'something went wrong' in source.lower() or 'could not fetch' in source.lower():
        visible_text = ' '.join(''.join(node.itertext()) for node in doc.iter() if node.tag.endswith('}text'))
        raise ValueError(f'{name}: upstream error card: {visible_text}')
    if name == 'snake.svg':
        x, y, width, height = doc.attrib['viewBox'].split()
        background = f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="#090B0A"/>'
        end = source.index('>') + 1
        source = source[:end] + background + source[end:]
        source = source.replace('</svg>', '<style>@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style></svg>')
    staged[name] = source
readme_path = root / 'README.md'
readme = readme_path.read_text(encoding='utf-8')
stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
readme, count = re.subn(r'<!-- activity-date -->.*?<!-- /activity-date -->', f'<!-- activity-date -->Updated {stamp} UTC<!-- /activity-date -->', readme)
if count != 1:
    raise ValueError('Expected exactly one update-date marker')
for name, source in staged.items():
    (root / 'assets' / name).write_text(source, encoding='utf-8')
readme_path.write_text(readme, encoding='utf-8')
print('Validated both assets and updated activity date.')
