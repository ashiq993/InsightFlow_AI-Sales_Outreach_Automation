import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from .tools.base.markdown_scraper_tool import scrape_website_to_markdown
from .tools.base.search_tools import get_recent_news
from .tools.base.gmail_tools import GmailTools
from .tools.google_docs_tools import GoogleDocsManager
from .tools.lead_research import research_lead_on_linkedin
from .tools.company_research import research_lead_company, generate_company_profile
from .tools.youtube_tools import get_youtube_stats
from .tools.rag_tool import fetch_similar_case_study
from .prompts import *
from .state import LeadData, CompanyData, Report, GraphInputState, GraphState
from .structured_outputs import WebsiteData, EmailResponse
from .utils import invoke_llm, get_report, get_current_date, save_reports_locally

# Enable or disable sending emails directly using GMAIL
# Should be confident about the quality of the email
SEND_EMAIL_DIRECTLY = False
# Enable or disable saving emails to Google Docs
# By defauly all reports are save locally in `reports` folder
SAVE_TO_GOOGLE_DOCS = True


class OutReachAutomationNodes:
    def __init__(self, loader, docs_manager=None):
        self.lead_loader = loader
        self.docs_manager = docs_manager if docs_manager else GoogleDocsManager()
        self.drive_folder_name = ""

    def get_new_leads(self, state: GraphInputState):
        logger.info("----- Fetching new leads -----")

        # Fetch new leads using the provided loader
        raw_leads = self.lead_loader.fetch_records()

        leads = []
        for lead in raw_leads:
            # Normalize keys to handle different input formats (CSV/Excel)
            # We look for standard keys or variations
            
            # Helper to find key case-insensitively
            def get_val(d, key_list):
                for k in d.keys():
                    if k.upper() in key_list:
                        return d[k]
                return ""

            full_name = get_val(lead, ["NAME", "FULL NAME", "FULL_NAME", "FIRST NAME", "FIRST_NAME"])
            # If name is split, try to combine
            if not full_name:
                first = get_val(lead, ["FIRST NAME", "FIRST_NAME"])
                last = get_val(lead, ["LAST NAME", "LAST_NAME"])
                if first or last:
                    full_name = f"{first} {last}".strip()
            
            email = get_val(lead, ["MAIL ID", "EMAIL", "EMAIL ADDRESS", "EMAIL_ADDRESS"])
            location = get_val(lead, ["LOCATION", "ADDRESS", "CITY", "COUNTRY"])
            role = get_val(lead, ["ROLE", "JOB TITLE", "TITLE", "POSITION"])
            linkedin = get_val(lead, ["LINKEDIN", "LINKEDIN URL", "LINKEDIN_URL"])
            company = get_val(lead, ["COMPANY", "COMPANY NAME", "COMPANY_NAME"])
            phone = get_val(lead, ["PHONE", "PHONE NUMBER", "MOBILE"])

            # Infer website from email domain when possible
            website = ""
            if email and "@" in email:
                domain = email.split("@")[-1]
                if "." in domain:
                    website = domain

            # Use 'id' if present, otherwise use index logic from loader
            lead_id = str(lead.get("id", ""))

            leads.append(
                LeadData(
                    id=lead_id,
                    name=full_name,
                    email=email,
                    phone=phone,
                    address=location,
                    profile="",  # will be constructed from LinkedIn + research nodes
                    role=role,
                    linkedin=linkedin,
                    location=location,
                    company=company,
                    website=website,
                )
            )

        logger.info(f"----- Fetched {len(leads)} leads -----")
        return {"leads_data": leads, "number_leads": len(leads)}

    @staticmethod
    def check_for_remaining_leads(state: GraphState):
        """Checks for remaining leads and updates lead_data in the state."""
        logger.info("----- Checking for remaining leads -----")

        current_lead = None
        if state["leads_data"]:
            current_lead = state["leads_data"].pop()
        return {"current_lead": current_lead}

    @staticmethod
    def check_if_there_more_leads(state: GraphState):
        # Number of leads remaining
        num_leads = state["number_leads"]
        if num_leads > 0:
            logger.info(f"----- Found {num_leads} more leads -----")
            return "Found leads"
        else:
            logger.info("----- Finished, No more leads -----")
            return "No more leads"

    def fetch_linkedin_profile_data(self, state: GraphState):
        logger.info("----- Searching Lead data on LinkedIn -----")
        lead_data = state["current_lead"]
        company_data = state.get("company_data", CompanyData())

        # Scrape lead linkedin profile
        (lead_profile, company_name, company_website, company_linkedin_url) = (
            research_lead_on_linkedin(lead_data.name, lead_data.email)
        )
        lead_data.profile = lead_profile

        # Research company on linkedin
        company_profile = research_lead_company(company_linkedin_url)

        # Update company name from LinkedIn data
        company_data.name = company_name
        company_data.website = company_website
        company_data.profile = str(company_profile)

        # Use a stable per-lead folder: Lead_Reports/{lead_name}_{company_name}
        lead_folder = f"{lead_data.name}_{company_data.name}".strip().replace("/", "_")
        self.drive_folder_name = f"Lead_Reports/{lead_folder}"
        # Ensure the folder exists in Drive; if already exists, leave it
        try:
            self.docs_manager.ensure_folder_path(
                self.drive_folder_name, make_shareable=True
            )
        except Exception as e:
            logger.error(f"Could not create or access Drive folder '{self.drive_folder_name}': {e}")

        return {"current_lead": lead_data, "company_data": company_data, "reports": []}

    def review_company_website(self, state: GraphState):
        logger.info("----- Scraping company website -----")
        lead_data = state.get("current_lead")
        company_data = state.get("company_data")
        company_website = company_data.website
        # print(f"Company Website: {company_website}")
        if company_website:
            # Scrape company website
            try:
                content = scrape_website_to_markdown(company_website)
            except Exception:
                content = ""

            if not content or not content.strip():
                # Avoid calling LLM when nothing to analyze
                website_info = WebsiteData(
                    summary="",
                    blog_url="",
                    youtube="",
                    twitter="",
                    facebook="",
                )
            else:
                # Call LLM to analyze website
                website_info = invoke_llm(
                    system_prompt=WEBSITE_ANALYSIS_PROMPT.format(
                        main_url=company_website
                    ),
                    user_message=content,
                    model="gemini-2.5-pro",
                    response_format=WebsiteData,
                )

            # Extract all relevant links
            company_data.social_media_links.blog = website_info.blog_url
            company_data.social_media_links.facebook = website_info.facebook
            company_data.social_media_links.twitter = website_info.twitter
            company_data.social_media_links.youtube = website_info.youtube

            # Update company profile with website summary
            company_data.profile = generate_company_profile(
                company_data.profile, website_info.summary
            )

        inputs = f"""
        # **Lead Profile:**

        {lead_data.profile}


        # **Company Information:**

        {company_data.profile}
        """

        # Generate general lead search report
        general_lead_search_report = invoke_llm(
            system_prompt=LEAD_SEARCH_REPORT_PROMPT,
            user_message=inputs,
            model="gemini-2.5-pro",
        )

        lead_search_report = Report(
            title="General Lead Research Report",
            content=general_lead_search_report,
            is_markdown=True,
        )

        return {"company_data": company_data, "reports": [lead_search_report]}

    @staticmethod
    def collect_company_information(state: GraphState):
        return {"reports": []}

    def analyze_blog_content(self, state: GraphState):
        logger.info("----- Analyzing company main blog -----")
        reports_out = []

        # Check if company has a blog
        company_data = state["company_data"]
        blog_url = company_data.social_media_links.blog
        if blog_url:
            blog_content = scrape_website_to_markdown(blog_url)
            prompt = BLOG_ANALYSIS_PROMPT.format(company_name=company_data.name)
            blog_analysis_report = invoke_llm(
                system_prompt=prompt,
                user_message=blog_content,
                model="gemini-2.5-pro",
            )
            blog_analysis_report = Report(
                title="Blog Analysis Report",
                content=blog_analysis_report,
                is_markdown=True,
            )
            reports_out.append(blog_analysis_report)
        return {"reports": reports_out}

    def analyze_social_media_content(self, state: GraphState):
        logger.info("----- Analyzing company social media accounts -----")

        # Load states
        company_data = state["company_data"]

        # Get social media urls
        facebook_url = company_data.social_media_links.facebook
        twitter_url = company_data.social_media_links.twitter
        youtube_url = company_data.social_media_links.youtube

        # Check If company has Youtube channel
        reports_out = []
        if youtube_url:
            # Safely attempt to fetch YouTube stats; fall back to error text for LLM
            try:
                youtube_data = get_youtube_stats(youtube_url)
                if youtube_data is None:
                    # Avoid passing None to LLM; provide clear context text instead
                    youtube_data = "Skipping YouTube analysis: No data returned."
                    logger.warning("Skipping YouTube analysis: No data returned.")
            except Exception as e:
                # If API key is missing or any other error occurs, skip the step but
                # pass a textual error message to the LLM instead of None
                youtube_data = f"Skipping YouTube analysis due to error: {str(e)}"
                logger.warning(f"Skipping YouTube analysis due to error: {str(e)}")
            prompt = YOUTUBE_ANALYSIS_PROMPT.format(company_name=company_data.name)
            youtube_insight = invoke_llm(
                system_prompt=prompt,
                user_message=youtube_data,
                model="gemini-2.5-pro",
            )
            youtube_analysis_report = Report(
                title="Youtube Analysis Report",
                content=youtube_insight,
                is_markdown=True,
            )
            reports_out.append(youtube_analysis_report)

        # Check If company has Facebook account
        if facebook_url:
            # TODO Add Facebook analysis part
            pass

        # Check If company has Twitter account
        if twitter_url:
            # TODO Add Twitter analysis part
            pass

        return {"company_data": company_data, "reports": reports_out}

    def analyze_recent_news(self, state: GraphState):
        logger.info("----- Analyzing recent news about company -----")

        # Load states
        company_data = state["company_data"]

        # Fetch recent news using serper API
        recent_news = get_recent_news(company=company_data.name)
        number_months = 6
        current_date = get_current_date()
        news_analysis_prompt = NEWS_ANALYSIS_PROMPT.format(
            company_name=company_data.name,
            number_months=number_months,
            date=current_date,
        )

        # Craft news analysis prompt
        news_insight = invoke_llm(
            system_prompt=news_analysis_prompt,
            user_message=recent_news,
            model="gemini-2.5-pro",
        )

        news_analysis_report = Report(
            title="News Analysis Report", content=news_insight, is_markdown=True
        )
        return {"reports": [news_analysis_report]}

    def generate_digital_presence_report(self, state: GraphState):
        logger.info("----- Generate Digital presence analysis report -----")

        # Load reports
        reports = state["reports"]
        blog_analysis_report = get_report(reports, "Blog Analysis Report")
        facebook_analysis_report = get_report(reports, "Facebook Analysis Report")
        twitter_analysis_report = get_report(reports, "Twitter Analysis Report")
        youtube_analysis_report = get_report(reports, "Youtube Analysis Report")
        news_analysis_report = get_report(reports, "News Analysis Report")

        inputs = f"""
        # **Digital Presence Data:**
        ## **Blog Information:**

        {blog_analysis_report}
        
        ## **Facebook Information:**

        {facebook_analysis_report}
        
        ## **Twitter Information:**

        {twitter_analysis_report}

        ## **Youtube Information:**

        {youtube_analysis_report}

        # **Recent News:**

        {news_analysis_report}
        """

        prompt = DIGITAL_PRESENCE_REPORT_PROMPT.format(
            company_name=state["company_data"].name, date=get_current_date()
        )
        digital_presence_report = invoke_llm(
            system_prompt=prompt, user_message=inputs, model="gemini-2.5-pro"
        )

        digital_presence_report = Report(
            title="Digital Presence Report",
            content=digital_presence_report,
            is_markdown=True,
        )
        return {"reports": [digital_presence_report]}

    def generate_full_lead_research_report(self, state: GraphState):
        logger.info("----- Generate global lead analysis report -----")

        # Load reports
        reports = state["reports"]
        general_lead_search_report = get_report(reports, "General Lead Research Report")
        digital_presence_report = get_report(reports, "Digital Presence Report")

        inputs = f"""
        # **Lead & company Information:**

        {general_lead_search_report}
        
        ---

        # **Digital Presence Information:**

        {digital_presence_report}
        """

        prompt = GLOBAL_LEAD_RESEARCH_REPORT_PROMPT.format(
            company_name=state["company_data"].name, date=get_current_date()
        )
        full_report = invoke_llm(
            system_prompt=prompt, user_message=inputs, model="gemini-2.5-pro"
        )

        global_research_report = Report(
            title="Global Lead Analysis Report", content=full_report, is_markdown=True
        )
        return {"reports": [global_research_report]}

    @staticmethod
    def score_lead(state: GraphState):
        """
        Score the lead based on the company profile and open positions.

        @param state: The current state of the application.
        @return: Updated state with the lead score.
        """
        logger.info("----- Scoring lead -----")

        # Load reports
        reports = state["reports"]
        global_research_report = get_report(reports, "Global Lead Analysis Report")

        # Scoring lead
        lead_score = invoke_llm(
            system_prompt=SCORE_LEAD_PROMPT,
            user_message=global_research_report,
            model="gemini-2.5-pro",
        )
        return {"lead_score": lead_score.strip()}

    @staticmethod
    def is_lead_qualified(state: GraphState):
        """
        Check if the lead is qualified based on the lead score.

        @param state: The current state of the application.
        @return: Updated state with the qualification status.
        """
        logger.info("----- Checking if lead is qualified -----")
        return {"reports": []}

    @staticmethod
    def check_if_qualified(state: GraphState):
        """
        Check if the lead is qualified based on the lead score.

        @param state: The current state of the application.
        @return: Updated state with the qualification status.
        """
        # Checking if the lead score is 7 or higher
        logger.info(f"Score: {state['lead_score']}")
        is_qualified = float(state["lead_score"]) >= 3
        if is_qualified:
            logger.info("Lead is qualified")
            return "qualified"
        else:
            logger.info("Lead is not qualified")
            return "not qualified"

    @staticmethod
    def create_outreach_materials(state: GraphState):
        return {"reports": []}

    def generate_custom_outreach_report(self, state: GraphState):
        logger.info("----- Crafting Custom outreach report based on gathered information -----")

        # Load reports
        reports = state["reports"]
        general_lead_search_report = get_report(reports, "General Lead Research Report")
        global_research_report = get_report(reports, "Global Lead Analysis Report")

        # TODO Create better description to fetch accurate similar case study using RAG
        # get relevant case study
        case_study_report = fetch_similar_case_study(general_lead_search_report)

        inputs = f"""
        **Research Report:**

        {global_research_report}

        ---

        **Case Study:**

        {case_study_report}
        """

        # Generate report
        custom_outreach_report = invoke_llm(
            system_prompt=GENERATE_OUTREACH_REPORT_PROMPT,
            user_message=inputs,
            model="gemini-2.5-pro",
        )

        # TODO Find better way to include correct links into the final report
        # Proof read generated report
        inputs = f"""
        {custom_outreach_report}

        ---

        **Correct Links:**

        ** Our website link**: https://www.adople.com
        ** Case study link**: https://www.adople.com/project.html/
        """

        # Call our editor/proof-reader agent
        revised_outreach_report = invoke_llm(
            system_prompt=PROOF_READER_PROMPT,
            user_message=inputs,
            model="gemini-2.5-pro",
        )

        # Store report into google docs and get shareable link
        new_doc = self.docs_manager.add_document(
            content=revised_outreach_report,
            doc_title="Outreach Report",
            folder_name=self.drive_folder_name,
            make_shareable=True,
            folder_shareable=True,  # Set to false if only personal or true if with a team
            markdown=True,
        )
        if not new_doc:
            return {
                "custom_outreach_report_link": None,
                "reports_folder_link": None,
            }
        return {
            "custom_outreach_report_link": new_doc["shareable_url"],
            "reports_folder_link": new_doc["folder_url"],
        }

    def generate_personalized_email(self, state: GraphState):
        """
        Generate a personalized email for the lead.

        @param state: The current state of the application.
        @return: Updated state with the generated email.
        """
        logger.info("----- Generating personalized email -----")

        # Load reports
        reports = state["reports"]
        general_lead_search_report = get_report(reports, "General Lead Research Report")

        lead_data = f"""
        # **Lead & company Information:**

        {general_lead_search_report}

        # Outreach report Link:

        {state["custom_outreach_report_link"]}
        """
        output = invoke_llm(
            system_prompt=PERSONALIZE_EMAIL_PROMPT,
            user_message=lead_data,
            model="gemini-2.5-pro",
            response_format=EmailResponse,
        )

        # Get relevant fields
        subject = output.subject
        personalized_email = output.email

        # Get lead email
        email = state["current_lead"].email

        # Create draft email
        gmail = GmailTools()
        gmail.create_draft_email(
            recipient=email, subject=subject, email_content=personalized_email
        )

        # Send email directly
        if SEND_EMAIL_DIRECTLY:
            gmail.send_email(
                recipient=email, subject=subject, email_content=personalized_email
            )

        # Save email with reports for reference
        personalized_email_doc = Report(
            title="Personalized Email", content=personalized_email, is_markdown=False
        )
        return {"reports": [personalized_email_doc]}

    def generate_interview_script(self, state: GraphState):
        logger.info("----- Generating interview script -----")

        # Load reports
        reports = state["reports"]
        global_research_report = get_report(reports, "Global Lead Analysis Report")

        # Generating SPIN questions
        spin_questions = invoke_llm(
            system_prompt=GENERATE_SPIN_QUESTIONS_PROMPT,
            user_message=global_research_report,
            model="gemini-2.5-pro",
        )

        inputs = f"""
        # **Lead & company Information:**

        {global_research_report}

        # **SPIN questions:**

        {spin_questions}
        """

        # Generating interview script
        interview_script = invoke_llm(
            system_prompt=WRITE_INTERVIEW_SCRIPT_PROMPT,
            user_message=inputs,
            model="gemini-2.5-pro",
        )

        interview_script_doc = Report(
            title="Interview Script", content=interview_script, is_markdown=True
        )

        return {"reports": [interview_script_doc]}

    @staticmethod
    def await_reports_creation(state: GraphState):
        return {"reports": []}

    def save_reports_to_google_docs(self, state: GraphState):
        logger.info("----- Save Reports to Google Docs -----")

        current_folder = self.drive_folder_name
        if not current_folder:
            return state

        # Load all reports
        reports = state["reports"]

        # Deduplicate reports by title so we don't keep trying to save / check
        # the same logical document many times in a single run.
        # This also avoids printing a long list of identical
        # "Document 'X' already exists in folder 'Y', skipping." messages.
        unique_reports_by_title = {}
        for report in reports:
            title = getattr(report, "title", None)
            if not title:
                continue
            if title not in unique_reports_by_title:
                unique_reports_by_title[title] = report

        reports = list(unique_reports_by_title.values())

        # Ensure reports are saved locally
        save_reports_locally(reports)

        # Save all reports to Google docs in the same per-lead folder
        if SAVE_TO_GOOGLE_DOCS:
            for report in reports:
                # Skip creating a doc if one with the same title already exists
                if self.docs_manager.document_exists_in_folder(
                    current_folder, report.title
                ):
                    logger.info(
                        f"Document '{report.title}' already exists in "
                        f"folder '{current_folder}', skipping."
                    )
                    continue
                self.docs_manager.add_document(
                    content=report.content,
                    doc_title=report.title,
                    folder_name=self.drive_folder_name,
                    markdown=report.is_markdown,
                    make_shareable=False,
                    folder_shareable=True,
                )

        return state

    def update_CRM(self, state: GraphState):
        logger.info("----- Updating CRM records -----")

        # Save new record data back to the CRM / Google Sheet.
        # For your Apollo-style Google Sheet we only update a STATUS column.
        # Make sure your sheet has headers; missing ones will be added automatically for Google Sheets.
        lead_score = state.get("lead_score")
        qualified = None
        try:
            if lead_score is not None:
                qualified = "YES" if float(lead_score) >= 6 else "NO"
        except Exception:
            # If lead_score isn't a number, leave qualified unset
            pass

        new_data = {"STATUS": "CONTACTED"}
        if lead_score is not None:
            new_data["LEAD_SCORE"] = str(lead_score)
        if qualified is not None:
            new_data["QUALIFIED"] = qualified

        self.lead_loader.update_record(state["current_lead"].id, new_data)

        # reset reports list
        state["reports"] = []

        return {"number_leads": state["number_leads"] - 1}
