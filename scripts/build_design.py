"""Build self-contained profile headers with a reduced-motion alternative."""
from pathlib import Path
from html import escape
from activity import load_config

CONFIG = load_config()
OUT = Path(__file__).resolve().parents[1] / 'assets'
BG, PANEL, BORDER = '#090F0D', '#101D17', '#294536'
GREEN, MINT, WHITE, MUTED = '#34D399', '#B4D7C4', '#F4F7F5', '#A5B8AD'


def text(x, y, value, size=24, color=WHITE, extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{escape(value)}</text>'


def rect(x, y, w, h, fill=PANEL, radius=14):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{BORDER}"/>'


def svg(width, height, body, animated=False):
    title = CONFIG['display_name'] + ' — ' + CONFIG['headline']
    motion = '.flow{animation:flow 9s linear infinite}@keyframes flow{to{stroke-dashoffset:-96}}' if animated else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title>
<desc id="desc">{escape(CONFIG['tagline'])} A terminal, container and server connected by an emerald signal path.</desc>
<defs><linearGradient id="surface" x2="1" y2="1"><stop stop-color="#0B1510"/><stop offset="1" stop-color="#111F19"/></linearGradient><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#294536" stroke-opacity=".25"/></pattern></defs>
<style>text{{font-family:Arial,Helvetica,sans-serif}}.mono{{font-family:Consolas,monospace}}{motion}@media(prefers-reduced-motion:reduce){{.flow{{animation:none}}}}</style>
{rect(1, 1, width-2, height-2, 'url(#surface)', 20)}
{body}</svg>'''


def desktop():
    body = '<rect x="718" y="24" width="458" height="252" rx="16" fill="url(#grid)"/>'
    body += '<path d="M48 46H83" stroke="#34D399" stroke-width="3" stroke-linecap="round"/>'
    body += text(95, 51, CONFIG['username'].upper() + ' / ENGINEERING NOTES', 12, MINT, 'class="mono" letter-spacing="1.6"')
    body += text(46, 127, CONFIG['display_name'], 56, WHITE, 'font-weight="700" letter-spacing="-1.5"')
    body += text(48, 174, CONFIG['headline'], 27, MINT)
    body += text(48, 216, CONFIG['tagline'], 20, MUTED)
    body += text(48, 265, 'BUILD  /  AUTOMATE  /  LEARN', 12, GREEN, 'class="mono" letter-spacing="2"')
    path = 'M823 132H893V88H1020V191H1100'
    body += f'<path d="{path}" fill="none" stroke="{BORDER}" stroke-width="2"/><path class="flow" d="{path}" fill="none" stroke="{GREEN}" stroke-width="2" stroke-dasharray="6 42" stroke-linecap="round"/>'
    body += rect(754, 94, 106, 78) + text(773, 129, '>_', 25, GREEN, 'class="mono"')
    body += '<path d="M774 148h52" stroke="#688B78" stroke-width="2"/>'
    body += text(762, 198, 'TERMINAL', 11, MUTED, 'class="mono" letter-spacing="1.2"')
    body += rect(949, 46, 108, 84)
    body += '<g fill="none" stroke="#B4D7C4" stroke-width="2"><path d="M977 72l26-12 26 12v29l-26 13-26-13zM977 72l26 13 26-13M1003 85v29"/></g>'
    body += text(957, 154, 'CONTAINER', 11, MUTED, 'class="mono" letter-spacing="1"')
    body += rect(1060, 153, 96, 79)
    body += '<g fill="none" stroke="#B4D7C4" stroke-width="2"><path d="M1077 174h61M1077 192h61M1077 210h61"/></g><g fill="#34D399"><circle cx="1082" cy="174" r="3"/><circle cx="1082" cy="192" r="3"/><circle cx="1082" cy="210" r="3"/></g>'
    body += text(1076, 259, 'SERVER', 11, MUTED, 'class="mono" letter-spacing="1.2"')
    return body


def mobile():
    body = text(28, 40, CONFIG['username'].upper() + ' / ENGINEERING NOTES', 12, GREEN, 'class="mono" letter-spacing="1"')
    body += text(26, 103, CONFIG['display_name'], 42, WHITE, 'font-weight="700" letter-spacing="-1"')
    body += text(28, 147, CONFIG['headline'], 25, MINT)
    body += text(28, 185, CONFIG['tagline'], 21, MUTED)
    body += '<path d="M28 216H452" stroke="#294536"/>'
    body += text(28, 247, 'BUILD  /  AUTOMATE  /  LEARN', 12, GREEN, 'class="mono" letter-spacing="1.3"')
    return body


def main():
    OUT.mkdir(exist_ok=True)
    for name, content in (
        ('header.svg', svg(1200, 300, desktop(), animated=True)),
        ('header-static.svg', svg(1200, 300, desktop())),
        ('header-mobile.svg', svg(480, 274, mobile())),
    ):
        (OUT / name).write_text(content, encoding='utf-8')
    print('Built desktop, static and mobile profile headers.')


if __name__ == '__main__':
    main()
