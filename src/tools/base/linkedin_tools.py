import os
import requests
from src.utils import invoke_llm


def extract_linkedin_url_base(search_results):
    """
    Extracts the LinkedIn URL from the search results.
    """
    for result in search_results:
        if "linkedin.com/in" in result["link"]:
            return result["link"]
    return ""


def extract_linkedin_url(search_results):
    EXTRACT_LINKEDIN_URL_PROMPT = """
    **Role:**  
    You are an expert in extracting LinkedIn URLs from Google search results, specializing in finding the correct personal LinkedIn URL.

    **Objective:**  
    From the provided search results, find the LinkedIn URL of a specific person working at a specific company.

    **Instructions:**  
    1. Output **only** the correct LinkedIn URL if found, nothing else.  
    2. If no valid URL exists, output **only** an empty string.  
    3. Only consider URLs with `"/in"`. Ignore those with `"/posts"` or `"/company"`.  
    """

    result = invoke_llm(
        system_prompt=EXTRACT_LINKEDIN_URL_PROMPT,
        user_message=str(search_results),
        model="gemini-2.5-pro",
    )
    return result


def scrape_linkedin(linkedin_url, is_company=False):
    """
    Scrapes LinkedIn profile data based on the provided LinkedIn URL.

    @param linkedin_url: The LinkedIn URL to scrape.
    @param is_company: Boolean indicating whether to scrape a company profile or a person profile.
    @return: The scraped LinkedIn profile data.
    """
    if is_company:
        url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-company-by-linkedinurl"

        querystring = {"linkedin_url": linkedin_url}
    else:
        url = "https://fresh-linkedin-profile-data.p.rapidapi.com/enrich-lead"
        querystring = {
            "linkedin_url": linkedin_url,
            "include_skills": "true",
            "include_certifications": "true",
            "include_publications": "true",
            "include_honors": "true",
            "include_volunteers": "true",
            "include_projects": "true",
            "include_patents": "true",
            "include_courses": "true",
            "include_organizations": "true",
            "include_profile_status": "true",
            "include_company_public_url": "true",
        }

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com",
    }

    # Ensure RapidAPI key is configured
    if not headers.get("x-rapidapi-key"):
        print("RapidAPI key not configured; skipping LinkedIn scrape.")
        return {}
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        data = response.json()
        return data if isinstance(data, dict) else {}
    else:
        print(f"Request failed with status code: {response.status_code}")
        return {}
