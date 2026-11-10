"""Validate and frame the original Platane/snk SVG and make eaten cells glow."""
import re
from calendar import month_abbr
import xml.etree.ElementTree as ET


def glow_styles(source, cells):
    # Reuse Platane's bite timing and override only the contribution keyframes.
    bites = {name: (before, color, after) for name, before, color, after in re.findall(
        r'@keyframes (c[0-9a-z]+)\{([\d.]+)%\{fill:(var\(--c[1-4]\))\}'
        r'([\d.]+)%,100%\{fill:var\(--ce\)\}\}', source)}
    cell_names = {name for cell in cells for name in cell.get('class', '').split() if name != 'c'}
    if not cell_names <= bites.keys():
        raise ValueError('Missing bite timing for contribution cells')
    rules = []
    for name in sorted(cell_names):
        before, color, after = bites[name]
        rules.append(f'@keyframes {name}{{0%,{before}%{{fill:{color};filter:none}}'
                     f'{after}%,100%{{fill:#9CF9CA;filter:drop-shadow(0 0 2px #34D399) '
                     'drop-shadow(0 0 4px #34D399)}}')
    return ''.join(rules)


def prepare(source, calendar):
    doc = ET.fromstring(source)
    ns = '{http://www.w3.org/2000/svg}'
    if doc.tag != ns + 'svg' or 'Generated with https://github.com/Platane/snk' not in source:
        raise ValueError('Expected the original Platane contribution snake')
    if not any('s' in n.get('class', '').split() for n in doc) or '@keyframes' not in source:
        raise ValueError('Missing original snake animation')
    weeks = calendar['weeks']
    cells = [n for n in doc if 'c' in n.get('class', '').split()]
    columns = sorted({float(n.attrib['x']) for n in cells})
    if len(columns) != len(weeks):
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
    source = source.replace('</svg>', labels + '<style>' + glow_styles(source, cells) + '@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style></svg>')
    ET.fromstring(source)
    return source
