"""Animate a snake sweeping the same dated calendar used by the statistics."""
from html import escape
from calendar import month_abbr

COLORS = dict(zip(('NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE'),
                  ('#141916', '#174B36', '#187D52', '#24AA73', '#34D399')))


def render(calendar):
    weeks = calendar['weeks']
    days = [d for w in weeks for d in w['contributionDays']]
    width = 36 + len(weeks) * 14
    # Adjacent columns run in opposite directions so the snake turns smoothly.
    route = [(i, row) for i in range(len(weeks))
             for row in (range(7) if i % 2 == 0 else range(6, -1, -1))]
    points = [(23.5 + i * 14, 77.5 + row * 14) for i, row in route]
    # Return outside the grid, then restart without jumping through calendar cells.
    points += [(points[-1][0], 174), (9, 174), (9, 77.5), points[0]]
    path = 'M ' + ' L '.join(f'{x:g} {y:g}' for x, y in points)
    distances = [0.0]
    for (x, y), (nx, ny) in zip(points, points[1:]):
        distances.append(distances[-1] + abs(nx - x) + abs(ny - y))
    fractions = {point: distances[i] / distances[-1] for i, point in enumerate(route)}
    body = f'<rect width="{width}" height="224" rx="14" fill="#090B0A"/>'
    body += f'<text x="18" y="34" fill="#A7CDBB" font-size="18">{calendar["totalContributions"]:,} contributions</text>'
    previous = None
    last_label = -3
    for i, week in enumerate(weeks):
        dates = week['contributionDays']
        boundary = next((d['date'] for d in dates if d['date'].endswith('-01')), dates[0]['date'])
        month = boundary[:7]
        if month != previous and (i == 0 or boundary.endswith('-01')) and i < len(weeks) - 2 and i - last_label >= 3:
            body += f'<text x="{18+i*14}" y="60" fill="#A5AEA8" font-size="12">{month_abbr[int(boundary[5:7])]}</text>'
            last_label = i
        previous = month
        for day in dates:
            fraction = max(0.001, fractions[(i, day['weekday'])])
            color = COLORS[day['contributionLevel']]
            body += f'<rect x="{18+i*14}" y="{72+day["weekday"]*14}" width="11" height="11" rx="2" fill="{color}"><title>{day["date"]}: {day["contributionCount"]} contributions</title>'
            body += f'<animate attributeName="fill" values="{color};#141916;#141916" keyTimes="0;{fraction:.6f};1" calcMode="discrete" dur="40s" repeatCount="indefinite"/></rect>'
    # Tail first, head last, with progressively later starts to follow the head.
    for segment in range(5, -1, -1):
        fill = '#A7CDBB' if segment else '#F4F7F5'
        body += f'<rect class="snake" x="-5" y="-5" width="10" height="10" rx="3" fill="{fill}"><animateMotion path="{path}" dur="40s" begin="{segment * 0.07:.2f}s" calcMode="paced" repeatCount="indefinite"/></rect>'
    period = days[0]['date'] + ' — ' + days[-1]['date']
    body += f'<text x="18" y="198" fill="#A5AEA8" font-size="12">{escape(period)} · GitHub calendar dates</text>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="224" viewBox="0 0 {width} 224" role="img"><title>Animated GitHub contribution snake</title><style>text{{font-family:Arial,Helvetica,sans-serif}}@media(prefers-reduced-motion:reduce){{.snake{{display:none}}}}</style>{body}</svg>'
