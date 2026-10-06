import json
import os

class CoverLetterGenerator:
    def __init__(self, config_dir="config", templates_dir="templates"):
        self.config_path = os.path.join(config_dir, "profile.json")
        self.tech_templates_path = os.path.join(templates_dir, "cover_letters_tech.json")
        self.social_templates_path = os.path.join(templates_dir, "cover_letters_social.json")
        
        self.profile = self._load_json(self.config_path)
        self.tech_templates = self._load_json(self.tech_templates_path).get("tech_templates", [])
        self.social_templates = self._load_json(self.social_templates_path).get("social_templates", [])

    def _load_json(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def generate(self, company_name, job_title, category="Tech", template_id=None):
        """Generates a customized cover letter for a job."""
        personal = self.profile.get("personal", {})
        
        templates = self.tech_templates if category.lower() == "tech" else self.social_templates
        if not templates:
            templates = self.tech_templates

        selected_template = None
        if template_id:
            for t in templates:
                if t.get("id") == template_id:
                    selected_template = t
                    break
        
        if not selected_template and templates:
            selected_template = templates[0]

        if not selected_template:
            return "Error: No cover letter templates found."

        replacements = {
            "company_name": company_name or "Hiring Team",
            "job_title": job_title or "Position",
            "full_name": personal.get("full_name", "Nachiket Rana"),
            "email": personal.get("email", ""),
            "phone": personal.get("phone", ""),
            "linkedin": personal.get("linkedin", ""),
            "github": personal.get("github", ""),
            "portfolio": personal.get("portfolio", "")
        }

        body = selected_template.get("body", "")
        subject = selected_template.get("subject", "")

        for key, val in replacements.items():
            body = body.replace(f"{{{key}}}", str(val))
            subject = subject.replace(f"{{{key}}}", str(val))

        return {
            "template_name": selected_template.get("name"),
            "subject": subject,
            "body": body
        }

if __name__ == "__main__":
    gen = CoverLetterGenerator()
    result = gen.generate("Google", "Full-Stack Software Engineer", category="Tech")
    print(f"Subject: {result['subject']}\n\n{result['body']}")
