#!/usr/bin/env python3
"""Scrape all reviews for one or more RateMyProfessors professors via their GraphQL API."""

import base64
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
# Public auth token embedded in RMP's JS bundle
AUTH_TOKEN = "dGVzdDp0ZXN0"

HEADERS = {
    "Authorization": f"Basic {AUTH_TOKEN}",
    "Content-Type": "application/json",
    "Referer": "https://www.ratemyprofessors.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

PROFESSOR_QUERY = """
query TeacherRatingsPageQuery($id: ID!) {
  node(id: $id) {
    __typename
    ... on Teacher {
      id
      legacyId
      firstName
      lastName
      department
      school {
        name
        city
        state
      }
      avgRating
      avgDifficulty
      numRatings
      wouldTakeAgainPercent
    }
  }
}
"""

RATINGS_QUERY = """
query RatingsListQuery($count: Int!, $id: ID!, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      ratings(first: $count, after: $cursor) {
        edges {
          node {
            date
            class
            qualityRating
            difficultyRatingRounded
            comment
            grade
            wouldTakeAgain
            ratingTags
            flagStatus
            teacherNote {
              comment
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""


def legacy_id_to_graphql_id(legacy_id: int) -> str:
    return base64.b64encode(f"Teacher-{legacy_id}".encode()).decode()


def graphql(query: str, variables: dict) -> dict:
    resp = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_professor(graphql_id: str) -> dict:
    data = graphql(PROFESSOR_QUERY, {"id": graphql_id})
    return data["data"]["node"]


def fetch_all_ratings(graphql_id: str) -> list[dict]:
    ratings = []
    cursor = None

    while True:
        variables = {"count": 20, "id": graphql_id}
        if cursor:
            variables["cursor"] = cursor

        data = graphql(RATINGS_QUERY, variables)
        ratings_data = data["data"]["node"]["ratings"]
        edges = ratings_data["edges"]
        ratings.extend(edge["node"] for edge in edges)

        page_info = ratings_data["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    return ratings


def print_professor(prof: dict) -> None:
    school = prof.get("school") or {}
    print(f"\n{'='*60}")
    print(f"Professor: {prof['firstName']} {prof['lastName']}")
    print(f"School:    {school.get('name', 'N/A')} ({school.get('city')}, {school.get('state')})")
    print(f"Dept:      {prof.get('department', 'N/A')}")
    print(f"Avg Rating:     {prof.get('avgRating')}/5.0")
    print(f"Avg Difficulty: {prof.get('avgDifficulty')}/5.0")
    print(f"Would Take Again: {prof.get('wouldTakeAgainPercent'):.0f}%")
    print(f"Total Ratings: {prof.get('numRatings')}")
    print(f"{'='*60}\n")


def print_ratings(ratings: list[dict]) -> None:
    for i, r in enumerate(ratings, 1):
        tags = r.get("ratingTags", "") or ""
        tag_list = [t.strip() for t in tags.split("--") if t.strip()]
        wta = r.get("wouldTakeAgain")
        wta_str = {1: "Yes", 0: "No"}.get(wta, "N/A")

        print(f"--- Review {i} ---")
        print(f"Date:       {r.get('date', 'N/A')[:10]}")
        print(f"Course:     {r.get('class', 'N/A')}")
        print(f"Quality:    {r.get('qualityRating')}/5")
        print(f"Difficulty: {r.get('difficultyRatingRounded')}/5")
        print(f"Grade:      {r.get('grade') or 'N/A'}")
        print(f"Would Take Again: {wta_str}")
        if tag_list:
            print(f"Tags:       {', '.join(tag_list)}")
        print(f"Review:     {r.get('comment', '').strip()}")
        note = (r.get("teacherNote") or {}).get("comment")
        if note:
            print(f"Prof Reply: {note.strip()}")
        print()


PROFESSOR_IDS = [
    2926663, 2445092, 2000580, 2099184, 281383,
    214947,  2922737, 2926378, 3015141, 2318479,
]


def main():
    ids = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else PROFESSOR_IDS

    all_data = {}
    for legacy_id in ids:
        graphql_id = legacy_id_to_graphql_id(legacy_id)
        print(f"\nFetching professor {legacy_id}...")

        prof = fetch_professor(graphql_id)
        if not prof or prof.get("__typename") != "Teacher":
            print(f"  Not found, skipping.")
            continue

        print_professor(prof)

        ratings = fetch_all_ratings(graphql_id)
        print(f"Found {len(ratings)} reviews.\n")
        print_ratings(ratings)

        all_data[str(legacy_id)] = {"professor": prof, "ratings": ratings}

    out_file = "rmp_all_professors.json"
    with open(out_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"All data saved to {out_file}")


if __name__ == "__main__":
    main()
