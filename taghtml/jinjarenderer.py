import math
import json
import jinja2
import re
from jinja2 import FileSystemLoader
from pathlib import Path
from collections import defaultdict
from collections import OrderedDict
from .datahandler import Competitor, CompetitorData, Assignment

__TEMPLATE__ = Path(__file__).absolute().parent.parent / "template.html"
__EXP_EMOJI__ = Path(__file__).absolute().parent.parent / "experience_emoji.json"
__PEOPLE_EMOJI__ = Path(__file__).absolute().parent.parent / "people_emoji.json"
__CID_MODULO_EMOJI__ = Path(__file__).absolute().parent.parent / "cid_modulo_emoji.json"
__FORMATS__ = {
    "A4": (21.0, 29.7),
    "Letter": (21.59, 27.94)
}
__FLAG_BASE_CODE__ = 127397

def iso2flag(iso2: str):
    return ''.join([chr(__FLAG_BASE_CODE__ + ord(c)) for c in iso2.upper()])

def seperate_native_name(name):
    matches = re.match(r"([^()]*)(\(([^()]*)\))?", name)
    latin_name = matches.group(1)
    native_name = matches.group(3)
    return latin_name.strip(), native_name.strip() if native_name else ""


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
        self.jinja = jinja2.Environment(loader=FileSystemLoader(template_path.parent.absolute().as_posix()), autoescape=False, auto_reload=True)
        self.events = ["333","222","444","555","666","777","333bf","333fm","333oh","clock","minx","pyram","skewb","sq1","444bf","555bf","333mbf"]
        self.exp_emoji = json.load(open(exp_emoji_path, encoding="UTF-8"))
        self.people_emoji: dict = json.load(open(people_emoji_path, encoding="UTF-8"))
        assert isinstance(self.people_emoji, dict)
        self.cid_modulo_emoji = json.load(open(cid_modulo_emoji_path, encoding="UTF-8"))
        if isinstance(self.cid_modulo_emoji, dict):
            self.cid_modulo_emoji = list(self.cid_modulo_emoji.values())
    
    def get_render_dict(self, competitor: Competitor):
        latin_name, native_name = seperate_native_name(competitor.name)
        name_parts = latin_name.split()
        cid_emoji = ""
        if competitor.idx is not None:
            cid_emoji = self.cid_modulo_emoji[competitor.idx % len(self.cid_modulo_emoji)] 
        event_assignments = defaultdict(lambda: defaultdict(list))
        for assignment in competitor.assignments:
            event_assignments[assignment.event][f"r{assignment.round}"].append(assignment)

        event_comp_r1_assignments = defaultdict(lambda: None)
        event_help_r1_assignments = defaultdict(list)
        for assignment in competitor.assignments:
            if assignment.round != 1:
                continue
            if assignment.role == "competitor":
                if not assignment.event in event_comp_r1_assignments:
                    event_comp_r1_assignments[assignment.event] = assignment # TODO: change to list for fmc and mbld
            else:
                event_help_r1_assignments[assignment.event].append(assignment)
        return {
            "name": latin_name,
            "native_name": native_name,
            "wca_id": competitor.wca_id,
            "iso2": competitor.iso2,
            "iso2flag": iso2flag(competitor.iso2),
            "firstname": name_parts[0],
            "lastname": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
            "assignments": competitor.assignments,
            "event_assignments": event_assignments,
            "event_comp_r1_assignments": event_comp_r1_assignments,
            "event_help_r1_assignments": event_help_r1_assignments,
            "cid_emoji": cid_emoji,
            "pep_emoji": self.people_emoji.get(competitor.wca_id, ""),
            "exp_emoji": self.competition_count_to_emoji(competitor.num_competitions),
            "id": competitor.idx,
            "country": competitor.country,
            "num_competitions": competitor.num_competitions,
            "roles": competitor.roles
        }
    
    def setup(self, competitors: CompetitorData):        
        self.comp_name = competitors.comp_name
        pages: list[list[dict]] = []
        current_page = []
        for i, competitor in enumerate(competitors):
            if i % self.per_page == 0: 
                if len(current_page) != 0:
                    pages.append(current_page)
                current_page = []
            current_page.append(self.get_render_dict(competitor))
        if len(current_page) != 0:
            while len(current_page) != self.per_page:
                current_page.append(self.get_render_dict(Competitor(-1, "2042DUMM00", "No Name", "Germany", "de", 0, [], [])))
            pages.append(current_page)
        self.pages = pages
                
        self.event_index = {event: i for i, event in enumerate(self.events)}
        self.event_times = OrderedDict(sorted(competitors.event_times.items(), key=lambda x: (self.event_index[x[0][0]], x[0][1])))
        self.event_r1_times = OrderedDict(sorted([(event, t) for (event, round), t in competitors.event_times.items() if round == 1], key=lambda x: self.event_index[x[0]]))
        self.template = self.jinja.get_template(self.template_path.name)

    def render(self):
        self.template = self.jinja.get_template(self.template_path.name)
        return self.template.render(pages=self.pages, wca_events=self.events, event_times=self.event_times, event_r1_times=self.event_r1_times)

    def render_file(self, competitors: CompetitorData, out_path) -> str:
        self.setup(competitors)
        rendered = self.render()
        with open(out_path, "w", encoding="utf8") as file:
            file.write(rendered)
            

    def competition_count_to_emoji(self, comp_count):
        emoji = ""
        for k, v in self.exp_emoji.items():
            if comp_count >= int(k):
                emoji = v
        return emoji
