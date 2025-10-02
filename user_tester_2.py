from operator import add
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import keyring
import time
import os
import s4
from s4 import clarity
from s4.clarity import role

# ------------------------
# Configuration
# ------------------------
server = "dev" # Change this to 'prod' or 'staging' as needed
role_name = "Editor"
base_url = f"https://clarity-{server}.btolims.com"

CLARITY_SERVERS = {
    "prod": "https://billiontoone-prod.claritylims.com/api/v2",
    "staging": "https://clarity-staging.btolims.com/api/v2",
    "dev": "https://clarity-dev.btolims.com/api/v2"
}

# Define the same SERVICE_NAME used in store_creds.py
SERVICE_NAME = "user_tester_app"

# Retrieve stored credentials
username = keyring.get_password(SERVICE_NAME, "USERNAME_KEY")
password = keyring.get_password(SERVICE_NAME, username)  # use the username as the key

# Connect to Clarity API create the lims object
lims = s4.clarity.LIMS(CLARITY_SERVERS[server], username, password)
print(f'Connected to {server} - API version: {lims.versions[0]["major"]}')
print(f"The username is {username}")

def add_role_to_user(user, role_obj, username, role_name):
    """Add a role to a user."""   
    # Add the role
    user.add_role(role_obj)
    user.commit()
    print(f"Added {role_name} role to {username}")

def remove_role_from_user(user, role_obj, username, role_name):
    """Remove a role from a user."""
    # Remove the role
    user.remove_role(role_obj)  
    user.commit()
    print(f"Removed {role_name} role from {username}")

