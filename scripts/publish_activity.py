"""Validate a snapshot, then publish with recoverable file replacements."""
from pathlib import Path
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from activity import ROOT, COUNTS, validate_calendar
from snake import prepare as prepare_snake

NS = '{http://www.w3.org/2000/svg}'


def atomic_write(path, content):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def recover(root):
    journal = root / '.generated/publish-backup.json'
    if journal.exists():
        for relative, content in json.loads(journal.read_text(encoding='utf-8')).items():
            if content is None:
                (root / relative).unlink(missing_ok=True)
            else:
                atomic_write(root / relative, content)
        journal.unlink()


def publish(root=ROOT):
    # An interrupted multi-file update is rolled back before trying another snapshot.
    recover(root)
    calendar = json.loads((root / '.generated/calendar.json').read_text(encoding='utf-8'))
    validate_calendar(calendar)
    staged = {}
    for name in ('stats.svg', 'calendar.svg', 'snake.svg'):
        source = (root / '.generated' / name).read_text(encoding='utf-8')
        doc = ET.fromstring(source)
        if doc.tag != NS + 'svg':
            raise ValueError('Invalid SVG')
        if name == 'snake.svg':
            staged['assets/' + name] = prepare_snake(source, calendar)
            continue
        if any(node.tag.startswith(NS + 'animate') or node.tag == NS + 'set' for node in doc.iter()):
            raise ValueError('Activity graphics must be static')
        if name == 'calendar.svg':
            expected = [f'{d["date"]}: {d["contributionCount"]} contributions'
                        for w in calendar['weeks'] for d in w['contributionDays']]
            actual = [n.text for n in doc.iter(NS + 'title')][1:]
            if actual != expected:
                raise ValueError('Calendar cells mismatch')
            texts = [n.text for n in doc.iter(NS + 'text')]
            if f'{calendar["totalContributions"]:,} contributions' not in texts:
                raise ValueError('Calendar heading mismatch')
        else:
            counts = calendar['statistics']
            for key in COUNTS:
                if type(counts.get(key)) is not int or counts[key] < 0:
                    raise ValueError('Invalid statistic: ' + key)
            actual = [n.text for n in doc.iter(NS + 'text') if n.get('text-anchor') == 'end']
            if actual != [f'{counts[key]:,}' for key in COUNTS]:
                raise ValueError('Statistics counts mismatch')
            days = [d for w in calendar['weeks'] for d in w['contributionDays']]
            period = days[0]['date'] + ' — ' + days[-1]['date']
            if period not in [n.text for n in doc.iter(NS + 'text')]:
                raise ValueError('Statistics date range mismatch')
        staged['assets/' + name] = source
    readme, count = re.subn(r'<!-- activity-date -->.*?<!-- /activity-date -->',
                          lambda _: '<!-- activity-date -->Updated ' + calendar['refreshedAt'] + '<!-- /activity-date -->',
                          (root / 'README.md').read_text(encoding='utf-8'))
    if count != 1:
        raise ValueError('Expected one date marker')
    staged['README.md'] = readme
    backup = {name: (root / name).read_text(encoding='utf-8') if (root / name).exists() else None for name in staged}
    journal = root / '.generated/publish-backup.json'
    atomic_write(journal, json.dumps(backup))
    try:
        for name, source in staged.items():
            atomic_write(root / name, source)
    except BaseException:
        recover(root)
        raise
    journal.unlink()
    print('Validated activity assets:', calendar['totalContributions'], 'contributions')


if __name__ == '__main__':
    publish()
