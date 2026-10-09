import os
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from automation.cover_letter_generator import CoverLetterGenerator
from automation.tracker_manager import ApplicationTracker
from automation.form_assistant import FormAssistant

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 65)
    print("      🎯 150-JOB APPLICATION AUTOMATION ASSISTANT")
    print("             Candidate: Nachiket Rana | Target: 150 Offers")
    print("=" * 65)

def show_dashboard(tracker):
    stats = tracker.get_stats()
    print("\n📊 APPLICATION CAMPAIGN STATUS:")
    print(f"   • Total Applied:  [{stats['total_applied']} / 150] ({stats['progress_percent']}%)")
    print(f"   • Tech Jobs:       [{stats['tech_count']} / 100]")
    print(f"   • Social Media:    [{stats['social_count']} / 50]")
    print("-----------------------------------------------------------")

def option_launch_browser():
    print("\n🌐 BROWSER APPLICATION ASSISTANT - DIRECT APPLY PORTALS")
    print("Choose a pre-configured job search target with Direct 1-Click Apply enabled:")
    print("  [1] 🔹 LinkedIn: Full-Stack Developer Jobs (Easy Apply Filter ON)")
    print("  [2] 🔹 LinkedIn: Social Media Marketing Jobs (Easy Apply Filter ON)")
    print("  [3] ⚡ Instahyre: 1-Click Tech Jobs (India)")
    print("  [4] 🚀 Wellfound: Startup Jobs")
    print("  [5] 📌 Indeed: Easily Apply Jobs")
    print("  [6] 🔗 Enter Custom URL")
    print("-" * 65)

    choice = input("Select portal [1-6, default: 1]: ").strip()

    preset_urls = {
        "1": "https://www.linkedin.com/jobs/search/?f_AL=true&keywords=Full%20Stack%20Developer",
        "2": "https://www.linkedin.com/jobs/search/?f_AL=true&keywords=Social%20Media%20Marketing",
        "3": "https://www.instahyre.com/jobs/",
        "4": "https://wellfound.com/jobs",
        "5": "https://www.indeed.com/jobs?q=Full+Stack+Developer&vjk=1"
    }

    if choice == "6":
        url = input("Enter custom job URL: ").strip()
    else:
        url = preset_urls.get(choice, preset_urls["1"])

    assistant = FormAssistant()
    assistant.launch_browser_session(target_url=url)

def option_generate_cover_letter():
    print("\n📝 TAILORED COVER LETTER GENERATOR")
    company = input("Company Name: ").strip()
    role = input("Job Title: ").strip()
    category = input("Category (Tech / Social Media) [default: Tech]: ").strip()
    if not category:
        category = "Tech"

    generator = CoverLetterGenerator()
    res = generator.generate(company, role, category=category)

    print("\n" + "="*50)
    print(f"SUBJECT: {res['subject']}")
    print("="*50)
    print(res['body'])
    print("="*50 + "\n")

    input("Press Enter to return to main menu...")

def option_log_job(tracker):
    print("\n➕ LOG A NEW APPLICATION")
    company = input("Company Name: ").strip()
    role = input("Job Title: ").strip()
    category = input("Category (Tech / Social) [default: Tech]: ").strip() or "Tech"
    platform = input("Platform (LinkedIn / Wellfound / Instahyre / Indeed) [default: LinkedIn]: ").strip() or "LinkedIn"
    job_url = input("Job URL (optional): ").strip()
    
    app_id = tracker.log_application(company, role, category, platform=platform, job_url=job_url)
    print(f"\n✅ Application #{app_id} successfully logged to data/job_tracker.csv!")
    input("Press Enter to return to main menu...")

def main():
    tracker = ApplicationTracker()
    
    while True:
        clear_screen()
        print_header()
        show_dashboard(tracker)
        
        print("Choose an action:")
        print("  [1] 🚀 Launch Automated Application Browser (LinkedIn / Wellfound / Indeed)")
        print("  [2] 📝 Generate Tailored Cover Letter")
        print("  [3] ➕ Log a Submitted Job Application")
        print("  [4] 📋 View All Submitted Applications")
        print("  [5] 📖 Open Master Strategy Guide")
        print("  [0] ❌ Exit Assistant")
        print("-" * 65)

        choice = input("Select option [0-5]: ").strip()

        if choice == "1":
            option_launch_browser()
        elif choice == "2":
            option_generate_cover_letter()
        elif choice == "3":
            option_log_job(tracker)
        elif choice == "4":
            apps = tracker.get_all_applications()
            print(f"\n📋 ALL SUBMITTED APPLICATIONS ({len(apps)} total):")
            print("-" * 75)
            print(f"{'ID':<4} | {'Date':<10} | {'Company':<18} | {'Role':<20} | {'Category':<8} | {'Platform':<10}")
            print("-" * 75)
            for a in apps[-15:]:  # show last 15
                print(f"{a.get('ID',''):<4} | {a.get('Date',''):<10} | {a.get('Company',''):<18} | {a.get('Role',''):<20} | {a.get('Category',''):<8} | {a.get('Platform',''):<10}")
            print("-" * 75)
            input("\nPress Enter to return to main menu...")
        elif choice == "5":
            os.system("start notepad c:\\Users\\nachi\\OneDrive\\Desktop\\job\\00_START_HERE_MASTER_INDEX.md")
        elif choice == "0":
            print("\nGood luck with your applications, Nachiket! 🚀")
            break

if __name__ == "__main__":
    main()
