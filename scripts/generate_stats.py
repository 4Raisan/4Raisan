"""Public activity card using fields accessible to a repository GITHUB_TOKEN."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from html import escape

query = '''query {
  user(login: "4Raisan") {
    contributionsCollection {
      startedAt endedAt
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
    }
  }
}'''
request = Request('https://api.github.com/graphql',
    data=json.dumps({'query': query}).encode(),
    headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
             'Content-Type': 'application/json', 'User-Agent': '4Raisan-profile'})
with urlopen(request, timeout=45) as response:
    result = json.load(response)
if result.get('errors'):
    raise RuntimeError('; '.join(e['message'] for e in result['errors']))
data = result['data']['user']['contributionsCollection']
rows = [('Commits', 'totalCommitContributions'), ('Pull requests', 'totalPullRequestContributions'),
        ('Issues', 'totalIssueContributions'), ('Code reviews', 'totalPullRequestReviewContributions')]
body = '<rect x="1" y="1" width="458" height="222" rx="14" fill="#090B0A" stroke="#26382E"/>'
body += '<text x="24" y="36" fill="#34D399" font-size="19" font-weight="700">Public GitHub activity</text>'
period = data['startedAt'][:10] + ' — ' + data['endedAt'][:10]
body += f'<text x="24" y="61" fill="#A5AEA8" font-size="12">{escape(period)}</text>'
for i,(label,key) in enumerate(rows):
    value = data[key]
    if type(value) is not int or value < 0:
        raise ValueError(f'Invalid count: {key}')
    y = 96+i*33
    body += f'<circle cx="27" cy="{y-5}" r="3" fill="#34D399"/><text x="42" y="{y}" fill="#A7CDBB" font-size="15">{label}</text><text x="429" y="{y}" text-anchor="end" fill="#F4F7F5" font-size="16" font-weight="700">{value:,}</text>'
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="224" viewBox="0 0 460 224" role="img"><title>4Raisan public GitHub activity from {escape(period)}</title><style>text{{font-family:Arial,Helvetica,sans-serif}}</style>{body}</svg>'
out = Path(__file__).resolve().parents[1] / '.generated'
out.mkdir(exist_ok=True)
(out/'stats.svg').write_text(svg,encoding='utf-8')
print('Generated public contribution statistics for', period)
