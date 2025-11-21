from pydantic import BaseModel, Field
from typing import List, Annotated
from typing_extensions import TypedDict
from operator import add


class SocialMediaLinks(BaseModel):
    blog: str = ""
    facebook: str = ""
    twitter: str = ""
    youtube: str = ""
    # Can add other platform


class Report(BaseModel):
    title: str = ""
    content: str = ""
    is_markdown: bool = False


# Define the base data needed about the lead
class LeadData(BaseModel):
    # id: str = Field(
    #     ...,
    #     description=(
    #         "The unique identifier for the lead being processed "
    #         "(for Google Sheets this is the row number)"
    #     ),
    # )
    id: str | None = None
    name: str = Field("", description="The full name of the lead")
    address: str = Field("", description="The address or location of the lead")
    email: str = Field("", description="The email address of the lead")
    phone: str = Field("", description="The phone number of the lead, if available")
    profile: str = Field(
        "",
        description="The lead profile summary from LinkedIn data, if available",
    )

    # Custom fields to reflect Apollo / healthcare CRM exports
    role: str = Field(
        "",
        description="The lead's job role or title, e.g. CIO, CFO, COO",
    )
    linkedin: str = Field(
        "",
        description="The lead's LinkedIn profile URL",
    )
    location: str = Field(
        "",
        description="The geographic location of the lead",
    )
    company: str = Field(
        "",
        description="The lead's company or organization name",
    )
    website: str = Field(
        "",
        description="The company website domain, if known",
    )


class CompanyData(BaseModel):
    name: str = ""
    profile: str = ""
    website: str = ""
    social_media_links: SocialMediaLinks = SocialMediaLinks()


class GraphInputState(TypedDict):
    leads_ids: List[str]


class GraphState(TypedDict):
    leads_ids: List[str]
    leads_data: List[dict]
    current_lead: LeadData
    lead_score: str = ""
    company_data: CompanyData
    reports: Annotated[list[Report], add]
    reports_folder_link: str
    custom_outreach_report_link: str
    personalized_email: str
    interview_script: str
    number_leads: int
    # Guard to avoid saving the same reports multiple times in a single run
    reports_saved_to_google_docs: bool
    # Per-lead guard: folders already saved to Drive in this run
    saved_drive_folders: List[str]
