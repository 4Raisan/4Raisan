"""Shared configuration, bounded API retries, and snapshot validation."""
import json
import os
import time
from datetime import date, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
COUNTS = ('totalCommitContributions', 'totalPullRequestContributions',
          'totalIssueContributions', 'totalPullRequestReviewContributions')
LEVELS = ('NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE')

def load_config():
    config = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
    config['timezone'] = timezone(timedelta(minutes=config['timezone_offset_minutes']))
    return config

def fetch(query, variables, opener=urlopen, sleep=time.sleep):
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('Set GITHUB_TOKEN before refreshing activity')
    request = Request('https://api.github.com/graphql',
                      data=json.dumps({'query': query, 'variables': variables}).encode(),
                      headers={'Authorization': 'Bearer ' + token,
                               'Content-Type': 'application/json', 'User-Agent': 'profile-activity'})
    for attempt in range(4):
        delay = 2 ** attempt
        try:
            with opener(request, timeout=45) as response:
                result = json.load(response)
            if result.get('errors'):
                retryable = all(e.get('type') in ('RATE_LIMITED', 'INTERNAL', 'SERVICE_UNAVAILABLE')
                                for e in result['errors'])
                if retryable and attempt < 3:
                    sleep(delay)
                    continue
                raise RuntimeError('GitHub GraphQL request failed; check token permissions and API status')
            if not result.get('data', {}).get('user'):
                raise ValueError('GitHub returned no profile data')
            return result
        except HTTPError as error:
            error.close()
            limited = error.code == 403 and (error.headers.get('X-RateLimit-Remaining') == '0'
                                             or error.headers.get('Retry-After') is not None)
            if attempt == 3 or not (limited or error.code in (429, 500, 502, 503, 504)):
                raise RuntimeError(f'GitHub request failed (HTTP {error.code})') from None
            retry_after = error.headers.get('Retry-After', '')
            if retry_after.isdigit():
                delay = min(60, max(delay, int(retry_after)))
        except (URLError, TimeoutError, ConnectionError):
            if attempt == 3:
                raise RuntimeError('GitHub request failed after four network attempts') from None
        sleep(delay)

def validate_data(data):
    for key in COUNTS:
        if type(data.get(key)) is not int or data[key] < 0:
            raise ValueError('Invalid statistic: ' + key)
    validate_calendar(data['contributionCalendar'])

def validate_calendar(calendar):
    days = [day for week in calendar['weeks'] for day in week['contributionDays']]
    if not days:
        raise ValueError('Empty contribution calendar')
    previous = None
    for day in days:
        current = date.fromisoformat(day['date'])
        if previous is not None and current != previous + timedelta(days=1):
            raise ValueError('Calendar dates must be consecutive and unique')
        if type(day['weekday']) is not int or day['weekday'] != (current.weekday() + 1) % 7:
            raise ValueError('Calendar weekday mismatch')
        if type(day['contributionCount']) is not int or day['contributionCount'] < 0:
            raise ValueError('Invalid daily contribution count')
        if day['contributionLevel'] not in LEVELS:
            raise ValueError('Invalid contribution level')
        previous = current
    if type(calendar['totalContributions']) is not int or sum(d['contributionCount'] for d in days) != calendar['totalContributions']:
        raise ValueError('Calendar total mismatch')
