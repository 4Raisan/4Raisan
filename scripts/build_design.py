"""Generate the profile's original SVG artwork without third-party fonts."""
from pathlib import Path
from html import escape
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)
BG, PANEL, BORDER = '#090B0A', '#141916', '#26382E'
GREEN, MINT, WHITE, MUTED = '#34D399', '#A7CDBB', '#F4F7F5', '#A5AEA8'
def svg(w,h,title,body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}"><title>{escape(title)}</title><style>text{{font-family:Arial,Helvetica,sans-serif}} .mono{{font-family:Consolas,monospace}} .signal{{offset-path:path('M 825 140 L 912 140 L 912 100 L 1020 100 L 1020 195 L 1118 195');animation:travel 8s linear infinite}} @keyframes travel{{from{{offset-distance:0%}}to{{offset-distance:100%}}}} @media(prefers-reduced-motion:reduce){{.signal{{animation:none;display:none}}}}</style>{body}</svg>'''
def text(x,y,s,size=24,color=WHITE,extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{escape(s)}</text>'
def rect(x,y,w,h,fill=PANEL,r=14):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{BORDER}"/>'
def save(name,w,h,title,body):
    (OUT/name).write_text(svg(w,h,title,body),encoding='utf-8')
illustration=f'''<g fill="none" stroke="{BORDER}" stroke-width="2"><path d="M825 140H912V100H1020V195H1118"/><path d="M875 140V222H980"/></g>{rect(768,91,110,86)}{text(787,124,'>_',22,GREEN,'class="mono"')}<path d="M789 148h62" stroke="{MINT}" stroke-width="2"/>{rect(967,56,108,87)}<g fill="none" stroke="{MINT}" stroke-width="2"><path d="M994 83l27-13 27 13v28l-27 14-27-14zM994 83l27 14 27-14M1021 97v28"/></g>{rect(1069,160,89,73)}<g stroke="{MINT}" stroke-width="2"><path d="M1086 181h55M1086 195h55M1086 209h55"/></g><circle cx="0" cy="0" r="4" fill="{GREEN}" class="signal"/>{text(781,201,'TERMINAL',11,MUTED,'class="mono"')}{text(978,166,'CONTAINER',11,MUTED,'class="mono"')}{text(1080,256,'SERVER',11,MUTED,'class="mono"')}'''
header=rect(1,1,1198,278,BG,20)+text(48,57,'4RAISAN / ENGINEERING NOTES',14,GREEN,'class="mono" letter-spacing="2"')+text(46,126,'Rashen Anupama',58,WHITE,'font-weight="700"')+text(48,177,'Cloud & Platform Engineering',27,MINT)+text(48,220,'Learning through projects.',21,MUTED)+illustration
save('header.svg',1200,280,'Rashen Anupama — Cloud & Platform Engineering, learning through projects',header)
save('header-static.svg',1200,280,'Rashen Anupama — Cloud & Platform Engineering',header.replace('class="signal"','opacity="0"'))
mobile=rect(1,1,478,268,BG,18)+text(26,42,'4RAISAN / ENGINEERING NOTES',12,GREEN,'class="mono" letter-spacing="1"')+text(24,104,'Rashen Anupama',43,WHITE,'font-weight="700"')+text(26,148,'Cloud & Platform Engineering',25,MINT)+text(26,185,'Learning through projects.',22,MUTED)+f'<path d="M28 223h82m12 0h36m12 0h65" stroke="{BORDER}" stroke-width="3"/><circle cx="115" cy="223" r="4" fill="{GREEN}"/>'
save('header-mobile.svg',480,270,'Rashen Anupama — Cloud & Platform Engineering, learning through projects',mobile)
print('Built original header artwork and mobile variant.')
