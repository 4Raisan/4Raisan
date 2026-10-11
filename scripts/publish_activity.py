"""Validate both cards before publishing a synchronized snapshot."""
from pathlib import Path
import json, re
import xml.etree.ElementTree as ET
root = Path(__file__).resolve().parents[1]
calendar = json.loads((root/'.generated/calendar.json').read_text(encoding='utf-8'))
staged = {}
for name in ('stats.svg','snake.svg'):
    source = (root/'.generated'/name).read_text(encoding='utf-8')
    doc = ET.fromstring(source)
    if doc.tag != '{http://www.w3.org/2000/svg}svg':
        raise ValueError('Invalid SVG')
    if name == 'snake.svg':
        expected = [f'{d["date"]}: {d["contributionCount"]} contributions' for w in calendar['weeks'] for d in w['contributionDays']]
        actual = [n.text for n in doc.iter('{http://www.w3.org/2000/svg}title')][1:]
        if actual != expected or '<animate' in source:
            raise ValueError('Calendar cells mismatch')
    staged[name] = source
path = root/'README.md'
readme, count = re.subn(r'<!-- activity-date -->.*?<!-- /activity-date -->', '<!-- activity-date -->Updated '+calendar['refreshedAt']+'<!-- /activity-date -->',path.read_text(encoding='utf-8'))
if count != 1:
    raise ValueError('Expected one date marker')
for name,source in staged.items():
    (root/'assets'/name).write_text(source,encoding='utf-8')
path.write_text(readme,encoding='utf-8')
print('Validated both cards:',calendar['totalContributions'],'contributions')
