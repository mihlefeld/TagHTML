import pathlib
import math
import copy
import json
import datetime
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

def prepare_name(name: str):
    no_original_name = name.split(" (")[0]
    parts = no_original_name.split()
    ret = Tag(name="span")
    if len(parts) == 2:
        ret.append(NavigableString(parts[0]))
        ret.append(BeautifulSoup("<br>", 'html.parser').br)
        ret.append(NavigableString(parts[1]))
        return ret
    ret.string = NavigableString(no_original_name)
    return ret


class BS4Renderer:
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
        with open(template_path, encoding="utf-8") as file:
            markup = file.read()
        self.bs = BeautifulSoup(markup, features="html.parser")
        self.bs.find(name='style').string += "@page {size: " + format + "; margin: 0; }"
        self.front_tag_template = self.bs.find(id='front-tag').extract()
        self.back_tag_template = self.bs.find(id='back-tag').extract()
        self.exp_emoji = json.load(open(exp_emoji_path, encoding="UTF-8"))
        self.people_emoji: dict = json.load(open(people_emoji_path, encoding="UTF-8"))
        assert isinstance(self.people_emoji, dict)
        self.cid_modulo_emoji = json.load(open(cid_modulo_emoji_path, encoding="UTF-8"))
        if isinstance(self.cid_modulo_emoji, dict):
            self.cid_modulo_emoji = list(self.cid_modulo_emoji.values())
    
    

    def render(self, competitors: CompetitorData, out_path, progress: Progress):
        self.comp_name = competitors.comp_name
        body = Tag(name="body")
        front_page = None
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
            current_row.append(competitor)
        if len(current_row) != 0:
            current_page.append(current_row)
            pages.append(current_page)

        for page in progress.track(pages, description="Organizing pages"):
            front_page = Tag(name="div", attrs={'class': 'page', "style": f"width: {self.page_width}cm; height: {self.page_height}cm"})
            back_page = Tag(name="div", attrs={'class': 'page', "style": f"width: {self.page_width}cm; height: {self.page_height}cm; flex-direction: row-reverse;"})
            for i, row in enumerate(page):
                for j, competitor in enumerate(row):
                    item = self.replace_fill_tags(self.front_tag_template, competitor, competitors.event_times)
                    front_page.append(item)
                    item = self.replace_fill_tags(self.back_tag_template, competitor, competitors.event_times)
                    back_page.append(item)

            # insert spacer nametags to facilitate correct matching for two-sided printing
            for j in range(self.per_page - (len(row) + i * self.columns)):
                empty_tag = Tag(name="div", attrs={"class": "tag border-top border-left"})
                back_page.append(copy.copy(empty_tag))
                front_page.append(empty_tag)
            
            body.append(front_page)
            body.append(back_page)

        self.bs.find('body').replace_with(body)
        with open(out_path, "w", encoding='UTF-8') as file:
            file.write(self.bs.prettify())

    def competition_count_to_emoji(self, comp_count):
        emoji = ""
        for k, v in self.exp_emoji.items():
            if comp_count >= int(k):
                emoji = v
        return emoji

    def replace_fill_tags(self, name_tag: Tag, competitor: Competitor, event_times: dict[(str, int), (datetime.datetime, datetime.datetime)]):
        events = ["333","222","444","555","666","777","333bf","333fm","333oh","clock","minx","pyram","skewb","sq1","444bf","555bf","333mbf"]
        # front-tag
        nt = copy.copy(name_tag)
        def replace_contents(tg, cls, content):
            for x in tg.find_all(class_=cls):
                x.string = NavigableString(str(content))
        
        def replace_children(tg, cls, content):
            for x in tg.find_all(class_=cls):
                x: Tag
                x.clear()
                x.append(copy.copy(content))

        def replace_class(tg: Tag, cls, replacement):
            if cls in tg["class"]:
                tg["class"] = [class_name for class_name in tg["class"] + replacement if class_name != cls]
            for x in tg.find_all(class_=cls):
                x: Tag
                x["class"] = [class_name for class_name in x["class"] + replacement if class_name != cls]
        
        replace_contents(nt, "fill-comp-name", self.comp_name)
        replace_children(nt, "fill-person-name", prepare_name(competitor.name))
        replace_contents(nt, "fill-person-name-direct", competitor.name)
        replace_contents(nt, "fill-wca-id", competitor.wca_id)
        replace_contents(nt, "fill-c-id", competitor.idx if competitor.idx is not None else "")
        replace_contents(nt, "fill-country-name", competitor.country)
        replace_contents(nt, "fill-country-emoji", iso2flag(competitor.iso2))
        replace_contents(nt, "fill-competition-count", competitor.num_competitions)
        replace_contents(nt, "fill-experience-emoji", self.competition_count_to_emoji(competitor.num_competitions))
        replace_contents(nt, "fill-cid-modulo-emoji", self.cid_modulo_emoji[competitor.idx % len(self.cid_modulo_emoji)] if competitor.idx is not None else "")
        replace_contents(nt, "fill-people-emoji", self.people_emoji.get(competitor.wca_id, ""))
        replace_children(nt, "fill-country-flag", Tag(name="img", attrs={"src": f"graphics/flags/{competitor.iso2.lower()}.png"}))
        replace_class(nt, "replace-class-competition-role", competitor.roles)
        grouped_assignments: dict[(str, str), list[Assignment]] = defaultdict(list)
        for event in events:
            start, end = "", ""
            if (event, 1) in event_times:
                start_, end_ = event_times[(event, 1)]
                start = start_.strftime("%a %H:%M")
            replace_contents(nt, f"fill-{event}-r1-time", start)
            replace_contents(nt, f"fill-{event}-r1-c-assignment", "-")
            replace_contents(nt, f"fill-{event}-r1-assignments", "-")
        for assignment in competitor.assignments:
            grouped_assignments[(assignment.event, assignment.round)].append(assignment)
        active_events = []
        for (event, round), assignment_group in grouped_assignments.items():
            active_events.append(event)
            for assignment in assignment_group:
                if assignment.role[0].lower() == "c":
                    replace_contents(nt, f"fill-{event}-r{round}-c-assignment", assignment.group)
            assignment = assignment_group[0]
            replace_contents(nt, f"fill-{event}-r{round}-time", assignment.start_time.strftime("%a %H:%M"))
            help_assignments = []
            for assignment in assignment_group:
                if assignment.role[0].lower() == "c":
                    continue
                help_assignments.append(f"{assignment.role[0].upper()}{assignment.group}")
            help_assignments = " ".join(help_assignments) if help_assignments else "-"
            replace_contents(nt, f"fill-{event}-r{round}-assignments", help_assignments)
            replace_class(nt, f"replace-class-{event}-r1-active", ["event-active"])
            # replace_contents(assignment.)
        for event in active_events:
            replace_class(nt, f"replace-class-{event}-r1-active", ["event-active"])
        for event in set(events).difference(active_events):
            replace_class(nt, f"replace-class-{event}-r1-active", ["event-inactive"])
        if "style" in nt.attrs:
            nt.attrs['style'] += f"width: {self.tag_width}cm; height: {self.tag_height}cm;"
        else:
            nt.attrs['style'] = f"width: {self.tag_width}cm; height: {self.tag_height}cm;"
        
        row_template = nt.find(class_="fill-row-template")
        if row_template:
            parent = row_template.parent
            rt = row_template.extract()
            grouped_assignments = defaultdict(lambda: defaultdict(list))
            for assignment in competitor.assignments:
                if assignment.round == 1:
                    grouped_assignments[assignment.event][assignment.role].append(str(assignment.group))
            event_key = events
            event_key = {x: i for i, x in enumerate(event_key)}
            grouped_assignments_sorted = sorted(grouped_assignments.items(), key=lambda x: event_key[x[0]])
            for event, eventd in grouped_assignments_sorted:
                rtc = copy.copy(rt)
                for role, group in eventd.items():
                    content_str = ",".join(group)
                    replace_contents(rtc, f'fill-assignment-{role[0]}', content_str)
                rtc.find(class_="fill-event-image").attrs['src'] = f"graphics/svgs/{event}.svg"
                parent.append(rtc)

        return nt