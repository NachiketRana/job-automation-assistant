import os
import csv
from datetime import datetime

class ApplicationTracker:
    def __init__(self, data_dir="data", filename="job_tracker.csv"):
        self.data_dir = data_dir
        self.filepath = os.path.join(data_dir, filename)
        self.headers = [
            "ID", "Date", "Company", "Role", "Category", 
            "Platform", "Status", "Job_URL", "Cover_Letter_Used", "Notes"
        ]
        self._ensure_csv_exists()

    def _ensure_csv_exists(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
        
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_application(self, company, role, category, platform="LinkedIn", job_url="", cover_letter="", notes="Applied via Assistant"):
        """Logs a newly submitted job application."""
        apps = self.get_all_applications()
        next_id = len(apps) + 1
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        row = [
            next_id, date_str, company, role, category,
            platform, "Applied", job_url, cover_letter[:50] + "..." if len(cover_letter) > 50 else cover_letter, notes
        ]

        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        
        return next_id

    def get_all_applications(self):
        if not os.path.exists(self.filepath):
            return []
        
        apps = []
        with open(self.filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                apps.append(row)
        return apps

    def get_stats(self):
        apps = self.get_all_applications()
        tech_count = sum(1 for a in apps if a.get("Category", "").lower() == "tech")
        social_count = sum(1 for a in apps if a.get("Category", "").lower() in ["social", "social media", "marketing"])
        hybrid_count = len(apps) - (tech_count + social_count)

        return {
            "total_applied": len(apps),
            "target_total": 150,
            "tech_count": tech_count,
            "tech_target": 100,
            "social_count": social_count,
            "social_target": 50,
            "hybrid_count": hybrid_count,
            "progress_percent": round((len(apps) / 150) * 100, 1) if apps else 0.0
        }

if __name__ == "__main__":
    tracker = ApplicationTracker()
    tracker.log_application("Acme Corp", "Full-Stack Developer", "Tech", "LinkedIn", "https://linkedin.com/jobs/view/12345")
    stats = tracker.get_stats()
    print("Application Stats:", stats)
