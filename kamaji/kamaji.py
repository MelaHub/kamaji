import click
from pathlib import Path
import pandas as pd
import csv
import json
import seaborn as sn
import calendar
from typing import TypedDict

class Activity(TypedDict):
    S: str

class ActivityList(TypedDict):
    L: list[Activity]

class YearActivities(TypedDict):
    M: dict[str, list[ActivityList]]

def __generate_pd(activities: dict[str, YearActivities]) -> pd.DataFrame:
    data = [[0] * 12 for i in range(1, 32)]
    for activities_date in activities:
        activity_month, activity_day = activities_date.split("-")
        activities_year = activities[activities_date]["M"]
        for activity_year in activities_year:
            data[int(activity_day) - 1][int(activity_month) - 1] += len(
                activities_year[activity_year]["L"]
            )
    return pd.DataFrame(data, index=[i for i in range(1, 32)], columns=[calendar.month_name[i][0:3] for i in range(1, 13)])


def __retrieve_activities(activities_file_path: Path) -> dict[str, YearActivities]:
    str_activities = {}
    with open(activities_file_path) as csvfile:
        reader = csv.DictReader(csvfile)
        str_activities = [row for row in reader][0]["attributes"]
    return json.loads(str_activities)


@click.command()
@click.option("--activities-file-path", type=Path, required=True)
@click.option("--output-file-path", type=Path, required=True)
def activities_heat_map(activities_file_path: Path, output_file_path: Path):
    activities = __retrieve_activities(activities_file_path)
    pd_activities = __generate_pd(activities)
    svm = sn.heatmap(
        pd_activities, annot=True, cmap="coolwarm", linecolor="white", linewidths=1
    )
    figure = svm.get_figure()
    figure.savefig(output_file_path, dpi=400)
