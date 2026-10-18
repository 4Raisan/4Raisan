import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import activity
import generate_stats
import publish_activity
import xml.etree.ElementTree as ET


def snapshot():
    calendar = {'totalContributions': 3, 'weeks': [{'contributionDays': [
        {'date': '2024-02-28', 'weekday': 3, 'contributionCount': 1, 'contributionLevel': 'FIRST_QUARTILE'},
        {'date': '2024-02-29', 'weekday': 4, 'contributionCount': 2, 'contributionLevel': 'SECOND_QUARTILE'},
        {'date': '2024-03-01', 'weekday': 5, 'contributionCount': 0, 'contributionLevel': 'NONE'}]}]}
    return {'data': {'user': {'contributionsCollection': {
        'contributionCalendar': calendar, **dict(zip(activity.COUNTS, [3, 2, 1, 0]))}}}}


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'assets').mkdir()
        (self.root / 'README.md').write_text('<!-- activity-date -->old<!-- /activity-date -->', encoding='utf-8')
        for name in ('stats.svg', 'calendar.svg'):
            (self.root / 'assets' / name).write_text('old ' + name, encoding='utf-8')
        generate_stats.generate(self.root, snapshot(), datetime(2024, 3, 1, tzinfo=timezone.utc))
        fixture = Path(__file__).parent / 'fixtures/original-snake.svg'
        doc = ET.fromstring(fixture.read_text())
        cells = [n for n in doc if 'c' in n.get('class', '').split()]
        first = min(float(n.attrib['x']) for n in cells)
        for cell in cells:
            if float(cell.attrib['x']) != first:
                doc.remove(cell)
        # Preserve CSS and original snake segments, limiting the calendar to one week.
        raw = ET.tostring(doc, encoding='unicode').replace('ns0:', '').replace(':ns0', '')
        (self.root / '.generated/snake.svg').write_text(raw)


    def originals(self):
        return {p: p.read_bytes() for p in [self.root / 'README.md', *sorted((self.root / 'assets').glob('*'))]}

    def test_generate_publish_leap_day(self):
        publish_activity.publish(self.root)
        self.assertIn('2024-02-29: 2 contributions', (self.root / 'assets/calendar.svg').read_text())
        self.assertIn('2024-03-01', (self.root / 'README.md').read_text())

    def test_original_snake_animation_is_preserved(self):
        raw = (self.root / '.generated/snake.svg').read_text()
        publish_activity.publish(self.root)
        published = (self.root / 'assets/snake.svg').read_text()
        self.assertIn('Generated with https://github.com/Platane/snk', published)
        ns = '{http://www.w3.org/2000/svg}'
        old_styles = [n.text for n in ET.fromstring(raw).iter(ns + 'style')]
        new_styles = [n.text for n in ET.fromstring(published).iter(ns + 'style')]
        self.assertTrue(all(style in new_styles for style in old_styles))
        self.assertIn('Contributions', published)

    def test_tampered_snake_does_not_publish(self):
        before = self.originals()
        path = self.root / '.generated/snake.svg'
        path.write_text(path.read_text().replace('Generated with https://github.com/Platane/snk', 'invalid generator'))
        with self.assertRaisesRegex(ValueError, 'original Platane'):
            publish_activity.publish(self.root)
        self.assertEqual(before, self.originals())

    def test_failed_first_snake_publish_removes_new_file(self):
        before = self.originals()
        real = os.replace
        def fail_readme(source, target):
            if Path(target).name == 'README.md' and not getattr(fail_readme, 'failed', False):
                fail_readme.failed = True
                raise OSError('simulated failure after creating snake')
            return real(source, target)
        with patch('publish_activity.os.replace', side_effect=fail_readme):
            with self.assertRaises(OSError):
                publish_activity.publish(self.root)
        self.assertEqual(before, self.originals())

    def test_invalid_statistics_leave_published_files_unchanged(self):
        before = self.originals()
        p = self.root / '.generated/stats.svg'
        p.write_text(p.read_text().replace('>3</text>', '>999</text>'))
        with self.assertRaisesRegex(ValueError, 'Statistics counts'):
            publish_activity.publish(self.root)
        self.assertEqual(before, self.originals())

    def test_invalid_marker_leaves_files_unchanged(self):
        (self.root / 'README.md').write_text('No marker')
        before = self.originals()
        with self.assertRaisesRegex(ValueError, 'date marker'):
            publish_activity.publish(self.root)
        self.assertEqual(before, self.originals())

    def test_failed_replace_rolls_back(self):
        before = self.originals()
        real = os.replace
        calls = 0
        def fail_once(source, target):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError('simulated disk failure')
            return real(source, target)
        with patch('publish_activity.os.replace', side_effect=fail_once):
            with self.assertRaises(OSError):
                publish_activity.publish(self.root)
        self.assertEqual(before, self.originals())

    def test_recover_interrupted_publish(self):
        before = self.originals()
        backup = {str(p.relative_to(self.root)): p.read_text() for p in before}
        (self.root / '.generated/publish-backup.json').write_text(json.dumps(backup))
        (self.root / 'assets/stats.svg').write_text('interrupted write')
        publish_activity.recover(self.root)
        self.assertEqual(before, self.originals())

    def test_reject_invalid_calendar(self):
        base = snapshot()['data']['user']['contributionsCollection']
        for field, value in [('date', '2024-02-28'), ('weekday', 6), ('contributionCount', -1), ('contributionLevel', 'UNKNOWN')]:
            data = copy.deepcopy(base)
            data['contributionCalendar']['weeks'][0]['contributionDays'][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                activity.validate_data(data)
        base['contributionCalendar']['totalContributions'] = 100
        with self.assertRaises(ValueError):
            activity.validate_data(base)

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test-token'})
    def test_retry_transient_http_and_network_errors(self):
        failures = [URLError('temporary'), HTTPError('url', 503, 'temporary', {}, None)]
        def opener(*args, **kwargs):
            if failures:
                raise failures.pop(0)
            return io.BytesIO(json.dumps(snapshot()).encode())
        delays = []
        self.assertEqual(activity.fetch('query', {}, opener, delays.append), snapshot())
        self.assertEqual(delays, [1, 2])

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test-token'})
    def test_authentication_failure_is_not_retried(self):
        opener = unittest.mock.Mock(side_effect=HTTPError('url', 401, 'unauthorized', {}, None))
        with self.assertRaises(RuntimeError):
            activity.fetch('query', {}, opener, lambda _: None)
        self.assertEqual(opener.call_count, 1)

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test-token'})
    def test_retry_budget_is_bounded(self):
        opener = unittest.mock.Mock(side_effect=URLError('temporary'))
        with self.assertRaises(RuntimeError):
            activity.fetch('query', {}, opener, lambda _: None)
        self.assertEqual(opener.call_count, 4)

    def test_query_window_never_exceeds_365_days(self):
        now = datetime(2024, 3, 1, tzinfo=timezone.utc)
        with patch('generate_stats.fetch', return_value=snapshot()) as fetch:
            generate_stats.generate(self.root, now=now)
        variables = fetch.call_args.args[1]
        start = datetime.fromisoformat(variables['from'])
        end = datetime.fromisoformat(variables['to'])
        self.assertEqual((end - start).days, 365)
        self.assertEqual(end, now.replace(hour=23, minute=59, second=59))


if __name__ == '__main__':
    unittest.main()
