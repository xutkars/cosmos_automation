import re
import time

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


# ============================================================
# CONFIGURATION
# ============================================================

COSMOS_URL = (
    "http://cosmos.pramericalife.in:8080/"
    "home/dpli/insurance/DPLIindex.htm#/NBSApptracKer"
)


# IL App Types which are allowed to trigger Submit
ERROR_TYPES = {
    "NBS_STP_FAIL",
    "Common BO hit in IL",
    "NBS_PROPOSAL_CREATION",
    "NBS_PPHI",
    "NBS_REQUIREMENT_UPDATION",
    "NBS-IL-NOMINEE",
    "NBS_REQUIREMENT_CREATION",
    "NBS-IL-LACLIENT",
}

# Small waits because the application is Angular based
SHORT_WAIT = 0.10
IL_TABLE_TIMEOUT = 5.0
PAGE_CHANGE_TIMEOUT = 6.0
LIST_TIMEOUT = 7.0


# ============================================================
# HELPERS
# ============================================================

def normalize(text):
    """Normalize UI text."""
    if text is None:
        return ""

    return re.sub(r"\s+", " ", text).strip()


def get_proposal_locator(page):
    """
    Locator for proposal numbers in ILRole list.
    """
    return page.locator(
        "a[ng-click*='getSelectedTaskDetails']"
    ).filter(
        visible=True
    )


def get_proposal_names(page):
    """
    Get a clean snapshot of proposal names.

    IMPORTANT:
    We return strings, not locators.

    The DOM changes after clicking/submitting, so keeping old
    locators/indexes causes the same proposal to be processed
    repeatedly.
    """

    locator = get_proposal_locator(page)

    try:
        locator.first.wait_for(
            state="visible",
            timeout=LIST_TIMEOUT * 1000
        )
    except PlaywrightTimeoutError:
        return []

    names = []

    count = locator.count()

    for i in range(count):
        try:
            name = normalize(locator.nth(i).inner_text())

            if name and name not in names:
                names.append(name)

        except Exception:
            continue

    return names


def wait_for_proposal_list(page):
    """
    Wait until proposal list is visible.
    """

    locator = get_proposal_locator(page)

    try:
        locator.first.wait_for(
            state="visible",
            timeout=LIST_TIMEOUT * 1000
        )
        return True

    except PlaywrightTimeoutError:
        return False


def wait_for_il_popup(page):
    """
    Wait for IL Details popup.

    We don't rely only on #done because the popup/table
    can render in stages.
    """

    deadline = time.monotonic() + IL_TABLE_TIMEOUT

    while time.monotonic() < deadline:

        # Submit button
        try:
            if page.locator("#done:visible").count() > 0:
                return True
        except Exception:
            pass

        # Close button
        try:
            close_buttons = page.get_by_role(
                "button",
                name=re.compile(r"^Close$", re.I)
            ).filter(visible=True)

            if close_buttons.count() > 0:
                return True
        except Exception:
            pass

        # IL table header
        try:
            tables = page.locator("table:visible")

            for i in range(tables.count()):
                table = tables.nth(i)

                text = normalize(table.inner_text())

                if (
                    "IL App Type" in text
                    and "IL Status" in text
                ):
                    return True

        except Exception:
            pass

        page.wait_for_timeout(100)

    return False


