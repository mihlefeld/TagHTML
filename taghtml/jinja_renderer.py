import pathlib
import math
import copy
import json
import datetime
import jinja2
from jinja2 import FileSystemLoader
from pathlib import Path
from rich.progress import Progress
from collections import defaultdict
from typing import List
from bs4 import BeautifulSoup, Tag, NavigableString
from .datahandler import Competitor, CompetitorData, Assignment

__TEMPLATE__ = pathlib.Path(__file__).absolute().parent.parent / "template.html"
__EXP_EMOJI__ = pathlib.Path(__file__).absolute().parent.parent / "experience_emoji.json"
__PEOPLE_EMOJI__ = pathlib.Path(__file__).absolute().parent.parent / "people_emoji.json"
__CID_MODULO_EMOJI__ = pathlib.Path(__file__).absolute().parent.parent / "cid_modulo_emoji.json"
__FORMATS__ = {
    "A4": (21.0, 29.7),
    "Letter": (21.59, 27.94)
}
__FLAG_BASE_CODE__ = 127397

def iso2flag(iso2: str):
    return ''.join([chr(__FLAG_BASE_CODE__ + ord(c)) for c in iso2.upper()])



class JinjaRenderer:
    def __init__(
            self, width, height, template_path=__TEMPLATE__, 
            exp_emoji_path=__EXP_EMOJI__, people_emoji_path=__PEOPLE_EMOJI__,
            cid_modulo_emoji_path=__CID_MODULO_EMOJI__, format="A4") -> None:
        self.page_width, self.page_height = __FORMATS__[format]
        self.tag_width = width
        self.tag_height = height
        self.columns = int(math.floor(self.page_width / width))
        self.rows = int(math.floor(self.page_height / height))
        self.per_page = self.columns * self.rows
        self.valid_replace_tags = defaultdict(lambda: defaultdict(bool))
        self.template_path = template_path
        self.jinja = jinja2.Environment(loader=FileSystemLoader(template_path.parent.absolute().as_posix()), autoescape=False)
        # with open(template_path, encoding="utf-8") as file:
        #     markup = file.read()
        # self.bs = BeautifulSoup(markup, features="html.parser")
        # self.bs.find(name='style').string += "@page {size: " + format + "; margin: 0; }"
        # self.front_tag_template = self.bs.find(id='front-tag').extract()
        # self.back_tag_template = self.bs.find(id='back-tag').extract()
        self.exp_emoji = json.load(open(exp_emoji_path, encoding="UTF-8"))
        self.people_emoji: dict = json.load(open(people_emoji_path, encoding="UTF-8"))
        assert isinstance(self.people_emoji, dict)
        self.cid_modulo_emoji = json.load(open(cid_modulo_emoji_path, encoding="UTF-8"))
        if isinstance(self.cid_modulo_emoji, dict):
            self.cid_modulo_emoji = list(self.cid_modulo_emoji.values())
    
    def get_render_dict(self, competitor: Competitor):
        name_parts = competitor.name.split()
        cid_emoji = ""
        if competitor.idx is not None:
            cid_emoji = self.cid_modulo_emoji[competitor.idx % len(self.cid_modulo_emoji)] 
        return {
            "name": competitor.name,
            "wca_id": competitor.wca_id,
            "iso2": competitor.iso2,
            "iso2flag": iso2flag(competitor.iso2),
            "firstname": name_parts[0],
            "lastname": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
            "assignments": competitor.assignments,
            "cid_emoji": cid_emoji,
            "pep_emoji": self.people_emoji.get(competitor.wca_id, ""),
            "exp_emoji": self.competition_count_to_emoji(competitor.num_competitions),
            "idx": competitor.idx,
            "country": competitor.country,
            "num_competitions": competitor.num_competitions,
            "roles": competitor.roles
        }

    def render(self, competitors: CompetitorData, out_path, progress: Progress):
        self.comp_name = competitors.comp_name
        pages: List[List[Competitor]] = []
        current_row = []
        current_page = []
        for i, competitor in enumerate(competitors):
            if i % self.columns == 0 or i == len(competitors) - 1:
                if len(current_row) != 0:
                    current_page.append(current_row)
                current_row = []
            if i % self.per_page == 0 or i == len(competitors) - 1: 
                if len(current_page) != 0:
                    pages.append(current_page)
                current_page = []
            current_row.append(self.get_render_dict(competitor))
        if len(current_row) != 0:
            current_page.append(current_row)
            pages.append(current_page)
        
        events = ["333","222","444","555","666","777","333bf","333fm","333oh","clock","minx","pyram","skewb","sq1","444bf","555bf","333mbf"]
        
        template = self.jinja.get_template(self.template_path.name)
        rendered = template.render(pages=pages, wca_events=events, event_times=competitors.event_times)
        with open(out_path, "w", encoding="utf8") as file:
            file.write(rendered)
            

    def competition_count_to_emoji(self, comp_count):
        emoji = ""
        for k, v in self.exp_emoji.items():
            if comp_count >= int(k):
                emoji = v
        return emoji
