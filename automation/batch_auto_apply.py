import os
import json
import time
from automation.tracker_manager import ApplicationTracker

class BatchAutoApply:
    """Automated crawler that iterates over job listings on Wellfound, LinkedIn, and Indeed."""
    def __init__(self, config_path="config/profile.json"):
        self.config_path = config_path
        self.profile = self._load_profile()
        self.tracker = ApplicationTracker()

    def _load_profile(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def auto_apply(self, page):
        """Scans current page for Apply / Easy Apply elements and processes them."""
        print("\n🔍 Scanning page for job listings and Apply buttons...")
        
        personal = self.profile.get("personal", {})
        tech_prof = self.profile.get("tech_profile", {})

        # Step 1: Scroll page to trigger dynamic element rendering
        try:
            page.evaluate("window.scrollBy(0, 400);")
            time.sleep(1)
            page.evaluate("window.scrollBy(0, -200);")
            time.sleep(1)
        except Exception:
            pass

        # Step 2: Broad search for any button or clickable element with Apply text
        selectors = [
            "button:has-text('Easy Apply')",
            "button:has-text('Apply')",
            "a:has-text('Easy Apply')",
            "a:has-text('Apply')",
            "[data-test*='Apply']",
            "button[class*='apply']",
            "span:has-text('Easy Apply')",
            "span:has-text('Apply Now')"
        ]

        found_elements = []
        for sel in selectors:
            try:
                elems = page.query_selector_all(sel)
                for el in elems:
                    if el.is_visible():
                        txt = el.text_content().strip()
                        if "applied" not in txt.lower() and "save" not in txt.lower():
                            found_elements.append((el, txt))
            except Exception:
                pass

        # If direct apply buttons weren't found on job list, try clicking job cards to open detail drawer
        if not found_elements:
            print("  ℹ️ No direct apply buttons visible on list. Attempting to select job cards...")
            card_selectors = [
                "div[class*='jobCard']",
                "div[class*='styles_component']",
                "a[class*='job-title']",
                "li.jobs-search-results__list-item",
                "div.job-card-container"
            ]
            for c_sel in card_selectors:
                try:
                    cards = page.query_selector_all(c_sel)
                    if cards:
                        print(f"  Found {len(cards)} job card(s). Selecting first card...")
                        cards[0].click()
                        time.sleep(2)
                        # Re-scan after selecting card
                        for sel in selectors:
                            elems = page.query_selector_all(sel)
                            for el in elems:
                                if el.is_visible():
                                    txt = el.text_content().strip()
                                    if "applied" not in txt.lower():
                                        found_elements.append((el, txt))
                        break
                except Exception:
                    pass

        print(f"  Found {len(found_elements)} clickable Apply element(s).")

        applied_count = 0
        for el, text in found_elements[:5]:  # Process up to 5 jobs per batch run safely
            try:
                print(f"\n👉 Processing element: '{text}'...")
                el.click()
                time.sleep(2)

                # Step 3: Handle Application Form / Modal
                # Fill any visible textareas (Cover Letter / Note to recruiter)
                textareas = page.query_selector_all("textarea")
                for ta in textareas:
                    if ta.is_visible():
                        note = (
                            f"Hi! I am {personal.get('full_name', 'Nachiket Rana')}, a {tech_prof.get('title', 'Full-Stack Developer')} "
                            f"with experience in React, Node.js, and PostgreSQL. I improved backend API throughput by 30% and built real-time financial dashboards. "
                            f"Portfolio: {personal.get('portfolio', '')} | GitHub: {personal.get('github', '')}"
                        )
                        ta.fill(note)
                        print("  ✅ Auto-filled cover letter / recruiter note.")

                # Fill any visible text inputs (Name, Email, Phone, Portfolio)
                inputs = page.query_selector_all("input[type='text'], input[type='email'], input[type='tel']")
                for inp in inputs:
                    try:
                        if inp.is_visible() and not inp.input_value().strip():
                            placeholder = (inp.get_attribute("placeholder") or "").lower()
                            name_attr = (inp.get_attribute("name") or "").lower()
                            
                            if "email" in placeholder or "email" in name_attr:
                                inp.fill(personal.get("email", ""))
                            elif "phone" in placeholder or "phone" in name_attr or "mobile" in placeholder:
                                inp.fill(personal.get("phone", ""))
                            elif "name" in placeholder or "name" in name_attr:
                                inp.fill(personal.get("full_name", ""))
                            elif "github" in placeholder or "github" in name_attr:
                                inp.fill(personal.get("github", ""))
                            elif "linkedin" in placeholder or "linkedin" in name_attr:
                                inp.fill(personal.get("linkedin", ""))
                            elif "website" in placeholder or "portfolio" in placeholder:
                                inp.fill(personal.get("portfolio", ""))
                    except Exception:
                        pass

                # Step 4: Look for Submit / Send / Next buttons
                submit_selectors = [
                    "button:has-text('Send Application')",
                    "button:has-text('Submit')",
                    "button:has-text('Submit application')",
                    "button:has-text('Next')",
                    "button:has-text('Send')"
                ]

                sub_clicked = False
                for s_sel in submit_selectors:
                    try:
                        s_btn = page.query_selector(s_sel)
                        if s_btn and s_btn.is_visible():
                            s_text = s_btn.text_content().strip()
                            print(f"  🚀 Action: Clicking '{s_text}'...")
                            s_btn.click()
                            sub_clicked = True
                            applied_count += 1
                            time.sleep(2)
                            break
                    except Exception:
                        pass

                if sub_clicked:
                    self.tracker.log_application("Auto-Applied Company", "Developer / Specialist", "Tech", "Auto-Browser", page.url)

            except Exception as err:
                print(f"  ⚠️ Form interaction note: {err}")

        print(f"\n🎉 Batch auto-apply completed! Successfully processed {applied_count} application(s).\n")

    def auto_apply_wellfound(self, page):
        """Wrapper method for auto_apply."""
        self.auto_apply(page)

if __name__ == "__main__":
    print("BatchAutoApply module updated.")
