import os
import json
import asyncio
import time
from datetime import datetime
from typing import List, Callable, Optional, Set
from automation.cover_letter_generator import CoverLetterGenerator
from automation.tracker_manager import ApplicationTracker

class BrowserEngine:
    """
    Asynchronous Playwright Browser Engine for the Job Automation Assistant.
    Provides persistent browser sessions, intelligent form filling,
    guided batch application queues, and real-time event broadcasting to the web dashboard.
    """
    def __init__(self, config_path="config/profile.json", log_broadcaster: Optional[Callable] = None):
        self.config_path = config_path
        self.log_broadcaster = log_broadcaster
        self.profile = self.load_profile()
        self.tracker = ApplicationTracker()
        self.cover_letter_gen = CoverLetterGenerator()
        
        self.playwright = None
        self.context = None
        self.page = None
        self.is_running = False
        self.current_url = ""

        # Wellfound Batch Queue State
        self.queue_active = False
        self.queue_total = 10
        self.queue_current = 0
        self.pending_company = ""
        self.pending_role = ""
        self.pending_note = ""
        self.processed_companies: Set[str] = set()

    def load_profile(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_profile(self, new_profile_data):
        self.profile = new_profile_data
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(new_profile_data, f, indent=2)

    async def log(self, message: str, level: str = "info"):
        """Broadcasts a log message with level (info, success, warning, error, action)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_payload = {
            "type": "log",
            "timestamp": timestamp,
            "message": message,
            "level": level
        }
        if self.log_broadcaster:
            await self.log_broadcaster(log_payload)
        else:
            print(f"[{timestamp}] [{level.upper()}] {message}")

    async def broadcast_event(self, event_data: dict):
        if self.log_broadcaster:
            await self.log_broadcaster(event_data)

    async def launch_browser(self, target_url: str = "https://www.linkedin.com/jobs/"):
        """Launches persistent Chromium/Edge browser context."""
        from playwright.async_api import async_playwright
        
        user_data_dir = os.path.abspath("browser_session_data")
        os.makedirs(user_data_dir, exist_ok=True)

        await self.log("Launching persistent browser session...", "action")
        await self.log(f"Session directory: {user_data_dir}", "info")
        await self.log("Saved logins (Wellfound, LinkedIn, Indeed) will be restored automatically.", "info")

        if not self.playwright:
            self.playwright = await async_playwright().start()

        browser_options = [
            {}, # default playwright chromium
            {"channel": "msedge"},
            {"channel": "chrome"}
        ]

        user_agent_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        browser_args = [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox"
        ]

        for opts in browser_options:
            try:
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False,
                    args=browser_args,
                    user_agent=user_agent_str,
                    viewport=None,
                    **opts
                )
                break
            except Exception:
                continue

        if not self.context:
            await self.log("Chromium binary not found locally, downloading...", "warning")
            os.system("playwright install chromium")
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=browser_args,
                user_agent=user_agent_str,
                viewport=None
            )

        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        self.is_running = True

        await self.log(f"Navigating to: {target_url}", "info")
        try:
            await self.page.goto(target_url, wait_until="domcontentloaded", timeout=40000)
            self.current_url = self.page.url
            await self.log(f"Portal loaded successfully: {self.page.url}", "success")
        except Exception as e:
            await self.log(f"Initial navigation notice: {e}", "warning")

        self.page.on("close", lambda p: self._handle_page_close())

    def _handle_page_close(self):
        self.is_running = False
        self.queue_active = False

    async def get_status(self):
        url = ""
        title = ""
        if self.page and not self.page.is_closed():
            try:
                url = self.page.url
                title = await self.page.title()
            except Exception:
                pass
        return {
            "is_running": self.is_running and self.page is not None and not self.page.is_closed(),
            "current_url": url,
            "page_title": title,
            "queue_active": self.queue_active,
            "queue_current": self.queue_current,
            "queue_total": self.queue_total,
            "pending_company": self.pending_company,
            "pending_role": self.pending_role
        }

    async def autofill_current_page(self):
        """Scans the active browser page/modal and autofills questions & inputs."""
        if not self.page or self.page.is_closed():
            await self.log("Browser is not open. Launch browser first!", "error")
            return {"success": False, "message": "Browser is not open."}

        self.profile = self.load_profile()
        personal = self.profile.get("personal", {})
        availability = self.profile.get("availability", {})
        comp = self.profile.get("compensation", {})
        skills = self.profile.get("skill_experience_years", {})
        screening = self.profile.get("screening_answers", {})

        await self.log("⚡ Initiating Smart Auto-Fill on active window...", "action")
        filled_count = 0

        # 1. Fill Text Inputs
        text_mappings = [
            (["first_name", "firstname", "first-name", "fname"], personal.get("first_name", "")),
            (["last_name", "lastname", "last-name", "lname"], personal.get("last_name", "")),
            (["full_name", "name", "fullname", "full-name"], personal.get("full_name", "")),
            (["email", "e-mail", "user_email"], personal.get("email", "")),
            (["phone", "mobile", "cell", "telephone", "contact_number"], personal.get("phone", "")),
            (["city", "location", "address", "current_city"], personal.get("city", "")),
            (["postal", "zip", "zipcode", "pincode"], personal.get("postal_code", "")),
            (["linkedin", "linkedin_url", "linkedin_profile"], personal.get("linkedin", "")),
            (["github", "github_url", "github_profile"], personal.get("github", "")),
            (["portfolio", "website", "personal_website", "url"], personal.get("portfolio", "")),
            (["salary", "desired_salary", "expected_salary", "ctc"], comp.get("expected_salary_tech_numeric", "800000")),
            (["notice", "notice_period"], availability.get("notice_period", "Immediate")),
            (["experience", "years_experience", "total_experience"], skills.get("total_experience", "2"))
        ]

        for keywords, value in text_mappings:
            if not value:
                continue
            for kw in keywords:
                selectors = [
                    f'input[name*="{kw}" i]',
                    f'input[id*="{kw}" i]',
                    f'input[placeholder*="{kw}" i]',
                    f'input[aria-label*="{kw}" i]'
                ]
                for sel in selectors:
                    try:
                        elems = await self.page.query_selector_all(sel)
                        for el in elems:
                            if await el.is_visible() and await el.is_enabled():
                                curr = await el.input_value()
                                if not curr.strip():
                                    await el.fill(str(value))
                                    filled_count += 1
                                    await self.log(f"Filled input '{kw}': {value}", "success")
                    except Exception:
                        pass

        # 2. Fill Radio Buttons & Checkboxes (Work Auth & Sponsorship)
        radio_rules = [
            (["authorized", "legally", "work authorization", "eligible to work"], "yes"),
            (["sponsorship", "visa", "require visa", "require sponsorship"], "no"),
            (["relocate", "relocation"], "yes"),
            (["background", "screening"], "yes"),
            (["drug"], "yes")
        ]

        for keywords, target_choice in radio_rules:
            for kw in keywords:
                try:
                    containers = await self.page.query_selector_all(f"fieldset:has-text('{kw}'), div:has-text('{kw}')")
                    for cont in containers[:3]:
                        if await cont.is_visible():
                            target_radio = await cont.query_selector(f"input[type='radio'][value*='{target_choice}' i], label:has-text('{target_choice.capitalize()}')")
                            if target_radio and await target_radio.is_visible():
                                await target_radio.click()
                                filled_count += 1
                                await self.log(f"Selected radio answer '{target_choice.upper()}' for '{kw}'", "success")
                                break
                except Exception:
                    pass

        # 3. Fill Screening Textareas (Elevator Pitch / Recruiter Notes)
        try:
            textareas = await self.page.query_selector_all("textarea")
            for ta in textareas:
                if await ta.is_visible() and await ta.is_enabled():
                    curr_txt = await ta.input_value()
                    if not curr_txt.strip():
                        pitch = screening.get("elevator_pitch", "")
                        if pitch:
                            await ta.fill(pitch)
                            filled_count += 1
                            await self.log("Auto-filled pitch into application textarea.", "success")
        except Exception:
            pass

        await self.log(f"Auto-fill complete! Filled {filled_count} field(s). Review and click Submit.", "action")
        return {"success": True, "filled_count": filled_count}

    async def inject_cover_letter(self, company: str = "", role: str = "", category: str = "Tech"):
        """Generates tailored cover letter and injects it into active textarea."""
        if not self.page or self.page.is_closed():
            await self.log("Browser is not open.", "error")
            return {"success": False, "message": "Browser is not open."}

        await self.log(f"Generating tailored cover letter for {company or 'Company'} ({role or 'Role'})...", "action")
        result = self.cover_letter_gen.generate(company, role, category=category)
        body_text = result.get("body", "")

        try:
            injected = await self.page.evaluate("""(text) => {
                const active = document.activeElement;
                if (active && (active.tagName === 'TEXTAREA' || active.isContentEditable || active.tagName === 'INPUT')) {
                    active.value = text;
                    active.dispatchEvent(new Event('input', { bubbles: true }));
                    active.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                const textareas = Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent !== null);
                if (textareas.length > 0) {
                    textareas[0].value = text;
                    textareas[0].dispatchEvent(new Event('input', { bubbles: true }));
                    textareas[0].dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            }""", body_text)

            if injected:
                await self.log(f"Successfully injected cover letter ({category}) into active form!", "success")
                return {"success": True, "cover_letter": result}
            else:
                await self.log("No active textarea found on page. Generated letter copied to response.", "warning")
                return {"success": False, "message": "No textarea found", "cover_letter": result}
        except Exception as e:
            await self.log(f"Error injecting cover letter: {e}", "error")
            return {"success": False, "error": str(e), "cover_letter": result}

    # =========================================================================
    # WELLFOUND CONTINUOUS GUIDED AUTO-APPLY PIPELINE (WITH USER REVIEW)
    # =========================================================================

    async def _close_any_active_modal(self):
        """Ensures any application modal, drawer, or success popup is dismissed so subsequent jobs can be clicked."""
        if not self.page or self.page.is_closed():
            return

        close_selectors = [
            "button:has-text('Done')",
            "button:has-text('Back to jobs')",
            "button:has-text('Close')",
            "button[aria-label*='Close' i]",
            "button[aria-label*='Dismiss' i]",
            "div[role='dialog'] button:has-text('Cancel')",
            "button:has-text('Cancel')",
            "svg[data-icon='xmark']"
        ]
        for sel in close_selectors:
            try:
                btns = await self.page.query_selector_all(sel)
                for b in btns:
                    if await b.is_visible():
                        await b.click()
                        await asyncio.sleep(0.8)
                        break
            except Exception:
                pass

        try:
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
        except Exception:
            pass

    async def start_wellfound_batch_queue(self, max_companies: int = 10):
        """
        Starts the Guided Queue on Wellfound.
        Opens each job card, generates customized pitch note, fills screening fields,
        and pauses for the user to review and click 'Yes, Submit'.
        """
        if not self.page or self.page.is_closed():
            await self.launch_browser("https://wellfound.com/jobs")
        elif "wellfound.com" not in self.page.url:
            await self.page.goto("https://wellfound.com/jobs", wait_until="domcontentloaded")

        self.queue_active = True
        self.queue_total = max_companies
        self.queue_current = 0
        self.processed_companies.clear()

        limit_label = f"{max_companies} companies" if max_companies < 900 else "Continuous Mode"
        await self.log(f"🚀 Initializing Wellfound Guided Queue ({limit_label})...", "action")
        await self.log("The assistant will prepare each application with a tailored pitch, then pause for your approval.", "info")

        return await self._prepare_next_wellfound_job()

    async def _prepare_next_wellfound_job(self):
        """Finds the next unapplied job listing, opens modal, injects pitch, and awaits user review."""
        if not self.queue_active or not self.page or self.page.is_closed():
            return {"success": False, "message": "Queue not active or browser closed."}

        if self.queue_current >= self.queue_total:
            self.queue_active = False
            await self.log(f"🎉 Wellfound Campaign Milestone Reached! Completed all {self.queue_total} applications.", "success")
            await self.broadcast_event({"type": "wellfound_finished", "total_applied": self.queue_total})
            return {"success": True, "finished": True}

        queue_label = f"{self.queue_current + 1}/{self.queue_total}" if self.queue_total < 900 else f"#{self.queue_current + 1}"
        await self.log(f"🔍 [Queue {queue_label}] Scanning Wellfound for next available job...", "action")

        # Make sure any lingering dialog from previous action is dismissed
        await self._close_any_active_modal()

        target_btn = None
        target_card = None
        company_name = "Startup"
        role_title = "Full-Stack Developer"

        # Search with automatic scrolling up to 8 cycles
        for scroll_cycle in range(8):
            # Check for direct Apply buttons
            apply_buttons = await self.page.query_selector_all("button:has-text('Apply'), a:has-text('Apply')")
            for btn in apply_buttons:
                try:
                    if not await btn.is_visible():
                        continue
                    txt = (await btn.text_content()).strip().lower()
                    if "applied" in txt or "save" in txt or "share" in txt or "filter" in txt:
                        continue

                    # Extract card text to identify company
                    parent_text = ""
                    try:
                        parent_text = await btn.evaluate("""el => {
                            const card = el.closest('div[class*="component"], div[class*="jobCard"], div[class*="styles_result"], li') || el.parentElement;
                            return card ? card.innerText : '';
                        }""")
                    except Exception:
                        pass

                    first_lines = [l.strip() for l in parent_text.split('\\n') if l.strip()]
                    detected_company = first_lines[0][:40] if first_lines else ""

                    if detected_company and detected_company in self.processed_companies:
                        continue

                    # Found an unapplied button!
                    target_btn = btn
                    if detected_company:
                        company_name = detected_company
                        if len(first_lines) >= 2:
                            role_title = first_lines[1][:50]
                    break
                except Exception:
                    continue

            if target_btn:
                break

            # If no direct button found, search for job card containers to open detail drawer
            cards = await self.page.query_selector_all("div[class*='jobCard'], div[class*='styles_component'], div[data-test*='StartupResult']")
            for c in cards:
                try:
                    if not await c.is_visible():
                        continue
                    c_text = await c.evaluate("el => el.innerText || ''")
                    c_lines = [l.strip() for l in c_text.split('\\n') if l.strip()]
                    c_name = c_lines[0][:40] if c_lines else ""

                    if c_name and c_name in self.processed_companies:
                        continue
                    if "applied" in c_text.lower():
                        continue

                    target_card = c
                    if c_name:
                        company_name = c_name
                    if len(c_lines) >= 2:
                        role_title = c_lines[1][:50]

                    await c.click()
                    await asyncio.sleep(2)

                    inner_btn = await self.page.query_selector("button:has-text('Apply')")
                    if inner_btn and await inner_btn.is_visible():
                        target_btn = inner_btn
                        break
                except Exception:
                    continue

            if target_btn:
                break

            # Scroll down to load more cards dynamically
            await self.log(f"Auto-scrolling down to load more job listings (attempt {scroll_cycle + 1}/8)...", "info")
            try:
                await self.page.evaluate("window.scrollBy(0, 700);")
                await asyncio.sleep(1.8)
            except Exception:
                pass

        if not target_btn:
            await self.log("No more unapplied job listings visible on page. Please change search filter or adjust location.", "warning")
            await self.broadcast_event({"type": "wellfound_waiting_scroll"})
            return {"success": False, "message": "No unapplied jobs found on current view."}

        btn_txt = (await target_btn.text_content()).strip()
        await self.log(f"👉 Opening application for: {company_name} — '{role_title}' (Button: '{btn_txt}')...", "action")
        await target_btn.click()

        # Wait for application modal to render
        await asyncio.sleep(2.5)

        # Inspect modal for accurate company name
        try:
            modal_heading = await self.page.query_selector("div[role='dialog'] h2, div[role='dialog'] h3, div[class*='modal'] h2")
            if modal_heading and await modal_heading.is_visible():
                heading_txt = (await modal_heading.text_content()).strip()
                if "apply to" in heading_txt.lower():
                    company_name = heading_txt.replace("Apply to", "").strip()
                elif heading_txt:
                    role_title = heading_txt
        except Exception:
            pass

        if company_name:
            self.processed_companies.add(company_name)

        # Prepare Tailored Pitch for Hiring Manager using REAL Profile Details
        self.profile = self.load_profile()
        personal = self.profile.get("personal", {})
        full_name = personal.get("full_name", "Nachiket Rana")
        city = personal.get("city", "Ahmedabad")
        github_url = personal.get("github", "https://github.com/nachiketrana")
        linkedin_url = personal.get("linkedin", "https://www.linkedin.com/in/nachiket-rana-6079662a4/")
        portfolio_url = (personal.get("portfolio") or "").strip()

        links = [f"GitHub: {github_url}", f"LinkedIn: {linkedin_url}"]
        if portfolio_url and "example" not in portfolio_url:
            links.insert(0, f"Portfolio: {portfolio_url}")
        links_str = " | ".join(links)

        tailored_note = (
            f"Hi {company_name} Team,\n\n"
            f"I am writing to express my strong interest in the {role_title} role. With 2+ years of full-stack engineering "
            f"experience in React, Node.js, and PostgreSQL, I previously improved backend API throughput by 30% and built "
            f"high-performance web applications.\n\n"
            f"I take full end-to-end ownership of product features, write clean and scalable code, and thrive in fast-paced startup teams. "
            f"Based in {city}, India, I am available to join immediately.\n\n"
            f"{links_str}\n\n"
            f"I would love the opportunity to contribute to your mission!\n\n"
            f"Best regards,\n{full_name}"
        )

        # Auto-fill the Note textarea in the open modal
        note_filled = False
        try:
            textareas = await self.page.query_selector_all("div[role='dialog'] textarea, div[class*='modal'] textarea, textarea")
            for ta in textareas:
                if await ta.is_visible():
                    await ta.fill(tailored_note)
                    note_filled = True
                    await self.log("✅ Auto-filled tailored note for hiring manager.", "success")
                    break
        except Exception as e:
            await self.log(f"Note filling notice: {e}", "warning")

        # Also auto-fill any other common inputs in the modal (experience, salary, links)
        await self.autofill_current_page()

        # Save pending review details
        self.pending_company = company_name
        self.pending_role = role_title
        self.pending_note = tailored_note

        # Broadcast review prompt to dashboard
        review_data = {
            "type": "wellfound_review",
            "company": company_name,
            "role": role_title,
            "current_index": self.queue_current + 1,
            "total_queue": self.queue_total,
            "note_preview": tailored_note
        }
        await self.broadcast_event(review_data)

        await self.log(f"🔔 [ACTION REQUIRED] Review Application #{queue_label}: {company_name} ({role_title})", "action")
        await self.log("👉 Form & Pitch are prepared. Check browser and click 'Yes, Submit' on dashboard to confirm!", "action")

        return {"success": True, "review_ready": True, "company": company_name, "role": role_title}

    async def confirm_current_submission(self):
        """
        Called when the user clicks 'Yes, Submit' on the dashboard.
        Clicks the submission button, logs to CSV, closes the modal, and advances continuously to the next company.
        """
        if not self.page or self.page.is_closed():
            return {"success": False, "message": "Browser is not open."}

        await self.log(f"🚀 User approved! Submitting application to {self.pending_company}...", "action")

        submit_selectors = [
            "button:has-text('Send application')",
            "button:has-text('Submit application')",
            "button:has-text('Submit')",
            "button:has-text('Send')",
            "button:has-text('Apply')"
        ]

        submitted = False
        for sel in submit_selectors:
            try:
                btns = await self.page.query_selector_all(sel)
                for b in btns:
                    if await b.is_visible():
                        b_text = (await b.text_content()).strip().lower()
                        if "save" not in b_text:
                            await b.click()
                            submitted = True
                            await self.log(f"Clicked submission button: '{b_text.capitalize()}'.", "success")
                            break
                if submitted:
                    break
            except Exception:
                pass

        # Log into Application Tracker
        app_id = self.tracker.log_application(
            company=self.pending_company,
            role=self.pending_role,
            category="Tech",
            platform="Wellfound",
            job_url=self.page.url if self.page else "",
            cover_letter=self.pending_note
        )

        await self.log(f"✅ Application #{app_id} successfully submitted to {self.pending_company}!", "success")
        self.queue_current += 1

        # Broadcast updated stats
        stats = self.tracker.get_stats()
        await self.broadcast_event({"type": "stats", **stats})

        # Wait for submission network request to finalize
        await asyncio.sleep(2)

        # CRITICAL: Close the modal so the screen is completely clear for the next job!
        await self._close_any_active_modal()
        await asyncio.sleep(1)

        # Scroll down slightly so the applied card moves up and the next fresh cards come into view
        try:
            await self.page.evaluate("window.scrollBy(0, 450);")
            await asyncio.sleep(1)
        except Exception:
            pass

        # Pacing delay (natural 2.5 seconds so platform sees human interaction)
        queue_label = f"{self.queue_current}/{self.queue_total}" if self.queue_total < 900 else f"#{self.queue_current}"
        await self.log(f"⏳ Advancing continuously to next company ({queue_label})...", "info")
        await asyncio.sleep(2.5)

        # Proceed continuously to next company in queue
        return await self._prepare_next_wellfound_job()

    async def skip_current_submission(self):
        """Skips the current application, closes modal, and proceeds to next company."""
        await self.log(f"⏭️ Skipping application for {self.pending_company}. Proceeding to next...", "warning")
        if self.pending_company:
            self.processed_companies.add(self.pending_company)

        # Close the open application modal
        await self._close_any_active_modal()
        await asyncio.sleep(1)

        # Scroll down slightly
        try:
            await self.page.evaluate("window.scrollBy(0, 400);")
            await asyncio.sleep(1)
        except Exception:
            pass

        return await self._prepare_next_wellfound_job()

    async def stop_batch_queue(self):
        """Cancels the current batch queue."""
        self.queue_active = False
        await self._close_any_active_modal()
        await self.log("🛑 Wellfound Batch Queue stopped by user.", "info")
        await self.broadcast_event({"type": "wellfound_stopped"})
        return {"success": True}

    async def close_browser(self):
        self.queue_active = False
        if self.context:
            await self.context.close()
            self.context = None
            self.page = None
            self.is_running = False
            await self.log("Browser session closed.", "info")
