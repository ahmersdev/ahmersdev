#!/usr/bin/env python3
"""
Fetches live GitHub stats for a user and renders them into
dark_mode.svg / light_mode.svg terminal-style cards.

Requires an environment variable ACCESS_TOKEN with a GitHub
Personal Access Token that has 'read:user' and 'repo' scope
(so it can see stats on private repos too, if desired).
"""

import os
import datetime
import requests

USERNAME = os.environ.get("GITHUB_USERNAME", "ahmersdev")
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
HEADERS = {"Authorization": f"bearer {ACCESS_TOKEN}"}
GRAPHQL_URL = "https://api.github.com/graphql"

TAGLINE = "Full-Stack Engineer"
TECH_LINE_1 = "React.js, Next.js, TypeScript, Node.js, NestJS"
TECH_LINE_2 = "PostgreSQL, MongoDB, React Native, AWS, Docker"
EMAIL = "official.ahmersdev@gmail.com"
LINKEDIN = "linkedin.com/in/ahmersdev"
PORTFOLIO = "ahmersdev.com"


def run_query(query, variables=None):
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def get_account_created_year():
    query = """
    query($login: String!) {
      user(login: $login) { createdAt }
    }
    """
    data = run_query(query, {"login": USERNAME})["user"]
    return int(data["createdAt"][:4])


def get_user_overview():
    # ownerAffiliations OWNER + ORGANIZATION_MEMBER picks up org repos too.
    # Dropping the `privacy` filter (rather than hardcoding PUBLIC) includes
    # private repos as well, since we're authenticated as the account owner.
    query = """
    query($login: String!, $cursor: String) {
      user(login: $login) {
        name
        followers { totalCount }
        repositories(
          ownerAffiliations: [OWNER, ORGANIZATION_MEMBER]
          first: 100
          after: $cursor
          isFork: false
        ) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes {
            nameWithOwner
            stargazers { totalCount }
          }
        }
      }
    }
    """
    repos = []
    cursor = None
    name = None
    followers = 0
    while True:
        data = run_query(query, {"login": USERNAME, "cursor": cursor})["user"]
        name = data["name"] or USERNAME
        followers = data["followers"]["totalCount"]
        repos.extend(data["repositories"]["nodes"])
        page = data["repositories"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]

    stars = sum(r["stargazers"]["totalCount"] for r in repos)

    # Full-history commit count: contributionsCollection only covers the
    # trailing 12 months per call, so sum it year by year since account creation.
    start_year = get_account_created_year()
    current_year = datetime.datetime.utcnow().year
    commit_query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """
    total_commits = 0
    for year in range(start_year, current_year + 1):
        from_dt = f"{year}-01-01T00:00:00Z"
        to_dt = f"{year}-12-31T23:59:59Z"
        cc = run_query(commit_query, {"login": USERNAME, "from": from_dt, "to": to_dt})
        coll = cc["user"]["contributionsCollection"]
        total_commits += coll["totalCommitContributions"] + coll["restrictedContributionsCount"]

    return {
        "name": name,
        "followers": followers,
        "repos": len(repos),
        "stars": stars,
        "commits": total_commits,
        "repo_full_names": [r["nameWithOwner"] for r in repos],
    }


def get_lines_changed(repo_full_names):
    """
    Sums additions/deletions across the given repos (owner:name form, as
    returned by the GraphQL query, so private + org repos are included as
    long as the token has access) using the REST stats/contributors endpoint.

    GitHub computes these stats lazily and returns 202 with an empty body
    on the first request while it caches them in the background — this
    retries a few times with a short delay before giving up on a repo.
    """
    import time

    additions = 0
    deletions = 0
    for full_name in repo_full_names:
        stats_url = f"https://api.github.com/repos/{full_name}/stats/contributors"
        data = None
        for attempt in range(4):
            r = requests.get(stats_url, headers=HEADERS, timeout=30)
            if r.status_code == 200 and r.text.strip():
                data = r.json()
                break
            if r.status_code == 202:
                time.sleep(3)  # stats still computing, give GitHub a moment
                continue
            break  # 403/404/etc — skip this repo
        if not isinstance(data, list):
            continue
        for contributor in data:
            if contributor.get("author", {}) and contributor["author"].get("login") == USERNAME:
                for week in contributor.get("weeks", []):
                    additions += week.get("a", 0)
                    deletions += week.get("d", 0)
    return additions, deletions


def format_number(n):
    return f"{n:,}"


def render_svg(template_path, output_path, values):
    with open(template_path, "r") as f:
        svg = f.read()
    for key, val in values.items():
        svg = svg.replace("{{" + key + "}}", str(val))
    with open(output_path, "w") as f:
        f.write(svg)


def main():
    overview = get_user_overview()
    additions, deletions = get_lines_changed(overview["repo_full_names"])

    values = {
        "FULL_NAME": overview["name"],
        "TAGLINE": TAGLINE,
        "REPOS": format_number(overview["repos"]),
        "COMMITS": format_number(overview["commits"]),
        "STARS": format_number(overview["stars"]),
        "FOLLOWERS": format_number(overview["followers"]),
        "LINES_ADDED": format_number(additions),
        "LINES_DELETED": format_number(deletions),
        "TECH_LINE_1": TECH_LINE_1,
        "TECH_LINE_2": TECH_LINE_2,
        "EMAIL": EMAIL,
        "LINKEDIN": LINKEDIN,
        "PORTFOLIO": PORTFOLIO,
        "LAST_UPDATED": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

    render_svg("dark_mode_template.svg", "dark_mode.svg", values)
    render_svg("light_mode_template.svg", "light_mode.svg", values)
    print("SVGs updated:", values)


if __name__ == "__main__":
    main()