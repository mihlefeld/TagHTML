import pathlib
import os
import requests
import zipfile
import polars as pl
import warnings
import datetime
from rich.progress import Progress
from typing import List
from dataclasses import dataclass

_DATA_ = (pathlib.Path(__file__).parent.parent / "data").absolute()


def update_data():
    with Progress() as p:
        ted = p.add_task("Downloading export", total=1)
        os.makedirs(_DATA_, exist_ok=True)
        r = requests.get("https://www.worldcubeassociation.org/export/results/WCA_export.tsv.zip")
        p.update(ted, completed=1)
        twf = p.add_task("Writing to file", total=1)
        with open(_DATA_ / "export.zip", "wb") as file:
            file.write(r.content)
        p.update(twf, completed=1)
        ext = p.add_task("Extracting", total=1)
        with zipfile.ZipFile(_DATA_ / "export.zip", "r") as file:
            file.extractall(_DATA_)
        p.update(ext, completed=1)

@dataclass
class Assignment:
    event: str
    round: int
    group: int
    role: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    group_start_time: datetime.datetime
    group_end_time: datetime.datetime
    room_name: str

@dataclass
class Competitor:
    idx: int
    wca_id: int
    name: str
    country: str
    iso2: str
    num_competitions: int
    assignments: List[Assignment]
    roles: List[str]

class CompetitorData:
    def __init__(self, comp_id) -> None:
        self.data = None
        self.competitor_assignments = None
        self.comp_id = comp_id
        self.comp_name = None
        self.event_times: dict[(str, int), (datetime.datetime, datetime.datetime)] = {}
        self.prepare_data()
        self.index = 0

    def prepare_data(self):
        comp_data = requests.request("GET", f'https://worldcubeassociation.org/api/v0/competitions/{self.comp_id}/wcif/public').json()
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
            .select(
                'registrantId', 'wcaId', 'name', 
                pl.col("id").alias("country"), 
                pl.col("countryIso2").alias('iso2'), 
                pl.col("numComps").fill_null(0) + 1,
                'roles'
            )
            .sort("name")
            .collect()
        )
        
        activities = {}
        for venue in comp_data['schedule']['venues']:
            	for room in venue['rooms']:
                    for activity in room["activities"]:
                        child_activities = activity['childActivities']
                        if 'other' not in activity['activityCode'] and not child_activities:
                            child_activities = [activity]
                        for child_activity in child_activities:
                            try:
                                event, round_, group = child_activity['activityCode'].split('-')[:3]
                            except:
                                continue
                            start_time = datetime.datetime.strptime(activity["startTime"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.UTC).astimezone()
                            end_time = datetime.datetime.strptime(activity["endTime"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.UTC).astimezone()
                            group_start_time = datetime.datetime.strptime(child_activity["startTime"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.UTC).astimezone()
                            group_end_time = datetime.datetime.strptime(child_activity["endTime"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.UTC).astimezone()
                            activities[child_activity['id']] = {
                                'event': event,
                                'round': int(round_[1:]),
                                'group': int(group[1:]),
                                'start_time': start_time,
                                'group_start_time': group_start_time,
                                'group_end_time': group_end_time,
                                'end_time': end_time,
                                'room_name': room['name'].lower().replace(' ', '-'),
                            }
                            key = (event, int(round_[1:]))
                            if key not in self.event_times: # TODO: change to list for mbld and fmc
                                self.event_times[key] = (start_time, end_time)
        competitor_assignments = {}
        for person in comp_data['persons']:
            person_assignments = []
            for assignment in person['assignments']:
                activity_id = assignment['activityId']
                try:
                    activity = activities[activity_id]
                except KeyError as e:
                    # warnings.warn(f"Tried to access non-existant activity {activity_id}")
                    continue
                try:
                    role = assignment['assignmentCode'].replace("staff-", "").replace("stagelead", "lead")
                    if role not in ["competitor", "runner", "judge", "scrambler", "delegate", "lead"]:
                        continue

                    person_assignments.append(Assignment(
                            role=role, 
                            **activity
                        )
                    )
                except KeyError as e:
                    warnings.warn(f"Assignments other than competitor/judge/scrambler are not yet supported {assignment}")
            competitor_assignments[person['registrantId']] = person_assignments
        self.competitor_assignments = competitor_assignments
        self.comp_name = comp_data['shortName']

    def __getitem__(self, key: int) -> Competitor:
        idx, wca_id, name, country, iso2, num_competitions, roles = self.data.row(key)
        return Competitor(idx, wca_id, name, country, iso2, num_competitions, self.competitor_assignments[idx], roles)

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





        
