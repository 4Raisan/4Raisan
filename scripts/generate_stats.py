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
    days = [d for w in data['contributionCalendar']['weeks'] for d in w['contributionDays']]
    period = days[0]['date'] + ' — ' + days[-1]['date']
    total = data['contributionCalendar']['totalContributions']
    body = '<rect x="1" y="1" width="548" height="124" rx="14" fill="#101816" stroke="#30483c"/>'
    body += f'<text x="275" y="33" text-anchor="middle" fill="#eff6f2" font-size="22" font-weight="bold">{total:,} contributions</text>'
    for i, (label, key) in enumerate(rows):
        x = 18 + i * 134
        body += f'<text x="{x}" y="77" font-size="13" fill="#c8d5ce">{label}</text>'
        body += f'<text x="{x + 107}" y="77" text-anchor="end" font-size="16" fill="#eff6f2">{data[key]:,}</text>'
    body += f'<text x="275" y="108" text-anchor="middle" font-size="13" fill="#adbbb3">{period}</text>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="550" height="126" viewBox="0 0 550 126" role="img"><title>{escape(config["username"])} public GitHub activity</title><style>text{{font-family:Arial,Helvetica,sans-serif}}</style>{body}</svg>'
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
    body = f'<rect width="{width}" height="198" rx="14" fill="#090B0A"/><text x="18" y="34" fill="#A7CDBB" font-size="18">{calendar["totalContributions"]:,} contributions</text>'
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
    body += f'<text x="18" y="182" fill="#A5AEA8" font-size="12">{period} · GitHub calendar dates</text>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="198" viewBox="0 0 {width} 198" role="img"><title>GitHub contribution calendar</title><style>text{{font-family:Arial,Helvetica,sans-serif}}</style>{body}</svg>'
    (out/'calendar.svg').write_text(svg,encoding='utf-8')
    calendar['refreshedAt'] = local_now.strftime('%Y-%m-%d %H:%M ') + config['timezone_label']
    calendar['statistics'] = {key: data[key] for _, key in rows}
    (out/'calendar.json').write_text(json.dumps(calendar),encoding='utf-8')


if __name__ == '__main__':
    generate()
