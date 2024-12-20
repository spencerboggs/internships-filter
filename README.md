# Internships Filter
A Flask app that fetches and displays internship listings from GitHub README files. The user can filter the listings by company, role, and location. Additionally, users can exclude specific filters (ex. -remote to exclude remote internships) for more refined results.

You can view the original repositories, which the data is collected from, here: 
* [Cvrve & Ouckah Repo](https://github.com/cvrve/Summer2025-Internships/tree/dev)
* [Pitt CSC & Simplify Repo](https://github.com/SimplifyJobs/Summer2025-Internships/tree/dev)

## Features
* Fetch Internship Data: Collects internship listings from GitHub Internship README repositories and displays them in a table.
* Filter Listings: Filter internships by company, role, or location. Supports negative filters like -remote to exclude specific entries.
* Clear Filters: Resets applied filters for a fresh search.
* Interactive Web Interface: View detailed internship information, including company, role, location, application link, and date posted.
* Apply Status: Mark internships as applied or not applied, allowing you to track progress.

## Dependencies
The project requires the following Python libraries:
* Flask
* requests

## Usage
1. Clone the repo and install the required libraries:
```
git clone https://github.com/spencerboggs/internships-filter.git
cd internship-listings-filter
pip install -r requirements.txt
```
2. Start the app:
```
python app.py
```

The development server will most likely start on http://localhost:5000. If not, check the terminal for the correct URL.

Filtering Results:
* **Company Filter**: Enter the company name to filter internships by company.
* **Role Filter**: Enter the role name to filter internships by role.
* **Location Filter**: Enter the location to filter internships by location.
* **Negative Filters**: Use `-` before a filter term to exclude that term (e.g., `-remote` to exclude remote internships).
* **Applied Status**: Mark internships as applied or not applied, allowing users to track their progress.
* **Arrow Replacement Logic**: Any internship listing with the company name `\u21b3` (the rightwards arrow symbol) is replaced with the last valid company name in the listing. This ensures continuity in the internship data display.