def get_il_rows(page):
    """
    Get the actual IL Details rows.

    First try the known Angular ng-repeat.

    If Angular has not exposed those rows yet, find the visible
    table containing:

        IL App Type
        IL Status

    This prevents the old problem where the popup was visible
    but the automation read 0 rows.
    """

    deadline = time.monotonic() + IL_TABLE_TIMEOUT

    last_count = 0

    while time.monotonic() < deadline:

        # ----------------------------------------------------
        # METHOD 1
        # Known Angular selector
        # ----------------------------------------------------

        try:
            rows = page.locator(
                "tr[ng-repeat='ildetail in ILrespForDetails']:visible"
            )

            count = rows.count()

            if count > 0:
                return rows

            last_count = count

        except Exception:
            pass

        # ----------------------------------------------------
        # METHOD 2
        # Visible IL table
        # ----------------------------------------------------

        try:
            tables = page.locator("table:visible")

            for i in range(tables.count()):

                table = tables.nth(i)

                table_text = normalize(table.inner_text())

                if (
                    "IL App Type" not in table_text
                    or "IL Status" not in table_text
                ):
                    continue

                rows = table.locator("tr:visible")

                valid_rows = []

                for j in range(rows.count()):

                    row = rows.nth(j)

                    try:
                        cells = row.locator("td")

                        if cells.count() >= 3:
                            valid_rows.append(row)

                    except Exception:
                        continue

                if valid_rows:
                    return valid_rows

        except Exception:
            pass

        page.wait_for_timeout(100)

    return []


def open_proposal(page, proposal_name):
    """
    Open a proposal from the current page.
    """

    locator = get_proposal_locator(page)

    count = locator.count()

    for i in range(count):

        try:
            current_name = normalize(
                locator.nth(i).inner_text()
            )

            if current_name == proposal_name:

                locator.nth(i).scroll_into_view_if_needed(
                    timeout=3000
                )

                locator.nth(i).click(
                    timeout=5000
                )

                print(f"Opened proposal: {proposal_name}")

                if not wait_for_il_popup(page):
                    print("WARNING: IL popup did not fully load.")

                else:
                    print("IL Details popup opened.")

                return True

        except Exception:
            continue

    print(
        f"Could not find proposal in current page: "
        f"{proposal_name}"
    )

    return False


def close_il_details(page):
    """
    Close IL Details only when the case was NOT submitted.
    """

    try:

        close_buttons = page.get_by_role(
            "button",
            name=re.compile(r"^Close$", re.I)
        ).filter(visible=True)

        if close_buttons.count() > 0:

            close_buttons.first.click(
                timeout=3000
            )

            page.wait_for_timeout(150)

            return True

    except Exception:
        pass

    return False


def click_submit(page):
    """
    Click Submit.

    IMPORTANT:
    After Submit we NEVER click Close.

    The real frontend returns to proposal list automatically.
    """

    try:

        submit = page.locator("#done:visible")

        if submit.count() == 0:

            # Fallback using button text
            submit = page.get_by_role(
                "button",
                name=re.compile(r"^Submit$", re.I)
            ).filter(visible=True)

        if submit.count() == 0:

            print("  >>> Submit button not found.")

            return False

        print("  >>> Submit button found.")

        submit.first.scroll_into_view_if_needed(
            timeout=3000
        )

        submit.first.click(
            timeout=5000
        )

        print("  >>> Submit clicked.")

        return True

    except Exception as e:

        print(f"  >>> Submit failed: {e}")

        return False


def wait_after_submit(page):
    """
    Wait for frontend to return to proposal list.

    The frontend normally returns to PAGE 1.
    """

    deadline = time.monotonic() + LIST_TIMEOUT

    while time.monotonic() < deadline:

        try:

            proposals = get_proposal_locator(page)

            if proposals.count() > 0:

                try:
                    if proposals.first.is_visible():
                        print(
                            "  >>> Proposal list returned."
                        )
                        return True

                except Exception:
                    pass

        except Exception:
            pass

        page.wait_for_timeout(100)

    print(
        "  >>> Proposal list did not return within timeout."
    )

    return False