def navigate_and_click(driver, wait, element_name, strategies, fallback_url=None, wait_after=2):
    """
    Try multiple strategies to find and click an element.
    
    Args:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
        element_name: Description of element for logging
        strategies: List of tuples (selector_type, selector_value, description)
        fallback_url: Optional URL to navigate to if all strategies fail
        wait_after: Seconds to wait after successful action
       
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{element_name}:")
    
    for selector_type, selector_value, description in strategies:
        try:
            print(f"  Trying: {description}...")
            
            if selector_type == "CSS":
                element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector_value)))
            elif selector_type == "XPATH":
                element = wait.until(EC.element_to_be_clickable((By.XPATH, selector_value)))
            elif selector_type == "ID":
                element = wait.until(EC.element_to_be_clickable((By.ID, selector_value)))
            else:
                continue
            
            # Try regular click first, then JavaScript click if needed
            try:
                element.click()
                print("Selenium Click")
            except:
                driver.execute_script("arguments[0].click();", element)
                print("Javascript Click")
            
            print(f"  ✓ Success using {description}!")
            time.sleep(wait_after)
            return True
            
        except Exception as e:
            print(f"  ✗ Failed: {str(e)[:50]}...")
    
    # If all strategies failed and we have a fallback URL
    if fallback_url:
        print(f"  → All methods failed. Navigating directly to URL...")
        driver.get(fallback_url)
        print(f"  ✓ Direct navigation completed!")
        time.sleep(wait_after)
        return True
    
    print(f"  ✗ Could not complete action for {element_name}")
    return False

def select_dropdown_option(driver, wait, dropdown_id, option_text, wait_for_load=15):
    """
    Select an option from a React dropdown/multiselect widget.
    
    Args:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
        dropdown_id: ID of the dropdown element
        option_text: Text of the option to select
        wait_for_load: Seconds to wait for dropdown to load (default 15)
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"  Selecting '{option_text}' from {dropdown_id}...")
    
    try:
        # Wait longer for dropdowns to fully load
        long_wait = WebDriverWait(driver, wait_for_load)
        
        # Find and click the main dropdown container to open it
        dropdown = long_wait.until(
            EC.element_to_be_clickable((By.ID, dropdown_id))
        )
        
        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        time.sleep(0.5)
        
        # Click to open dropdown - try regular click first, then JavaScript
        try:
            dropdown.click()
        except:
            driver.execute_script("arguments[0].click();", dropdown)
        
        # Wait for dropdown options to be visible
        time.sleep(1)  # Small delay for animation
        
        # Try multiple strategies to find and click the option
        strategies = [
            # Strategy 1: Direct text match in listbox
            (By.XPATH, f"//ul[@id='{dropdown_id}__listbox']//li[text()='{option_text}']"),
            # Strategy 2: Contains text (in case of extra whitespace)
            (By.XPATH, f"//ul[@id='{dropdown_id}__listbox']//li[contains(text(), '{option_text}')]"),
            # Strategy 3: Any visible li with matching text
            (By.XPATH, f"//li[@role='option' and contains(text(), '{option_text}')]"),
            # Strategy 4: CSS selector approach
            (By.CSS_SELECTOR, f"#{dropdown_id}__listbox li[role='option']")
        ]
        
        option_clicked = False
        for strategy_type, strategy_selector in strategies[:3]:  # Try text-based strategies first
            try:
                option = wait.until(EC.element_to_be_clickable((strategy_type, strategy_selector)))
                driver.execute_script("arguments[0].click();", option)
                option_clicked = True
                print(f"    ✓ Selected '{option_text}' successfully!")
                break
            except:
                continue
        
        # If text strategies failed, try iterating through all options
        if not option_clicked:
            try:
                all_options = driver.find_elements(By.CSS_SELECTOR, f"#{dropdown_id}__listbox li[role='option']")
                for option in all_options:
                    if option_text.lower() in option.text.lower():
                        driver.execute_script("arguments[0].click();", option)
                        option_clicked = True
                        print(f"    ✓ Selected '{option_text}' successfully!")
                        break
            except:
                pass
        
        if not option_clicked:
            # Last resort: try clicking by option position if we know the exact text
            try:
                # Click the dropdown again to ensure it's open
                dropdown.click()
                time.sleep(0.5)
                
                # For known options, we can use their position
                option_map = {
                    "Administrative Lab": 0,
                    "Editor": 2,
                    "Collaborator": 1,
                    # Add more mappings as needed
                }
                
                if option_text in option_map:
                    option_index = option_map[option_text]
                    option_element = driver.find_element(
                        By.CSS_SELECTOR, 
                        f"#{dropdown_id}__listbox__option__{option_index}"
                    )
                    driver.execute_script("arguments[0].click();", option_element)
                    option_clicked = True
                    print(f"    ✓ Selected '{option_text}' by position!")
            except:
                pass
        
        # Wait a bit after selection
        time.sleep(1)
        
        if option_clicked:
            return True
        else:
            print(f"    ✗ Could not select '{option_text}' from {dropdown_id}")
            return False
            
    except Exception as e:
        print(f"    ✗ Error selecting dropdown option: {str(e)[:100]}...")
        return False


# Element strategies definition
ELEMENT_STRATEGIES = {
    "configuration": [
        ("CSS", "#navbar-menu-ul > li:nth-child(4) > a", "navbar CSS selector"),
        ("XPATH", "//a[@href='/clarity/configuration']", "href XPath"),
        ("XPATH", "//a[text()='Configuration']", "text XPath")
    ],
    "user_management": [
        # ("CSS", "#configuration-app-container .tab-panel-header > div:nth-child(4)", "4th tab CSS"),
        ("XPATH", "//div[contains(@class, 'tab-title') and contains(text(), 'USER MANAGEMENT')]", "text XPath"),
        ("XPATH", "//div[contains(@class, 'tab') and contains(., 'USER')]", "partial text XPath")
    ]
}

FORM_FIELDS = {
    "firstName": "Emil",
    "lastName": "Test", 
    "username": username
}
# Fallback URLs
FALLBACK_URLS = {
    "configuration": f"{base_url}/clarity/configuration",
    "user_management": f"{base_url}/clarity/configuration/user-management/users",
}

# ------------------------
# Main Script
# ------------------------

# Get current user
current_user = lims.researchers.query(**{
    'firstname': ['Emil'],
    'lastname': "Test"
})
     
print(f"Current user: {current_user[0].first_name} {current_user[0].last_name}")
print(f"Current user: {current_user[0].username}")

role = lims.roles.get_by_name(role_name)

