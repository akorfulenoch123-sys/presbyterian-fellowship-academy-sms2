# Presbyterian Fellowship Academy School Management System (PFA-SMS)

A responsive HTML/CSS/JavaScript school portal powered by Flask and PostgreSQL. The web interface is served from HTML templates and works on desktop, tablet and mobile browsers.

## Included modules
- Role-based sign-in: administrator, teacher, accountant, parent and student account roles
- Dashboard overview
- Student registration and directory
- Teacher records
- Class management
- Attendance recording
- Fee payment records
- Examination results
- User account creation and role assignment

## Run on Windows (local testing)
1. Install Python 3.11 or newer.
2. Extract this ZIP.
3. Open Command Prompt in the extracted `PFA_School_Management_System` folder.
4. Run:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   set ADMIN_USERNAME=admin
   set ADMIN_PASSWORD=Choose-A-Strong-Password-Here
   set SECRET_KEY=replace-with-a-long-random-secret
   py app.py
   ```
5. Open `http://127.0.0.1:5000`.

If ADMIN_PASSWORD is not set, the app creates a temporary admin password `ChangeThisNow123!` for local testing. Change it immediately and do not use it on a public deployment.

## Deploy online with Render
1. Create a GitHub account and a Render account.
2. Create a private GitHub repository and upload the contents of this folder.
3. In Render, choose **New + > Blueprint**, connect the repository and select `render.yaml`.
4. When prompted, set `ADMIN_PASSWORD` to a strong unique password. Render generates `SECRET_KEY` and provisions PostgreSQL from the blueprint.
5. Deploy. Render will provide a public HTTPS URL after the build succeeds.
6. Open the URL and sign in using the administrator username and the password you supplied.
7. Create individual accounts for staff. Do not share one administrator account.

## Important production configuration
- Configure a real school logo and official contact details before launch.
- Set a strong `ADMIN_PASSWORD` and `SECRET_KEY`; never commit secrets to GitHub.
- Use the PostgreSQL database provisioned by Render, not SQLite, for the public system.
- Set up scheduled database backups and test restoring one.
- Restrict administrator accounts, use unique passwords, and remove accounts when staff leave.
- Obtain school approval and parent/guardian consent before entering student information.
- Add a privacy notice and retention policy appropriate to Ghana's Data Protection Act, 2012 (Act 843).
- Confirm hosting plan, data location, uptime and backup terms before using real student records.

## Current scope / items requiring school-specific setup
This is a functional starter system, not a fully audited school ERP. Parent/student portal pages, report-card PDF generation, SMS/email notifications, online payment gateway, fee balances/invoicing, timetable editor, bulk import/export, audit logs, password reset and two-factor authentication are not yet implemented. The parent/student roles are provisioned for future portal access but currently have no dedicated self-service pages. Review security and operational requirements before production use.

## School identity
School name: Presbyterian Fellowship Academy
Brand palette: navy blue, white and gold
