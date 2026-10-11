import os
import json
import asyncio
import time
from datetime import datetime
from typing import List, Callable, Optional
from automation.cover_letter_generator import CoverLetterGenerator
from automation.tracker_manager import ApplicationTracker

class BrowserEngine:
    """
    Asynchronous Playwright Browser Engine for the Job Automation Assistant.
    Provides persistent browser sessions, intelligent form filling,
    and real-time event broadcasting to the web dashboard.
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
            "timestamp": timestamp,
            "message": message,
            "level": level
        }
        if self.log_broadcaster:
            await self.log_broadcaster(log_payload)
        else:
            print(f"[{timestamp}] [{level.upper()}] {message}")

    async def launch_browser(self, target_url: str = "https://www.linkedin.com/jobs/"):
        """Launches persistent Chromium/Edge browser context."""
        from playwright.async_api import async_playwright
        
        user_data_dir = os.path.abspath("browser_session_data")
        os.makedirs(user_data_dir, exist_ok=True)

        await self.log(f"Launching persistent browser session...", "action")
        await self.log(f"Session directory: {user_data_dir}", "info")
        await self.log("Saved logins (LinkedIn, Wellfound, Indeed) will be restored automatically.", "info")

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
            except Exception as e:
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

        await self.log(f"Navigating to target portal: {target_url}", "info")
        try:
            await self.page.goto(target_url, wait_until="domcontentloaded", timeout=40000)
            self.current_url = self.page.url
            await self.log(f"Portal loaded successfully: {self.page.url}", "success")
        except Exception as e:
            await self.log(f"Initial navigation notice: {e}", "warning")

        # Listen for page close
        self.page.on("close", lambda p: self._handle_page_close())

    def _handle_page_close(self):
        self.is_running = False

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
            "page_title": title
        }

    async def autofill_current_page(self):
        """Scans the active browser page/modal and autofills questions & inputs."""
        if not self.page or self.page.is_closed():
            await self.log("Browser is not open. Launch browser first!", "error")
            return {"success": False, "message": "Browser is not open."}

        self.profile = self.load_profile()
        personal = self.profile.get("personal", {})
        work_auth = self.profile.get("work_authorization", {})
        availability = self.profile.get("availability", {})
        comp = self.profile.get("compensation", {})
        skills = self.profile.get("skill_experience_years", {})
        screening = self.profile.get("screening_answers", {})
        form_defs = self.profile.get("form_defaults", {})

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
            # Legally authorized to work -> YES
            (["authorized", "legally", "work authorization", "eligible to work"], "yes"),
            # Require sponsorship -> NO
            (["sponsorship", "visa", "require visa", "require sponsorship"], "no"),
            # Willing to relocate -> YES
            (["relocate", "relocation"], "yes"),
            # Background check -> YES
            (["background", "screening"], "yes"),
            # Drug test -> YES
            (["drug"], "yes")
        ]

        for keywords, target_choice in radio_rules:
            for kw in keywords:
                try:
                    # Look for fieldsets, labels or parent containers
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

        await self.log(f"Auto-fill finished! Completed {filled_count} field(s). Review and click Next/Submit.", "action")
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
            # Try filling focused element or first visible textarea
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

    async def safe_batch_apply_step(self):
        """Finds and applies to the next available job card with human-paced safety delays."""
        if not self.page or self.page.is_closed():
            await self.log("Browser is not open.", "error")
            return {"success": False, "message": "Browser is not open."}

        await self.log("🔍 Scanning current listings for available Easy Apply buttons...", "action")
        
        selectors = [
            "button:has-text('Easy Apply')",
            "button:has-text('Apply')",
            "[data-test*='Apply']"
        ]

        found_btn = None
        for sel in selectors:
            try:
                btns = await self.page.query_selector_all(sel)
                for b in btns:
                    if await b.is_visible():
                        txt = (await b.text_content()).strip().lower()
                        if "applied" not in txt and "save" not in txt:
                            found_btn = b
                            break
                if found_btn:
                    break
            except Exception:
                pass

        if not found_btn:
            await self.log("No direct Easy Apply button visible on active list. Try clicking a job card first.", "warning")
            return {"success": False, "message": "No apply button found."}

        btn_text = (await found_btn.text_content()).strip()
        await self.log(f"Clicking application button: '{btn_text}'", "action")
        await found_btn.click()

        # Human safety delay
        await asyncio.sleep(2)
        await self.autofill_current_page()
        await self.log("Waiting for user review before final submit (safety protection against bot-detection).", "info")
        return {"success": True}

    async def close_browser(self):
        if self.context:
            await self.context.close()
            self.context = None
            self.page = None
            self.is_running = False
            await self.log("Browser session closed.", "info")
