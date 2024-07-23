import pathlib
import os
import requests
import zipfile
import polars as pl
import json
import warnings
from typing import List, Dict
from dataclasses import dataclass

_DATA_ = (pathlib.Path(__file__).parent.parent / "data").absolute()


def update_data():
    os.makedirs(_DATA_, exist_ok=True)
    r = requests.get("https://www.worldcubeassociation.org/export/results/WCA_export.tsv.zip")
    with open(_DATA_ / "export.zip", "wb") as file:
        file.write(r.content)
    with zipfile.ZipFile(_DATA_ / "export.zip", "r") as file:
        file.extractall(_DATA_)

@dataclass
class Assignment:
    event: str
    round: int
    group: int
    role: str

@dataclass
class Competitor:
    idx: int
    wca_id: int
    name: str
    country: str
    num_competitions: int
    assignments: List[Assignment]

class CompetitorData:
    def __init__(self, comp_id) -> None:
        self.data = None
        self.competitor_assignments = None
        self.comp_id = comp_id
        self.comp_name = None
        self.prepare_data()
        self.index = 0
        pass

    def prepare_data(self):
        comp_data = json.loads(requests.request("GET", f'https://worldcubeassociation.org/api/v0/competitions/{self.comp_id}/wcif/public').content)
        competitor_data = pl.DataFrame(comp_data['persons'])

        # count the number of competitions each competitor has been to
        comp_counts = (
            pl.scan_csv(_DATA_ / "WCA_export_Results.tsv", separator="\t")
            .group_by(['personId'])
            .agg(
                pl.col("competitionId").n_unique().alias("numComps")
                ))
        self.data = (
            competitor_data.lazy()
            .join(comp_counts, left_on="wcaId", right_on="personId", how="left")
            .join(pl.scan_csv(_DATA_ / "WCA_export_Countries.tsv", separator="\t"), left_on='countryIso2', right_on='iso2')
            .select('registrantId', 'wcaId', 'name', pl.col("id").alias("country"), pl.col("numComps").fill_null(0) + 1)
            .sort("name")
            .collect()
        )
        
        activities = {}
        for venue in comp_data['schedule']['venues']:
            	for room in venue['rooms']:
                    for activity in room["activities"]:
                        for child_activity in activity['childActivities']:                      
                            event, round_, group = child_activity['activityCode'].split('-')[:3]
                            activities[child_activity['id']] = {
                                'event': event,
                                'round': int(round_[1:]),
                                'group': int(group[1:])
                            }
        competitor_assignments = {}
        for person in comp_data['persons']:
            person_assignments = []
            for assignment in person['assignments']:
                activity_id = assignment['activityId']
                try:
                    activity = activities[activity_id]
                    role = assignment['assignmentCode']
                    person_assignments.append(Assignment(activity['event'], activity['round'], activity['group'], role))
                except KeyError as e:
                    warnings.warn("Assignments other than competitor/judge/scrambler are not yet supported")
            competitor_assignments[person['registrantId']] = person_assignments
        self.competitor_assignments = competitor_assignments
        self.comp_name = comp_data['shortName']

    def __getitem__(self, key: int) -> Competitor:
        idx, wca_id, name, country, num_competitions = self.data.row(key)
        return Competitor(idx, wca_id, name, country, num_competitions, self.competitor_assignments[idx])

    def __len__(self):
        return self.data.shape[0]

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self):
            raise StopIteration
        x = self[self.index]
        self.index += 1
        return x





        
