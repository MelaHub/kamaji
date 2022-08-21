import click
from pathlib import Path
import pandas as pd
import csv
import json
import seaborn as sn


def __generate_pd(activities):
    data = [[0] * 12 for i in range(1, 32)]
    for activities_date in activities:
        activity_month, activity_day = activities_date.split("-")
        activities_year = activities[activities_date]["M"]
        for activity_year in activities_year:
            data[int(activity_day) - 1][int(activity_month) - 1] += len(
                activities_year[activity_year]["L"]
            )
    return pd.DataFrame(data, index=[i for i in range(1, 32)], columns=['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])


def __retrieve_activities(activities_file_path):
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
