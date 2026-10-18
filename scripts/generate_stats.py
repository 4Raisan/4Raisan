"""Public activity card using fields accessible to a repository GITHUB_TOKEN."""
import json
from html import escape
from datetime import datetime, timezone, timedelta
from calendar import month_abbr
from activity import ROOT, load_config, fetch, validate_data

query = '''query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
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
def generate(root=ROOT, result=None, now=None):
    config = load_config()
    local_now = now or datetime.now(config['timezone'])
    # GitHub accepts at most one year: an exact 365-day window also handles leap years.
    end = local_now.replace(hour=23, minute=59, second=59, microsecond=0)
    start = end - timedelta(days=365)
    variables = {'login': config['username'], 'from': start.astimezone(timezone.utc).isoformat(),
                 'to': end.astimezone(timezone.utc).isoformat()}
    result = result if result is not None else fetch(query, variables)
    data = result['data']['user']['contributionsCollection']
    validate_data(data)
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
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="224" viewBox="0 0 300 224" role="img"><title>{escape(config['username'])} public GitHub activity from {escape(period)}</title><style>text{{font-family:Arial,Helvetica,sans-serif}}</style>{body}</svg>'
    out = root / '.generated'
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
    last_label = -3
    for i, week in enumerate(weeks):
        dates = week['contributionDays']
        boundary = next((d['date'] for d in dates if d['date'].endswith('-01')), dates[0]['date'])
        month = boundary[:7]
        x = 18+i*14
        if month != previous and (i == 0 or boundary.endswith('-01')) and i < len(weeks)-2 and i-last_label >= 3:
            body += f'<text x="{x}" y="60" fill="#A5AEA8" font-size="12">{month_abbr[int(boundary[5:7])]}</text>'
            last_label = i
        previous = month
        for d in dates:
            body += f'<rect x="{x}" y="{72+d["weekday"]*14}" width="11" height="11" rx="2" fill="{colors[d["contributionLevel"]]}"><title>{d["date"]}: {d["contributionCount"]} contributions</title></rect>'
    body += f'<text x="18" y="198" fill="#A5AEA8" font-size="12">{period} · GitHub calendar dates</text>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="224" viewBox="0 0 {width} 224" role="img"><title>GitHub contribution calendar</title><style>text{{font-family:Arial,Helvetica,sans-serif}}</style>{body}</svg>'
    (out/'calendar.svg').write_text(svg,encoding='utf-8')
    calendar['refreshedAt'] = local_now.strftime('%Y-%m-%d %H:%M ') + config['timezone_label']
    calendar['statistics'] = {key: data[key] for _, key in rows}
    (out/'calendar.json').write_text(json.dumps(calendar),encoding='utf-8')


if __name__ == '__main__':
    generate()
