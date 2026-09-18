"""Validate the whole refresh before replacing any last-known-good assets."""
from datetime import datetime, timezone
from pathlib import Path
import re
import json
from calendar import month_abbr
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
        weeks = json.loads((root / '.generated' / 'calendar.json').read_text(encoding='utf-8'))['weeks']
        cells = [n for n in doc if 'c' in n.get('class', '').split()]
        columns = sorted({float(n.attrib['x']) for n in cells})
        if len(columns) != len(weeks) or len(cells) != sum(len(w['contributionDays']) for w in weeks):
            raise ValueError('Snake and calendar dates do not match; preserving previous assets')
        first = weeks[0]['contributionDays'][0]['date']
        last = weeks[-1]['contributionDays'][-1]['date']
        years = first[:4] if first[:4] == last[:4] else first[:4] + '–' + last[:4]
        labels = f'<g font-family="Arial,Helvetica,sans-serif"><text x="2" y="-42" fill="#A7CDBB" font-size="18">Contributions · {years}</text>'
        previous_month = None
        for column, week in zip(columns, weeks):
            # A month starts at the column containing its first day, as on GitHub.
            days = week['contributionDays']
            boundary = next((d['date'] for d in days if d['date'].endswith('-01')), None)
            date = boundary or days[0]['date']
            month = date[:7]
            if month != previous_month:
                # Leave enough room for a three-letter month at the right edge.
                if column <= columns[-1] - 28:
                    labels += f'<text x="{column:g}" y="-10" fill="#A5AEA8" font-size="16">{month_abbr[int(date[5:7])]}</text>'
                previous_month = month
        labels += '</g>'
        x, y, width, height = map(float, doc.attrib['viewBox'].split())
        y -= 32
        height += 32
        source = re.sub(r'viewBox="[^"]+"', f'viewBox="{x:g} {y:g} {width:g} {height:g}"', source, count=1)
        source = re.sub(r'height="[^"]+"', f'height="{height:g}"', source, count=1)
        background = f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" rx="14" fill="#090B0A"/>'
        end = source.index('>') + 1
        source = source[:end] + background + source[end:]
        source = source.replace('</svg>', labels + '<style>@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style></svg>')
        ET.fromstring(source)
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
