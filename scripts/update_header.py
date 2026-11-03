"""Render the public GitHub contribution calendar without third-party stats services."""
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen

USER = '9Sk1p'
ROOT = Path(__file__).resolve().parents[1]

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.tips = {}
        self.tip = None
        self.total_parts = []
        self.in_total = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and a.get('data-date'):
            self.days[a['id']] = (date.fromisoformat(a['data-date']), int(a['data-level']))
        if tag == 'tool-tip' and a.get('for') in self.days:
            self.tip = a['for']
            self.tips[self.tip] = ''
        if tag == 'h2' and a.get('id') == 'js-contribution-activity-description':
            self.in_total = True

    def handle_data(self, text):
        if self.tip:
            self.tips[self.tip] += text
        if self.in_total:
            self.total_parts.append(text)

    def handle_endtag(self, tag):
        if tag == 'tool-tip':
            self.tip = None
        if tag == 'h2':
            self.in_total = False


def render(source):
    graph = Calendar()
    graph.feed(source)
    if not 350 <= len(graph.days) <= 371:
        raise ValueError('Unexpected GitHub calendar; keep the existing header')
    match = re.search(r'([\d,]+)\s+contributions?', ''.join(graph.total_parts))
    if not match:
        raise ValueError('Contribution total not found; keep the existing header')
    total = int(match.group(1).replace(',', ''))
    first = min(day for day, _ in graph.days.values())
    last = max(day for day, _ in graph.days.values())
    colors = ['#26313b', '#164a39', '#1e7554', '#38a477', '#72dbad']
    cells = []
    months = {}
    for key, (day, level) in graph.days.items():
        if level not in range(5):
            raise ValueError('Unexpected contribution level')
        week = (day - first).days // 7
        row = (day.weekday() + 1) % 7
        label = escape(graph.tips.get(key, day.isoformat()))
        cells.append(f'<rect x="{508 + week * 10}" y="91" width="8" height="8" rx="1.5" fill="{colors[level]}" transform="translate(0,{row * 10})"><title>{label}</title></rect>')
        if day.day <= 7:
            months.setdefault((day.year, day.month), (week, day.strftime('%b')))
    labels = ''.join(f'<text x="{508 + week * 10}" y="79">{name}</text>' for week, name in months.values())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="235" viewBox="0 0 1100 235" role="img" aria-labelledby="title description">
<title id="title">Yehor Hubarenko - frontend development and GitHub contributions</title>
<desc id="description">{total} contributions shown by GitHub in the last year. Calendar {first} to {last}. Updated daily.</desc>
<rect width="1100" height="235" rx="12" fill="#141c24"/>
<path d="M38 35v163" stroke="#65c3aa" stroke-width="3"/>
<g font-family="Arial, sans-serif">
<text x="63" y="58" font-size="12" font-weight="700" letter-spacing="2.5" fill="#9fb3c5">FRONTEND DEVELOPMENT</text>
<text x="63" y="105" font-size="33" font-weight="700" fill="#f5f8fc">Yehor Hubarenko</text>
<text x="63" y="139" font-size="17" fill="#c5d3df">React · TypeScript · C foundations</text>
<text x="63" y="177" font-size="13" fill="#9fb3c5">Prague, CZ  /  ČZU &amp; 42 Prague  /  @9Sk1p</text>
<path d="M476 35v163" stroke="#344453"/>
<text x="508" y="49" font-size="18" font-weight="700" fill="#f5f8fc">{total} contributions in the last year</text>
<g font-size="10" fill="#9fb3c5">{labels}</g>
{''.join(cells)}
<text x="508" y="188" font-size="10" fill="#9fb3c5">GitHub calendar · {first} to {last} · refreshed {date.today().isoformat()}</text>
</g></svg>\n'''


def main():
    request = Request(f'https://github.com/users/{USER}/contributions', headers={'User-Agent': '9Sk1p-profile-header', 'Accept-Language': 'en'})
    with urlopen(request, timeout=30) as response:
        source = response.read().decode('utf-8')
    svg = render(source)
    target = ROOT / 'assets/header.svg'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(svg, encoding='utf-8')
    print(f'Updated {target.name} from GitHub calendar')

if __name__ == '__main__':
    main()
