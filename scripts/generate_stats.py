"""Public activity card using fields accessible to a repository GITHUB_TOKEN."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from html import escape
from datetime import datetime, timezone, timedelta
from calendar import month_abbr

query = '''query($from: DateTime!, $to: DateTime!) {
  user(login: "4Raisan") {
    contributionsCollection(from: $from, to: $to) {
      startedAt endedAt
      contributionCalendar { totalContributions weeks { contributionDays { date weekday contributionCount contributionLevel } } }
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
    }
  }
}'''
local_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
start = local_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365)
variables = {'from': start.astimezone(timezone.utc).isoformat(), 'to': local_now.replace(hour=23, minute=59, second=59, microsecond=0).astimezone(timezone.utc).isoformat()}
request = Request('https://api.github.com/graphql',
    data=json.dumps({'query': query, 'variables': variables}).encode(),
    headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
             'Content-Type': 'application/json', 'User-Agent': '4Raisan-profile'})
with urlopen(request, timeout=45) as response:
    result = json.load(response)
if result.get('errors'):
    raise RuntimeError('; '.join(e['message'] for e in result['errors']))
data = result['data']['user']['contributionsCollection']
rows = [('Commits', 'totalCommitContributions'), ('Pull requests', 'totalPullRequestContributions'),
        ('Issues', 'totalIssueContributions'), ('Code reviews', 'totalPullRequestReviewContributions')]
body = '<rect x="1" y="1" width="298" height="222" rx="14" fill="#090B0A" stroke="#26382E"/>'
body += '<text x="24" y="36" fill="#34D399" font-size="19" font-weight="700">Public GitHub activity</text>'
days = [d for w in data['contributionCalendar']['weeks'] for d in w['contributionDays']]
period = days[0]['date'] + ' — ' + days[-1]['date']
body += f'<text x="24" y="61" fill="#A5AEA8" font-size="12">{escape(period)}</text>'
for i,(label,key) in enumerate(rows):
    value = data[key]
    if type(value) is not int or value < 0:
        raise ValueError(f'Invalid count: {key}')
    y = 96+i*33
    body += f'<circle cx="27" cy="{y-5}" r="3" fill="#34D399"/><text x="42" y="{y}" fill="#A7CDBB" font-size="15">{label}</text><text x="269" y="{y}" text-anchor="end" fill="#F4F7F5" font-size="16" font-weight="700">{value:,}</text>'
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="224" viewBox="0 0 300 224" role="img"><title>4Raisan public GitHub activity from {escape(period)}</title><style>text{{font-family:Arial,Helvetica,sans-serif}}</style>{body}</svg>'
out = Path(__file__).resolve().parents[1] / '.generated'
out.mkdir(exist_ok=True)
(out/'stats.svg').write_text(svg,encoding='utf-8')
(out/'calendar.json').write_text(json.dumps(data['contributionCalendar']), encoding='utf-8')
print('Generated public contribution statistics and calendar for', period)

calendar = data['contributionCalendar']
weeks = calendar['weeks']
if sum(d['contributionCount'] for d in days) != calendar['totalContributions']:
    raise ValueError('Calendar total mismatch')
colors = dict(zip(['NONE','FIRST_QUARTILE','SECOND_QUARTILE','THIRD_QUARTILE','FOURTH_QUARTILE'], ['#141916','#174B36','#187D52','#24AA73','#34D399']))
width = 36 + len(weeks)*14
body = f'<rect width="{width}" height="224" rx="14" fill="#090B0A"/><text x="18" y="34" fill="#A7CDBB" font-size="18">{calendar["totalContributions"]:,} contributions</text>'
previous = None
for i, week in enumerate(weeks):
    dates = week['contributionDays']
    boundary = next((d['date'] for d in dates if d['date'].endswith('-01')), dates[0]['date'])
    month = boundary[:7]
    x = 18+i*14
    if month != previous and i < len(weeks)-2:
        body += f'<text x="{x}" y="60" fill="#A5AEA8" font-size="12">{month_abbr[int(boundary[5:7])]}</text>'
    previous = month
    for d in dates:
        body += f'<rect x="{x}" y="{72+d["weekday"]*14}" width="11" height="11" rx="2" fill="{colors[d["contributionLevel"]]}"><title>{d["date"]}: {d["contributionCount"]} contributions</title></rect>'
body += f'<text x="18" y="198" fill="#A5AEA8" font-size="12">{period} · GitHub calendar dates</text>'
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="224" viewBox="0 0 {width} 224" role="img"><title>GitHub contribution calendar</title><style>text{{font-family:Arial,Helvetica,sans-serif}}</style>{body}</svg>'
(out/'snake.svg').write_text(svg,encoding='utf-8')
calendar['refreshedAt'] = datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime('%Y-%m-%d %H:%M Sri Lanka time (UTC+05:30)')
(out/'calendar.json').write_text(json.dumps(calendar),encoding='utf-8')
