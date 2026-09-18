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
projects=[('luxora','01','Luxora','APPLICATION DELIVERY',['React / Express application with PostgreSQL,','Docker packaging, CI, and role-based access checks.'],['Docker','GitHub Actions','PostgreSQL']),('cosplay-proxy','02','cosplay-proxy','LOCAL DEVELOPER TOOLING',['Local AI proxy with FastAPI, PowerShell setup,','and diagnostic tooling for Windows.'],['Python','FastAPI','PowerShell'])]
for name,num,title,category,lines,labels in projects:
    body=rect(1,1,998,208)+text(30,37,num+' / '+category,13,GREEN,'class="mono" letter-spacing="1.5"')+text(30,83,title,35,WHITE,'font-weight="700"')+text(30,121,lines[0],23,MINT)+text(30,153,lines[1],23,MINT)+text(30,187,' / '.join(labels),16,MUTED,'class="mono"')+text(940,54,'↗',30,GREEN)
    save(name+'.svg',1000,210,title+' — '+' '.join(lines),body)
    descriptions=['React / Express + PostgreSQL','Docker packaging, CI,','and role-based access checks.'] if name=='luxora' else ['Local AI proxy with FastAPI,','PowerShell setup, and','Windows diagnostic tooling.']
    body=rect(1,1,478,258)+text(24,33,num+' / '+category,11,GREEN,'class="mono"')+text(24,79,title,34,WHITE,'font-weight="700"')
    for i,line in enumerate(descriptions): body+=text(24,120+i*31,line,23,MINT)
    body+=text(24,231,' / '.join(labels),15,MUTED,'class="mono"')
    save(name+'-mobile.svg',480,260,title+' — '+' '.join(lines),body)
icons={
'docker':('Docker','<path d="M16 26h31c-2 10-9 15-19 15-7 0-11-5-12-15zM44 24c1-5 6-6 8-4-1 4-4 6-8 6M20 22v-6h7v6zm10 0v-6h7v6zm0-10V6h7v6z"/>'),
'actions':('GitHub Actions','<circle cx="20" cy="22" r="7"/><circle cx="45" cy="12" r="5"/><circle cx="45" cy="34" r="5"/><path d="M27 22h5V12h8M32 22v12h8M18 19l4 3-4 3"/>'),
'python':('Python','<path d="M19 24V12q0-6 10-6h8q5 0 5 6v12H28v7H16q-6 0-6-8t6-8h3M42 20h7q6 0 6 8t-6 8h-7v5q0 6-10 6h-8q-5 0-5-6v-6h14v-7h9z"/><circle cx="27" cy="12" r="1"/><circle cx="35" cy="41" r="1"/>'),
'powershell':('PowerShell','<path d="M16 8h36l-9 35H7zM23 17l9 8-15 8M30 35h10"/>'),
'node':('Node.js','<path d="M31 5l20 11v23L31 50 11 39V16zM22 35V20l17 15V20"/>'),
'postgres':('PostgreSQL','<path d="M17 16q0-11 15-11t15 11v15q0 9-9 9l-2 10h-7V29q-12 2-12-13zM29 29l10-6M21 18h3M36 14h3M17 19l-7 9 9 7"/>')}
for key,(label,path) in icons.items():
    body=rect(1,1,106,72,BG,10)+f'<g transform="translate(29 4) scale(.8)" fill="none" stroke="{GREEN}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</g>'+text(54,65,label,12,MINT,'text-anchor="middle"')
    save('tool-'+key+'.svg',108,74,label,body)
print('Built original artwork and mobile variants.')
