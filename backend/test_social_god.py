import asyncio
import time
import httpx
import re
import urllib.parse

async def direct_github_osint(username_or_query: str):
    print(f"Starting Direct Endpoint OSINT for target: {username_or_query}")
    start_time = time.time()
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    async with httpx.AsyncClient() as client:
        # Step 1: Query global user directory fallback search index
        search_url = f"https://github.com{urllib.parse.quote(username_or_query)}"
        try:
            print("Querying public developer lookup index...")
            search_resp = await client.get(search_url, headers=headers, timeout=10.0)
            
            if search_resp.status_code == 200:
                search_data = search_resp.json()
                items = search_data.get("items", [])
                
                if not items:
                    print("No direct profile links caught in index layer. Trying profile prediction route...")
                    clean_target = re.sub(r"[^a-zA-Z0-9-]", "", username_or_query.split()[0].lower())
                    target_user = clean_target
                else:
                    target_user = items[0].get("login")
                
                # Step 2: Fetch full uncensored user profile data sheet
                url = f"https://github.com{target_user}"
                print(f"Fetching full public developer data layer: {url}")
                response = await client.get(url, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    dossier = [
                        f"Username: {data.get('login')}",
                        f"Name: {data.get('name')}",
                        f"Company: {data.get('company')}",
                        f"Bio: {data.get('bio')}",
                        f"Location: {data.get('location')}",
                        f"Public Repos: {data.get('public_repos')}",
                        f"Followers: {data.get('followers')}",
                        f"Blog/Website: {data.get('blog')}"
                    ]
                    
                    # Step 3: Grab recent active development paths
                    repos_url = data.get("repos_url")
                    if repos_url:
                        repos_resp = await client.get(repos_url, headers=headers, timeout=10.0)
                        if repos_resp.status_code == 200:
                            repos_data = repos_resp.json()[:3]
                            dossier.append("\n--- Recent Developer Activity ---")
                            for repo in repos_data:
                                dossier.append(f"Project: {repo.get('name')} | Language: {repo.get('language')} | Desc: {repo.get('description')}")
                    
                    profile_output = "\n".join(dossier)
                    print("\nSUCCESS! Extracted full public profile dossier.")
                    print(f"Preview for Claude Engine:\n{profile_output}")
                else:
                    print(f"User profile retrieval endpoint dropped with status code: {response.status_code}")
            else:
                print(f"Index engine check failed with status code: {search_resp.status_code}")
                
        except Exception as e:
            print(f"OSINT API Pipeline Failed: {str(e)}")
        finally:
            print(f"Total Execution Time: {round(time.time() - start_time, 2)} seconds")

# Test a broad text search query string matching our example target scenario
asyncio.run(direct_github_osint("Guillermo Rauch"))
