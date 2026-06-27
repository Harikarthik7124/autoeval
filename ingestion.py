import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GH_TOKEN_PAT") or os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def fetch_user_profile(username):
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def fetch_repositories(username):
    url = f"https://api.github.com/users/{username}/repos"
    params = {"per_page": 30, "sort": "updated"}
    response = requests.get(url, headers=HEADERS, params=params)
    repos = response.json()
    
    # filter out the profile README repo (same name as username)
    repos = [r for r in repos if r["name"] != username]
    
    return repos

def fetch_commits(username, repo_name):
    url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
    params = {"per_page": 10}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()

def check_readme(username, repo_name):
    url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
    response = requests.get(url, headers=HEADERS)
    return response.status_code == 200   # True if README exists, False if not

def build_profile_summary(username):
    print(f"Fetching profile for: {username}")

    profile  = fetch_user_profile(username)
    repos    = fetch_repositories(username)

    languages      = []
    readme_count   = 0
    total_stars    = 0
    recent_commits = 0

    for repo in repos:
        # collect language
        if repo.get("language"):
            languages.append(repo["language"])
            # Jupyter Notebook means Python underneath
            if repo["language"] == "Jupyter Notebook":
                languages.append("Python")

        # check actual README file exists
        if check_readme(username, repo["name"]):
            readme_count += 1

        # count stars
        total_stars += repo.get("stargazers_count", 0)

        # count recent commits
        commits = fetch_commits(username, repo["name"])
        if isinstance(commits, list):
            recent_commits += len(commits)

    summary = {
        "username"        : username,
        "name"            : profile.get("name", username),
        "public_repos"    : profile.get("public_repos", 0),
        "followers"       : profile.get("followers", 0),
        "languages"       : list(set(languages)),
        "total_stars"     : total_stars,
        "has_readme_count": readme_count,
        "recent_commits"  : recent_commits,
        "top_repo"        : repos[0]["name"] if repos else "None",
        "bio"             : profile.get("bio", ""),
    }

    return summary

if __name__ == "__main__":
    summary = build_profile_summary("Harikarthik7124")
    for key, value in summary.items():
        print(f"{key}: {value}")