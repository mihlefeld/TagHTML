import pathlib
import math
import countryflag
import copy
import json
import tqdm
from collections import defaultdict
from typing import List
from bs4 import BeautifulSoup, Tag, NavigableString
from .datahandler import Competitor, CompetitorData

__TEMPLATE__ = pathlib.Path(__file__).absolute().parent.parent / "template.html"
__EXP_EMOJI__ = pathlib.Path(__file__).absolute().parent.parent / "experience_emoji.json"
__FORMATS__ = {
    "A4": (21.0, 29.7),
    "Letter": (21.59, 27.94)
}

def iso2flag(iso2: str):
    return ''.join([chr(127397 + ord(c)) for c in iso2.upper()])


class BS4Renderer:
    def __init__(self, width, height, template_path=__TEMPLATE__, exp_emoji_path=__EXP_EMOJI__, format="A4") -> None:
        self.page_width, self.page_height = __FORMATS__[format]
        self.tag_width = width
        self.tag_height = height
        self.columns = int(math.floor(self.page_width / width))
        self.rows = int(math.floor(self.page_height / height))
        self.per_page = self.columns * self.rows
        with open(template_path) as file:
            markup = file.read()
        self.bs = BeautifulSoup(markup, features="html.parser")
        self.bs.find(name='style').string += "@page {size: " + format + "; margin: 0; }"
        self.front_tag_template = self.bs.find(id='front-tag').extract()
        self.back_tag_template = self.bs.find(id='back-tag').extract()
        self.exp_emoji = json.load(open(exp_emoji_path, encoding="UTF-8"))
    

    def render(self, competitors: CompetitorData, out_path):
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

        for page in tqdm.tqdm(pages, desc="Organizing pages"):
            front_page = Tag(name="div", attrs={'class': 'page', "style": f"width: {self.page_width}cm; height: {self.page_height}cm"})
            back_page = Tag(name="div", attrs={'class': 'page', "style": f"width: {self.page_width}cm; height: {self.page_height}cm; flex-direction: row-reverse;"})
            for i, row in enumerate(page):
                for j, competitor in enumerate(row):
                    item = self.replace_fill_tags(self.front_tag_template, competitor, i==0, j==0)
                    front_page.append(item)
                    item = self.replace_fill_tags(self.back_tag_template, competitor, i==0, j==0)
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

    def replace_fill_tags(self, name_tag: Tag, competitor: Competitor, top_border: bool, left_border: bool):
        # front-tag
        nt = copy.copy(name_tag)
        def replace_contents(tg, cls, content):
            for x in tg.find_all(class_=cls):
                x.string = NavigableString(str(content))
        
        replace_contents(nt, "fill-comp-name", self.comp_name)
        replace_contents(nt, "fill-person-name", competitor.name)
        replace_contents(nt, "fill-wca-id", competitor.wca_id)
        replace_contents(nt, "fill-c-id", competitor.idx)
        replace_contents(nt, "fill-country-name", competitor.country)
        replace_contents(nt, "fill-country-emoji", iso2flag(competitor.iso2))
        replace_contents(nt, "fill-competition-count", competitor.num_competitions)
        replace_contents(nt, "fill-experience-emoji", self.competition_count_to_emoji(competitor.num_competitions))
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
            event_key = ["333","222","444","555","666","777","333bf","333fm","333oh","clock","minx","pyram","skewb","sq1","444bf","555bf","333mbf"]
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