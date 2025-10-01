# User Tester - Clarity LIMS Automation

Automated testing tool for Clarity LIMS user management functionality.

## Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

**Note:** The `s4` package (Clarity LIMS API library) needs to be installed separately. Contact your team for installation instructions.

### 2. Configure Credentials

1. Copy the template file:
   ```bash
   cp store_creds_template.py store_creds.py
   ```

2. Edit `store_creds.py` and replace the placeholder values with your actual credentials:
   - `USERNAME`: Your Clarity LIMS username
   - `PASSWORD`: Your Clarity LIMS password

3. Run the script to store credentials securely in macOS Keychain:
   ```bash
   python3 store_creds.py
   ```

**IMPORTANT:** Never commit `store_creds.py` to version control! It's already excluded in `.gitignore`.

### 3. Configure Server and Role

Edit the configuration section in `user_tester_2.py`:
- `server`: Choose between "dev", "staging", or "prod"
- `role_name`: Set the role you want to test (e.g., "Editor")
- `base_url`: Automatically constructed based on server choice

## Usage

Run the main automation script:

```bash
python3 user_tester_2.py
```

The script will:
1. Log into Clarity LIMS using stored credentials
2. Navigate to User Management
3. Search for the specified user
4. Generate a PDF test report

## Project Structure

- `user_tester_2.py` - Main automation script
- `user_test_report_2.py` - PDF report generation module
- `store_creds_template.py` - Template for credential storage (copy to `store_creds.py`)
- `store_creds.py` - Your actual credentials (DO NOT COMMIT)
- `test_reports/` - Generated PDF test reports (excluded from git)
- `requirements.txt` - Python dependencies

## Security Notes

- Credentials are stored in macOS Keychain for security
- Never hardcode passwords in your scripts
- The `.gitignore` file excludes all sensitive files
- Test reports may contain sensitive data and are excluded from git

## Troubleshooting

If you get a "Module not found" error:
1. Make sure all dependencies are installed: `pip3 install -r requirements.txt`
2. Ensure the `s4` package is properly installed
3. Check if you need to activate a virtual environment

## License

[Your License Here]
