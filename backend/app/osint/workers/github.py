import time
import httpx

from ...config import load_settings

API="https://api.github.com"


async def github_worker(query:str):

    settings=load_settings()

    headers={
        "Accept":"application/vnd.github+json",
        "User-Agent":"AIGlass"
    }

    if settings.github_token:
        headers["Authorization"]=f"Bearer {settings.github_token}"

    start=time.perf_counter()

    async with httpx.AsyncClient(timeout=20) as client:

        search=await client.get(
            API+"/search/users",
            params={
                "q":query,
                "per_page":1,
            },
            headers=headers,
        )

        if search.status_code!=200:

            print("GitHub Status:", search.status_code)
            print(search.text)

            return {
                "provider":"github",
                "success":False,
                "confidence":0,
                "latency_ms":0,
                "data":{
                    "status":search.status_code,
                    "body":search.text,
                },
            }

        items=search.json().get("items",[])

        if not items:

            return {
                "provider":"github",
                "success":True,
                "confidence":0,
                "latency_ms":0,
                "data":{},
            }

        username=items[0]["login"]

        profile=await client.get(
            API+"/users/"+username,
            headers=headers,
        )

        repos=await client.get(
            API+"/users/"+username+"/repos",
            params={
                "sort":"updated",
                "per_page":5,
            },
            headers=headers,
        )

    latency=int((time.perf_counter()-start)*1000)

    profile_json=profile.json()

    repo_json=repos.json()

    languages={}

    repo_list=[]

    for repo in repo_json:

        lang=repo.get("language")

        if lang:
            languages[lang]=languages.get(lang,0)+1

        repo_list.append({
            "name":repo["name"],
            "language":repo.get("language"),
            "stars":repo.get("stargazers_count"),
            "updated":repo.get("updated_at"),
        })

    return {

        "provider":"github",

        "success":True,

        "confidence":0.9,

        "latency_ms":latency,

        "data":{

            "username":profile_json.get("login"),

            "name":profile_json.get("name"),

            "company":profile_json.get("company"),

            "location":profile_json.get("location"),

            "bio":profile_json.get("bio"),

            "followers":profile_json.get("followers"),

            "following":profile_json.get("following"),

            "public_repos":profile_json.get("public_repos"),

            "blog":profile_json.get("blog"),

            "languages":languages,

            "repos":repo_list,

        }
    }