print(f"Current roles for {username}:")
for r in current_user[0].roles:
    print(f"  - {r.name}")

# Change the function here to add or remove the role
add_role_to_user(current_user[0], role, username, role_name)

print(f"Current roles for {username}:")
for r in current_user[0].roles:
    print(f"  - {r.name}")

if not username or not password:
    print("Credentials not found. Please run store_creds.py first.")
    exit(1)

print(f"Starting automation as {username}")

# Initialize driver
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 60)

try:
    # Login
    print("\nStep 1: Login")
    driver.get(f"{base_url}/clarity/login/auth?unauthenticated=1")
    
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "sign-in").click()
    
    print("  ✓ Login submitted, waiting for page load...")
    time.sleep(3)

    # Navigate to Configuration
    navigate_and_click(
        driver, wait,
        "Step 2: Navigate to Configuration",
        ELEMENT_STRATEGIES["configuration"],
        FALLBACK_URLS["configuration"],
        wait_after=3
    )
    
    # Click User Management tab
    navigate_and_click(
        driver, wait,
        "Step 3: Click User Management Tab",
        ELEMENT_STRATEGIES["user_management"],
        FALLBACK_URLS["user_management"],
        wait_after=5  # Give more time for user list to load
    )
    
    print("\nStep 4: Wait for User List to Load")
    
    # DON'T refresh - we just navigated here!
    # driver.refresh()  # REMOVED - this was causing the problem
    
    # Smart wait for user list to load
    print("  Waiting for user list to load...")
    max_wait_time = 60  # Reduced from 300 - shouldn't take that long
    start_time = time.time()
    page_loaded = False
    
    # Method 1: Wait for JavaScript to report page is ready
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("  ✓ DOM ready state: complete")
    except:
        print("  ⚠ Could not confirm DOM ready state")
    
    # Method 2: Wait for specific elements that indicate the user list has loaded
    while not page_loaded and (time.time() - start_time) < max_wait_time:
        try:
            # Check multiple indicators that the page has loaded
            indicators = {
                "grid_container": len(driver.find_elements(By.CLASS_NAME, "g-col-grid-bar-lg")) > 0,
                "value_elements": len(driver.find_elements(By.CSS_SELECTOR, ".g-col-value")) > 0,
                "user_management_tab": len(driver.find_elements(By.XPATH, "//div[contains(text(), 'USER MANAGEMENT')]")) > 0,
                "any_table_or_grid": len(driver.find_elements(By.CSS_SELECTOR, "div[role='grid'], div[role='table'], table")) > 0,
                "user_rows": len(driver.find_elements(By.CSS_SELECTOR, "tr, div[role='row']")) > 0,
                "any_users": len(driver.find_elements(By.XPATH, "//*[contains(text(), '@')]")) > 0  # Look for email addresses
            }
            
            # Check if we have the main indicators
            if indicators["value_elements"]:
                page_loaded = True
                elapsed = round(time.time() - start_time, 1)
                print(f"  ✓ Page loaded successfully in {elapsed} seconds")
                print(f"    - Found {driver.find_elements(By.CSS_SELECTOR, '.g-col-value').__len__()} .g-col-value elements")
                break
            elif indicators["any_users"] or indicators["user_rows"]:
                # Found users in a different format
                page_loaded = True
                elapsed = round(time.time() - start_time, 1)
                print(f"  ✓ User list loaded (alternative format) in {elapsed} seconds")
                if indicators["user_rows"]:
                    print(f"    - Found {len(driver.find_elements(By.CSS_SELECTOR, 'tr, div[role=\"row\"]'))} user rows")
                break
            elif indicators["grid_container"] and indicators["any_table_or_grid"]:
                # Grid structure is there but might still be loading data
                print("  ⏳ Grid structure found, waiting for data...")
                time.sleep(1)
            else:
                # Page structure not ready yet
                elapsed = round(time.time() - start_time, 1)
                if elapsed % 5 == 0:  # Print status every 5 seconds
                    # Debug: Show what we're actually seeing
                    print(f"  ⏳ Still waiting... ({elapsed}s elapsed)")
                    if elapsed % 10 == 0:
                        print(f"    Debug - Found elements: {[k for k,v in indicators.items() if v]}")
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  ⚠ Error during wait: {str(e)[:50]}...")
            time.sleep(1)
    
    # Check if we timed out
    if not page_loaded:
        elapsed = round(time.time() - start_time, 1)
        print(f"  ⚠ Page load timeout after {elapsed} seconds. Proceeding anyway...")
    
    # Additional smart wait: Wait for any loading spinners to disappear
    try:
        # Wait for common loading indicators to disappear
        WebDriverWait(driver, 5).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, .loader, [class*='loading'], [class*='spinner']"))
        )
        print("  ✓ No loading indicators detected")
    except:
        pass  # No loading indicators found or they disappeared - good!
    
    # Small stabilization pause
    time.sleep(1)
    
    print("\n" + "-"*50)
    print("STARTING USER SEARCH")
    print("-"*50)
    
    # Dynamically construct the search name from form fields
    search_name = f"{FORM_FIELDS.get('firstName', '')} {FORM_FIELDS.get('lastName', '')}"
    print(f"  Search target: '{search_name}'")
    print(f"  Current URL: {driver.current_url}")
    print(f"  Page title: {driver.title}")
    
    # Check if we're on the right page
    if "user" not in driver.current_url.lower():
        print("  ⚠ WARNING: URL doesn't contain 'user' - might not be on user management page")
    
    # Final check for grid elements before searching
    print("\n  Verifying grid elements...")
    try:
        grid_containers = driver.find_elements(By.CLASS_NAME, "g-col-grid-bar-lg")
        value_elements_count = len(driver.find_elements(By.CSS_SELECTOR, ".g-col-value"))
        
        print(f"  Grid containers: {len(grid_containers)}")
        print(f"  Value elements: {value_elements_count}")
        
        if value_elements_count == 0:
            print("  ⚠ No .g-col-value elements found. Checking alternative selectors...")
            # Try to find any span elements
            all_spans = driver.find_elements(By.TAG_NAME, "span")
            print(f"  Total span elements on page: {len(all_spans)}")
            
            # Look for table or grid structures
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"  Tables found: {len(tables)}")
            
            divs_with_role = driver.find_elements(By.CSS_SELECTOR, "div[role='grid'], div[role='table']")
            print(f"  Divs with grid/table role: {len(divs_with_role)}")
    except Exception as e:
        print(f"  ⚠ Error checking grid: {str(e)[:100]}...")
    
    # Search for the user with multiple strategies
    print("\n" + "-"*50)
    print("EXECUTING SEARCH STRATEGIES")
    print("-"*50)
    
    user_found = False
    found_details = ""
    
    # Strategy 1: Direct text match in .g-col-value elements
    print("\n  === Strategy 1: Direct text match ===")
    try:
        value_elements = driver.find_elements(By.CSS_SELECTOR, ".g-col-value")
        print(f"  Checking {len(value_elements)} .g-col-value elements for '{search_name}'...")
        
        if len(value_elements) == 0:
            print("  ⚠ No .g-col-value elements to search!")
        
        # Show first few elements for debugging
        for i in range(min(5, len(value_elements))):
            text = value_elements[i].text.strip()
            if text:  # Only show non-empty elements
                print(f"    Element {i}: '{text[:50]}...' " if len(text) > 50 else f"    Element {i}: '{text}'")
        
        for i, element in enumerate(value_elements):
            if search_name in element.text:
                user_found = True
                found_details = f"Found exact match: '{search_name}' in g-col-value (element #{i})"
                print(f"    ✓ {found_details}")
                break
    except Exception as e:
        print(f"    ✗ Strategy 1 failed: {str(e)[:50]}...")
    
    # Strategy 2: Case-insensitive match in .g-col-value elements
    if not user_found:
        try:
            print("  Strategy 2: Case-insensitive search...")
            value_elements = driver.find_elements(By.CSS_SELECTOR, ".g-col-value")
            for element in value_elements:
                if search_name.lower() in element.text.lower().strip():
                    user_found = True
                    found_details = f"Found case-insensitive match: '{element.text.strip()}' contains '{search_name}'"
                    print(f"    ✓ {found_details}")
                    break
        except Exception as e:
            print(f"    ✗ Strategy 2 failed: {str(e)[:50]}...")
    
    # Strategy 3: XPath with contains text
    if not user_found:
        try:
            print("  Strategy 3: XPath search with contains...")
            xpath = f"//span[@class='g-col-value' and contains(text(), '{search_name}')]"
            user_element = driver.find_element(By.XPATH, xpath)
            user_found = True
            found_details = f"Found via XPath: '{user_element.text}'"
            print(f"    ✓ {found_details}")
        except:
            print(f"    ✗ Strategy 3: No match with XPath contains")
    
    # Strategy 4: Search for username as fallback
    if not user_found:
        try:
            username = FORM_FIELDS.get('username', '')
            if username:
                print(f"  Strategy 4: Searching for username '{username}'...")
                value_elements = driver.find_elements(By.CSS_SELECTOR, ".g-col-value")
                for element in value_elements:
                    if username.lower() in element.text.lower():
                        user_found = True
                        found_details = f"Found username match: '{element.text.strip()}' contains '{username}'"
                        print(f"    ✓ {found_details}")
                        break
        except Exception as e:
            print(f"    ✗ Strategy 4 failed: {str(e)[:50]}...")
    
    # Strategy 5: Search for email as last resort
    if not user_found:
        try:
            email = FORM_FIELDS.get('email', '')
            if email:
                print(f"  Strategy 5: Searching for email '{email}'...")
                value_elements = driver.find_elements(By.CSS_SELECTOR, ".g-col-value")
                for element in value_elements:
                    if email.lower() in element.text.lower():
                        user_found = True
                        found_details = f"Found email match: '{element.text.strip()}' contains '{email}'"
                        print(f"    ✓ {found_details}")
                        break
        except Exception as e:
            print(f"    ✗ Strategy 5 failed: {str(e)[:50]}...")
    
    # Strategy 6: Check if name parts appear in adjacent columns
    if not user_found:
        try:
            print("  Strategy 6: Checking for name parts in grid...")
            first_name = FORM_FIELDS.get('firstName', '')
            last_name = FORM_FIELDS.get('lastName', '')
            
            # Find all g-col-col containers
            containers = driver.find_elements(By.CSS_SELECTOR, ".g-col-col")
            for container in containers:
                container_text = container.text.lower()
                if first_name.lower() in container_text and last_name.lower() in container_text:
                    user_found = True
                    found_details = f"Found name parts in container: {container.text[:100]}"
                    print(f"    ✓ {found_details}")
                    break
        except Exception as e:
            print(f"    ✗ Strategy 6 failed: {str(e)[:50]}...")
    
    # Print final result
    print("\n" + "="*50)
    if user_found:
        print(f"✓ SUCCESS: User '{search_name}' FOUND in the user list!")
        print(f"  Details: {found_details}")
    else:
        print(f"✗ NOT FOUND: User '{search_name}' was not found in the user list")
        print(f"  Searched for: Name='{search_name}', Username='{FORM_FIELDS.get('username', '')}', Email='{FORM_FIELDS.get('email', '')}'")
    print("="*50)
    
    # Store test results in memory for PDF generation
    test_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "search_name": search_name,
        "role": role,
        "found": user_found,
        "details": found_details if user_found else f"User '{search_name}' not found"
    }
    
    # Generate PDF Report
    print("\nStep 5: Generate PDF Report")
    from user_test_report_2 import generate_pdf_report
    
    try:
        pdf_path = generate_pdf_report(test_results)
        print(f"  ✓ PDF report generated: {pdf_path}")
    except Exception as e:
        print(f"  ✗ Could not generate PDF: {str(e)}")
        print(f"  Test results stored in memory: {test_results}")
    
    print("\nAutomation completed successfully!")
    
except Exception as e:
    print(f"\n Error during automation: {e}")


finally:
    # Keep browser opens
    input("\nPress Enter to close the browser...")
    driver.quit()