def read_il_details(page):
    """
    Read IL Details and determine whether this case should
    be submitted.

    Returns:

        True  = matching IL_ERROR found
        False = no matching IL_ERROR
    """

    print("Checking IL Details...")

    rows = get_il_rows(page)

    if not rows:

        print("IL rows found: 0")
        print("No IL rows found.")

        return False

    try:
        row_count = len(rows)

    except Exception:
        row_count = rows.count()

    print(f"IL rows found: {row_count}")

    for i in range(row_count):

        try:

            row = rows[i] if isinstance(rows, list) else rows.nth(i)

            cells = row.locator("td")

            if cells.count() < 3:
                continue

            proposal_no = normalize(
                cells.nth(0).inner_text()
            )

            app_type = normalize(
                cells.nth(1).inner_text()
            )

            status = normalize(
                cells.nth(2).inner_text()
            )

            print(
                f"  Row {i + 1}: "
                f"{app_type} | {status}"
            )

            # ------------------------------------------------
            # IMPORTANT:
            # App Type and Status MUST belong to SAME row.
            # ------------------------------------------------

            if (
                app_type in ERROR_TYPES
                and status.upper() == "IL_ERROR"
            ):

                print(
                    f"  >>> MATCH FOUND: "
                    f"{app_type} | {status}"
                )

                return True

        except Exception as e:

            print(
                f"  Could not read row {i + 1}: {e}"
            )

    print("No matching IL_ERROR found.")

    return False


# ============================================================
# PROCESS ONE PROPOSAL
# ============================================================

def process_proposal(page, proposal_name):
    """
    Process one proposal.

    Returns:

        "SUBMITTED"
        "COMPLETED"
        "FAILED"
    """

    print()
    print("=" * 70)
    print(f"Processing: {proposal_name}")
    print("=" * 70)

    # --------------------------------------------------------
    # Open proposal
    # --------------------------------------------------------

    if not open_proposal(page, proposal_name):

        print("  >>> Could not open proposal.")

        return "FAILED"

    # --------------------------------------------------------
    # IMPORTANT SPECIAL CASE
    #
    # If proposal contains " - "
    #
    # Example:
    #
    # 00942159 - R1400430
    #
    # Directly submit without checking IL rows.
    # --------------------------------------------------------

    if " - " in proposal_name:

        print(
            "  >>> Proposal contains ' - '. "
            "Direct Submit."
        )

        submitted = click_submit(page)

        if submitted:

            wait_after_submit(page)

            print(
                f"  >>> Case submitted: "
                f"{proposal_name}"
            )

            return "SUBMITTED"

        return "FAILED"

    # --------------------------------------------------------
    # Normal case
    # --------------------------------------------------------

    should_submit = read_il_details(page)

    if should_submit:

        print(
            "  >>> Matching IL_ERROR found."
        )

        submitted = click_submit(page)

        if submitted:

            wait_after_submit(page)

            print(
                f"  >>> Case submitted: "
                f"{proposal_name}"
            )

            return "SUBMITTED"

        print(
            "  >>> Submit failed."
        )

        return "FAILED"

    # --------------------------------------------------------
    # No matching error
    # Close popup normally.
    # --------------------------------------------------------

    close_il_details(page)

    print(
        "  >>> Case completed without Submit."
    )

    return "COMPLETED"


# ============================================================
# PAGE SIGNATURE
# ============================================================

def get_page_signature(page):
    """
    Return a signature of current proposal page.

    Used to determine whether Next actually changed
    the page.

    This is also what prevents endless clicking on Next
    after the final page.
    """

    names = get_proposal_names(page)

    return tuple(names)


# ============================================================
# NEXT PAGE
# ============================================================

