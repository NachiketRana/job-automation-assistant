import os
import json
import time

class FormAssistant:
    def __init__(self, config_path="config/profile.json"):
        self.config_path = config_path
        self.profile = self._load_profile()

    def _load_profile(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def launch_browser_session(self, target_url=None):
        """Launches a Playwright browser session configured for job applications."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("\n❌ Playwright module is not installed yet. Run: pip install playwright && playwright install chromium")
            return False

        user_data_dir = os.path.abspath("browser_session_data")
        os.makedirs(user_data_dir, exist_ok=True)

        personal = self.profile.get("personal", {})
        tech_prof = self.profile.get("tech_profile", {})
        work_auth = self.profile.get("work_authorization", {})

        print(f"\n🚀 Launching Application Assistant Browser (User Session: {user_data_dir})...")
        print("💡 Hint: Log into LinkedIn, Wellfound, Instahyre, or Indeed inside this window. Your session will remain logged in!")

        with sync_playwright() as p:
            # Try default Playwright Chromium, fallback to installed Edge or Chrome
            context = None
            browser_options = [
                {}, # Default playwright chromium
                {"channel": "msedge"}, # Installed Microsoft Edge on Windows
                {"channel": "chrome"} # Installed Google Chrome on Windows
            ]

            user_agent_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            browser_args = [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]

            for opts in browser_options:
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=False,
                        args=browser_args,
                        user_agent=user_agent_str,
                        viewport=None,
                        **opts
                    )
                    break
                except Exception as e:
                    if "Executable doesn't exist" in str(e) or "Could not find browser" in str(e):
                        continue
                    else:
                        raise e

            if not context:
                print("\n❌ Could not find Playwright Chromium, Edge, or Chrome.")
                print("Downloading Chromium now... Please wait a moment.")
                os.system("playwright install chromium")
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=False,
                        args=browser_args,
                        user_agent=user_agent_str,
                        viewport=None
                    )
                except Exception as final_err:
                    print(f"❌ Error launching browser: {final_err}")
                    return False
            
            page = context.pages[0] if context.pages else context.new_page()
            
            initial_url = target_url or "https://www.linkedin.com/jobs"
            print(f"🔗 Navigating to: {initial_url}")
            try:
                page.goto(initial_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as nav_err:
                print(f"⚠️ Page load notice: {nav_err}. Proceeding with page content...")

            print("\n-----------------------------------------------------------")
            print("✨ APPLICATION ASSISTANT IS ACTIVE IN THE OPEN BROWSER!")
            print("Commands in terminal:")
            print("  [1] Auto-fill form fields on CURRENT OPEN FORM/MODAL")
            print("  [2] Paste Cover Letter into active text box")
            print("  [3] ⚡ Batch Auto-Apply to all listings on current page")
            print("  [q] Quit browser session")
            print("-----------------------------------------------------------\n")

            while True:
                user_cmd = input("Command (1=Auto-Fill, 2=Paste Cover Letter, 3=Batch Apply, q=Quit): ").strip().lower()
                if user_cmd == "q":
                    print("Closing browser session...")
                    break
                elif user_cmd == "1":
                    self._autofill_page(page, personal, tech_prof, work_auth)
                elif user_cmd == "2":
                    cl_text = input("Paste your cover letter text here (or press Enter to cancel): ").strip()
                    if cl_text:
                        self._fill_focused_textarea(page, cl_text)
                elif user_cmd == "3":
                    from automation.batch_auto_apply import BatchAutoApply
                    batcher = BatchAutoApply(self.config_path)
                    batcher.auto_apply_wellfound(page)

            context.close()
            return True

    def _autofill_page(self, page, personal, tech_prof, work_auth):
        """Attempts to auto-fill common input selectors on job forms."""
        print("⚡ Scanning page for known application fields...")
        
        field_mappings = [
            # First Name
            (["first_name", "firstname", "first-name", "fname"], personal.get("first_name", "")),
            # Last Name
            (["last_name", "lastname", "last-name", "lname"], personal.get("last_name", "")),
            # Full Name
            (["name", "full_name", "fullname", "full-name"], personal.get("full_name", "")),
            # Email
            (["email", "e-mail", "user_email"], personal.get("email", "")),
            # Phone
            (["phone", "mobile", "cell", "telephone", "contact_number"], personal.get("phone", "")),
            # City / Location
            (["city", "location", "address"], personal.get("city", "")),
            # LinkedIn
            (["linkedin", "linkedin_url", "linkedin_profile"], personal.get("linkedin", "")),
            # GitHub
            (["github", "github_url", "github_profile"], personal.get("github", "")),
            # Portfolio / Website
            (["portfolio", "website", "url", "personal_website"], personal.get("portfolio", "")),
            # Experience Years
            (["experience", "years_experience", "total_experience"], tech_prof.get("experience_years", "2")),
            # Salary Expectation
            (["salary", "desired_salary", "expected_salary", "ctc"], tech_prof.get("salary_expectation", ""))
        ]

        filled_count = 0
        for keywords, value in field_mappings:
            if not value:
                continue
            for kw in keywords:
                # Try finding by name, id, placeholder, or aria-label
                selectors = [
                    f'input[name*="{kw}" i]',
                    f'input[id*="{kw}" i]',
                    f'input[placeholder*="{kw}" i]',
                    f'textarea[name*="{kw}" i]',
                    f'textarea[placeholder*="{kw}" i]'
                ]
                for sel in selectors:
                    try:
                        elements = page.query_selector_all(sel)
                        for elem in elements:
                            if elem.is_visible() and elem.is_enabled():
                                current_val = elem.input_value() if elem.tag_name == "INPUT" else elem.text_content()
                                if not current_val.strip():
                                    elem.fill(str(value))
                                    filled_count += 1
                                    print(f"  ✅ Auto-filled '{kw}' with: {value}")
                    except Exception:
                        pass

        print(f"🎉 Auto-fill complete! Filled {filled_count} field(s). Review form and click Next/Submit when ready.\n")

    def _fill_focused_textarea(self, page, text):
        try:
            page.evaluate("""(textToPaste) => {
                const activeEl = document.activeElement;
                if (activeEl && (activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable || activeEl.tagName === 'INPUT')) {
                    activeEl.value = textToPaste;
                    activeEl.dispatchEvent(new Event('input', { bubbles: true }));
                    activeEl.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }""", text)
            print("  ✅ Cover letter pasted into active input field!\n")
        except Exception as e:
            print(f"  ❌ Error pasting: {e}")

if __name__ == "__main__":
    assistant = FormAssistant()
    # assistant.launch_browser_session()
