import sys
import sqlite3
from common.models import SiteHeadlines
from common.utils import build_s3_key, convert_objects_to_json_string, upload_data_to_s3
from datetime import datetime, timedelta


def iterate_dates(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date.strftime("%Y-%m-%d")
        current_date += timedelta(days=1)


print(sys.argv)

start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d")
end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d")
sqlite_path = sys.argv[3]
s3_bucket = sys.argv[4]
s3_prefix = sys.argv[5]


for date_str in iterate_dates(start_date, end_date):
    backfill_date = date_str

    print("=" * 20)
    print(f"Backfilling {date_str}...")
    print("-" * 20)

    query = f"""
        with records as (
        select scrapes.site, scrapes.day || ' ' ||scrapes.hour as date_time, trim(titles.title, ';') as title
        from titles join scrapes on titles.fk_scrapes=scrapes.pk_scrapes
        where scrapes.day = '{date_str}')

        select site, date_time, group_concat(title, ';')
        from records
        group by 1, 2;
        """

    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    headlines = [
        SiteHeadlines(
            name=record[0],
            timestamp=record[1],
            headlines=record[2].split(";"),
        )
        for record in data
    ]

    timestamps = {headline.timestamp for headline in headlines}

    for timestamp in timestamps:
        object_key = build_s3_key(prefix=s3_prefix, timestamp=timestamp, extension="json")
        headlines_to_load = list(filter(lambda h: h.timestamp == timestamp, headlines))
        print(f" Backfilling: {object_key}")
        s3_response: dict = upload_data_to_s3(
            bucket_name=s3_bucket,
            key=object_key,
            data=convert_objects_to_json_string(headlines_to_load),
        )
        http_status_code = s3_response.get("ResponseMetadata", {}).get("HTTPStatusCode", "n/a")
        print(f"HTTP status code of S3 response: {http_status_code}")