def click_next_page(page):
    """
    Click Next only if it is genuinely usable.

    IMPORTANT:
    We verify that the proposal list changes.

    If clicking Next leaves the same proposal list,
    we consider it the LAST PAGE and stop.
    """

    old_signature = get_page_signature(page)

    if not old_signature:

        print(
            "Cannot determine current page signature."
        )

        return False

    candidates = page.locator(
        "a[ng-click*='selectPage(page + 1)']:visible"
    )

    count = candidates.count()

    print(
        f"Next button candidates: {count}"
    )

    if count == 0:

        print(
            "No Next button found."
        )

        return False

    next_button = None

    # --------------------------------------------------------
    # Find a usable Next button
    # --------------------------------------------------------

    for i in range(count):

        try:

            candidate = candidates.nth(i)

            # Check candidate itself
            class_name = (
                candidate.get_attribute("class")
                or ""
            ).lower()

            aria_disabled = (
                candidate.get_attribute(
                    "aria-disabled"
                )
                or ""
            ).lower()

            # Check parent <li> too
            parent_class = ""

            try:

                parent_class = (
                    candidate.locator("..")
                    .get_attribute("class")
                    or ""
                ).lower()

            except Exception:
                pass

            disabled = (
                "disabled" in class_name
                or "disabled" in parent_class
                or aria_disabled == "true"
            )

            if disabled:
                continue

            next_button = candidate

            break

        except Exception:
            continue

    if next_button is None:

        print(
            "No usable Next button."
        )

        return False

    # --------------------------------------------------------
    # Click Next
    # --------------------------------------------------------

    try:

        print("Clicking Next page...")

        next_button.scroll_into_view_if_needed(
            timeout=3000
        )

        next_button.click(
            timeout=5000
        )

    except Exception as e:

        print(
            f"Could not click Next: {e}"
        )

        return False

    # --------------------------------------------------------
    # Wait until proposal list changes
    # --------------------------------------------------------

    deadline = time.monotonic() + PAGE_CHANGE_TIMEOUT

    while time.monotonic() < deadline:

        page.wait_for_timeout(150)

        new_signature = get_page_signature(page)

        if (
            new_signature
            and new_signature != old_signature
        ):

            print(
                "Next page loaded successfully."
            )

            return True

    # --------------------------------------------------------
    # VERY IMPORTANT
    #
    # Same list after Next = last page.
    # Do NOT click Next again.
    # --------------------------------------------------------

    print(
        "Next did not change the proposal list."
    )

    print(
        "Current page is the LAST PAGE."
    )

    return False


# ============================================================
# GO BACK TO PAGE 1
# ============================================================

def go_to_first_page(page):
    """
    After Submit, frontend returns to page 1.

    This function makes sure we are actually on page 1.
    """

    current_signature = get_page_signature(page)

    if not current_signature:
        return False

    # Look for active page = 1
    try:

        active = page.locator(
            "li.active a:visible"
        )

        if active.count() > 0:

            text = normalize(
                active.first.inner_text()
            )

            if text == "1":
                return True

    except Exception:
        pass

    # Try clicking page 1 directly
    candidates = page.locator(
        "a:visible"
    )

    for i in range(candidates.count()):

        try:

            candidate = candidates.nth(i)

            text = normalize(
                candidate.inner_text()
            )

            if text != "1":
                continue

            ng_click = (
                candidate.get_attribute(
                    "ng-click"
                )
                or ""
            )

            if "selectPage" not in ng_click:
                continue

            candidate.click(timeout=3000)

            page.wait_for_timeout(300)

            return True

        except Exception:
            continue

    # If frontend automatically returned to page 1,
    # the proposal list is already usable.
    return True


# ============================================================
# NAVIGATE TO SPECIFIC PAGE
# ============================================================

def go_to_page(page, target_page):
    """
    Navigate from page 1 to target page.

    This is used after Submit because the frontend returns
    to page 1.
    """

    if target_page <= 1:
        return True

    print(
        f"  >>> Returning to page 1 -> page {target_page}"
    )

    if not go_to_first_page(page):
        return False

    for step in range(1, target_page):

        print(
            f"  >>> Moving to page {step + 1}..."
        )

        if not click_next_page(page):

            print(
                f"  >>> Could not reach page "
                f"{target_page}."
            )

            return False

    return True


# ============================================================
# PROCESS CURRENT PAGE
# ============================================================

def process_current_page(
    page,
    page_number,
    processed,
    failed,
):
    """
    Process all proposals currently belonging to this page.

    We repeatedly take a NEW snapshot because Submit causes
    the frontend to refresh and return to page 1.
    """

    print()
    print("#" * 70)
    print(f"PROCESSING PAGE {page_number}")
    print("#" * 70)

    # --------------------------------------------------------
    # First snapshot
    # --------------------------------------------------------

    names = get_proposal_names(page)

    if not names:

        print(
            f"No proposals found on page {page_number}."
        )

        return True

    print(
        f"Proposals on page {page_number}: "
        f"{len(names)}"
    )

    # --------------------------------------------------------
    # Keep processing until there are no unprocessed cases
    # on this page.
    # --------------------------------------------------------

    while True:

        current_names = get_proposal_names(page)

        if not current_names:

            print(
                "No proposals currently visible."
            )

            break

        # ----------------------------------------------------
        # Find first unprocessed proposal
        # ----------------------------------------------------

        proposal_to_process = None

        for name in current_names:

            if name in processed:
                continue

            if name in failed:
                continue

            proposal_to_process = name
            break

        # ----------------------------------------------------
        # Nothing left on current page
        # ----------------------------------------------------

        if proposal_to_process is None:

            print()
            print(
                f"Finished processing page "
                f"{page_number}."
            )

            break

        # ----------------------------------------------------
        # Display tracking information
        # ----------------------------------------------------

        try:
            position = current_names.index(
                proposal_to_process
            ) + 1

        except ValueError:
            position = "?"

        print()
        print(
            f"Processing {position}/"
            f"{len(current_names)}: "
            f"{proposal_to_process}"
        )

        # ----------------------------------------------------
        # Process proposal
        # ----------------------------------------------------

        result = process_proposal(
            page,
            proposal_to_process
        )

        # ----------------------------------------------------
        # SUBMITTED
        # ----------------------------------------------------

        if result == "SUBMITTED":

            processed.add(
                proposal_to_process
            )

            print(
                f"  >>> Marked processed: "
                f"{proposal_to_process}"
            )

            # -----------------------------------------------
            # Frontend returns to page 1.
            #
            # We must go back to the page we were processing.
            # -----------------------------------------------

            page.wait_for_timeout(200)

            if not wait_for_proposal_list(page):

                print(
                    "  >>> Proposal list not available "
                    "after Submit."
                )

                failed.add(
                    proposal_to_process
                )

                continue

            if page_number > 1:

                returned = go_to_page(
                    page,
                    page_number
                )

                if not returned:

                    print(
                        "  >>> Original page no longer "
                        "exists after Submit."
                    )

                    # Restart from page 1.
                    # This handles the situation where deleting/
                    # submitting cases caused the last page to
                    # disappear.

                    page_number = 1

                    if not go_to_first_page(page):
                        break

            continue

        # ----------------------------------------------------
        # COMPLETED WITHOUT SUBMIT
        # ----------------------------------------------------

        if result == "COMPLETED":

            processed.add(
                proposal_to_process
            )

            continue

        # ----------------------------------------------------
        # FAILED
        # ----------------------------------------------------

        failed.add(
            proposal_to_process
        )

        print(
            f"  >>> Marked failed: "
            f"{proposal_to_process}"
        )


# ============================================================
# MAIN
# ============================================================

def run_automation(username, password, status=None):
    """Run the COSMOS Playwright automation using credentials supplied by Flask."""

    processed = set()
    failed = set()
    submitted_count = 0

    def update_status(**kwargs):
        if status is not None:
            status.update(kwargs)

    with sync_playwright() as p:
        browser = None
        try:
            update_status(status="Running", message="Opening COSMOS...")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            print("1. Opening COSMOS...")
            page.goto(COSMOS_URL, wait_until="domcontentloaded", timeout=30000)
            print("2. Login page opened")
            update_status(message="Login page opened.")

            inputs = page.locator("input")
            inputs.nth(0).wait_for(state="visible", timeout=15000)
            inputs.nth(0).fill(username)
            inputs.nth(1).fill(password)
            print("3. Username/password entered")
            update_status(message="Username/password entered.")

            page.get_by_role("button", name=re.compile(r"Login", re.I)).click()
            print("4. Login clicked")
            update_status(message="Login submitted. Waiting for Inbox...")

            inbox = page.get_by_text("Inbox", exact=True)
            inbox.wait_for(state="visible", timeout=30000)
            print("5. Inbox found")
            inbox.click()
            print("6. Inbox clicked")

            il_role = page.locator("div.role").filter(has_text=re.compile(r"^ILRole$"))
            il_role.first.wait_for(state="visible", timeout=30000)
            print("7. ILRole found")
            il_role.first.click()
            print("8. ILRole clicked")
            update_status(message="ILRole opened. Loading proposals...")

            if not wait_for_proposal_list(page):
                print("ERROR: Proposal list did not load.")
                raise RuntimeError("Proposal list did not load.")

            print("9. Proposal list loaded.")
            page_number = 1
            safety_counter = 0

            # Estimate/update total pages as discovered.
            update_status(current_page=1, total_pages=1, message="Proposal list loaded.")

            while True:
                safety_counter += 1
                if safety_counter > 100:
                    print("Safety limit reached. Stopping pagination.")
                    break

                if not wait_for_proposal_list(page):
                    print("Proposal list unavailable.")
                    break

                update_status(current_page=page_number, message=f"Processing page {page_number}...")

                # Process proposals while exposing progress to the frontend.
                names_before = get_proposal_names(page)
                page_total = len(names_before)
                update_status(current_page=page_number, total_pages=max(page_number, 1), message=f"Processing {page_total} proposals on page {page_number}...")

                while True:
                    current_names = get_proposal_names(page)
                    proposal_to_process = next((n for n in current_names if n not in processed and n not in failed), None)
                    if proposal_to_process is None:
                        break

                    update_status(current_proposal=proposal_to_process, message=f"Processing proposal {proposal_to_process}...")
                    result = process_proposal(page, proposal_to_process)

                    if result == "SUBMITTED":
                        processed.add(proposal_to_process)
                        submitted_count += 1
                        update_status(processed=len(processed), submitted=submitted_count, current_proposal=proposal_to_process, message=f"Submitted {proposal_to_process}.")
                    elif result == "COMPLETED":
                        processed.add(proposal_to_process)
                        update_status(processed=len(processed), current_proposal=proposal_to_process, message=f"Completed {proposal_to_process} without Submit.")
                    else:
                        failed.add(proposal_to_process)
                        update_status(errors=len(failed), current_proposal=proposal_to_process, message=f"Failed to process {proposal_to_process}.")

                    if result == "SUBMITTED":
                        page.wait_for_timeout(200)
                        if not wait_for_proposal_list(page):
                            failed.add(proposal_to_process)
                            update_status(errors=len(failed), message="Proposal list unavailable after Submit.")
                            continue
                        if page_number > 1 and not go_to_page(page, page_number):
                            page_number = 1
                            if not go_to_first_page(page):
                                break

                old_signature = get_page_signature(page)
                if not old_signature:
                    break

                print(f"Checking whether page {page_number + 1} exists...")
                update_status(message=f"Checking for page {page_number + 1}...")
                if not click_next_page(page):
                    print("No further page detected. Last page reached.")
                    break

                page_number += 1
                update_status(current_page=page_number, total_pages=page_number, message=f"Page {page_number} loaded.")

            print("\n" + "=" * 70)
            print("AUTOMATION COMPLETED")
            print("=" * 70)
            print(f"Total processed: {len(processed)}")
            print(f"Total failed: {len(failed)}")
            if failed:
                print("Failed proposals:")
                for proposal in sorted(failed):
                    print(f"  - {proposal}")

            update_status(
                running=False,
                status="Completed",
                message=f"Automation completed. Processed: {len(processed)}, Failed: {len(failed)}.",
                processed=len(processed),
                submitted=submitted_count,
                errors=len(failed),
                current_proposal=""
            )

        except KeyboardInterrupt:
            print("Automation stopped by user.")
            update_status(running=False, status="Stopped", message="Automation stopped by user.")
            raise
        except Exception as e:
            print("\n" + "=" * 70)
            print("AUTOMATION ERROR")
            print("=" * 70)
            print(e)
            update_status(running=False, status="Error", message=str(e), current_proposal="")
            raise
        finally:
            try:
                if browser:
                    browser.close()
            except Exception:
                pass


def main():
    """Optional manual mode; Flask normally calls run_automation()."""
    import getpass
    username = input("Enter COSMOS username: ").strip()
    password = getpass.getpass("Enter COSMOS password: ")
    run_automation(username, password)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()

    
