import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class TanglinTennisCourtHandler:
    def __init__(self, username: str, password: str):
        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self._username = username
        self._password = password

        self._is_logged_in = False

    def __del__(self):
        self.quit()

    def quit(self):
        self._driver.quit()

    def make_reservations(self, date: str, indoor: bool, duration: int, times: list[int]):
        assert duration in (1, 2), "duration can only be 1 or 2 hours"

        date = pd.Timestamp(date).floor('d')
        self._login()
        # wait till that time and start loading options, it'll take approximate 5s depending on network connectivity to load new pages
        self._go_to_cms_page()
        self._set_options(date, indoor, duration)
        self._wait(till='06:59:58')
        self._refresh_selections(date)

        failures = []
        for t in times:
            try:
                success = self._reserve_time(t)
                if success:
                    print("Made a reservation at time {t:02d}:00. Check your email for more information")
                    return

            except Exception:
                failures.append(t)

        if len(failures) > 0:
            print("Did not manage to book times: \n" + '\n'.join(f'  - {t:02d}:00' for t in failures))

    def _login(self):
        """Logs into the Tanglin Club website"""
        if self._is_logged_in:
            return

        self._driver.get("https://thetanglinclub.clubhouseonline-e3.net/login.aspx")

        _chunk = "p_lt_PageContent_pageplaceholder_p_lt_zoneRight_CHOLogin_LoginControl_ctl00_Login1_"
        login_input_id = f"{_chunk}UserName"
        password_input_id = f"{_chunk}Password"
        login_button_id = f"{_chunk}LoginButton"
        self._check_element((By.ID, login_input_id), "Timeout encountered while loading login page")

        login_input: WebElement = self._driver.find_element(By.ID, login_input_id)
        login_input.send_keys(self._username)

        password_input: WebElement = self._driver.find_element(By.ID, password_input_id)
        password_input.send_keys(self._password)

        login_button: WebElement = self._driver.find_element(By.ID, login_button_id)
        login_button.click()

        logged_in_header_id = "p_lt_Header_MyProfilePages_divSignedIn"
        self._check_element((By.ID, logged_in_header_id), "Could not identify div that ensures we are logged in")

        self._is_logged_in = True

    def _go_to_cms_page(self):
        """Goes to the CMS page"""
        self._driver.get("https://thetanglinclub.clubhouseonline-e3.net/CMSModules/CHO/CourtManagement/CourtBooking.aspx")
        self._check_element((By.CSS_SELECTOR, 'div.date-selector.ng-isolate-scope'), "Could not load Tennis booking page", 5)

    def _set_options(self, date: pd.Timestamp, indoor: bool, duration=2):
        """Sets up the Tennis options. The outcome of this is a Table of available time slots in the webpage."""

        selector_css = "div.dropdown.ng-isolate-scope.ng-not-empty.ng-valid"
        # select indoor or outdoor courts and num hours
        option_li_selector = 'li.ng-binding.ng-scope'

        self._select_date(date)

        def _select_option(target: str):
            self._check_element((By.CSS_SELECTOR, f"{selector_css}.open"))
            for ee in self._driver.find_elements(By.CSS_SELECTOR, option_li_selector):
                if ee.text == target:
                    print(f"Switching to '{target}'")
                    ee.click()
                    self._check_load_okay()
                    break
            else:
                raise RuntimeError(f"Could not detect {duration_text} option")

        for e in self._driver.find_elements(By.CSS_SELECTOR, "a.dropdown-display.ng-binding"):
            match e.text:
                case 'Tennis Courts - Outdoor Tennis Court.' | 'Tennis Courts - Indoor Tennis Court.' | \
                     'Squash Courts - Singles Squash Courts' | 'Squash Courts - Doubles Squash Courts':
                    # this sets the correct court type
                    if (indoor and e.text == 'Tennis Courts - Indoor Tennis Court.') or (not indoor and e.text == 'Tennis Courts - Outdoor Tennis Court.'):
                        continue

                    e.click()  # this opens the selector
                    self._check_element((By.CSS_SELECTOR, f"{selector_css}.open"), "Could not open court type selector")
                    for ee in self._driver.find_elements(By.CSS_SELECTOR, option_li_selector):  # type: WebElement
                        if ((indoor and ee.text == 'Tennis Courts - Indoor Tennis Court.') or
                                (not indoor and ee.text == 'Tennis Courts - Outdoor Tennis Court.')):
                            print(f"Switching to court type: {ee.text}")
                            ee.click()
                            self._check_load_okay()
                            break
                    else:
                        raise RuntimeError(f"Could not detect {'Indoors' if indoor else 'Outdoors'} option")
                case '1 hour' | '2 hours':
                    # this sets the correct duration
                    duration_text = f"{duration} hour{'s' if duration > 1 else ''}"
                    if e.text == duration_text:  # already in correct duration
                        continue

                    e.click()
                    _select_option(duration_text)
                case 'Only Show Available' | 'All times' | 'Morning' | 'Afternoon' | 'Evening':
                    # show only available times to speed session up
                    target_text = 'Only Show Available'
                    if e.text == target_text:
                        continue

                    e.click()
                    _select_option(target_text)
                case _:
                    continue

    def _select_date(self, date: pd.Timestamp):
        date_text = date.strftime('%b %#d')
        for e in self._driver.find_elements(By.CSS_SELECTOR, 'div.date.ng-binding'):  # type: WebElement
            if e.text == date_text:
                print(f"Switching to date: {date_text}")
                e.click()
                self._check_load_okay()
                break
        else:
            raise RuntimeError(f"Could not find date {date:%Y-%m-%d} in Tennis loading page")

    def _check_load_okay(self):
        self._check_element((By.CSS_SELECTOR, 'div.container.slick-initialized.slick-slider'), "Could not load schedule table", 5)

    @staticmethod
    def _wait(till: str):
        import time

        hour, minute, second = map(int, till.split(':'))
        now = pd.Timestamp.now()
        # gets the next opening time for booking
        if now.hour >= hour and now.minute >= minute and now.second >= second and now.microsecond > 0:
            sleep_till_time = (now.floor('d') + pd.offsets.Day(1)).replace(hour=hour, minute=minute, second=second)
        else:
            sleep_till_time = now.floor('d').replace(hour=hour, minute=minute, second=second)

        while now < sleep_till_time:
            # sleep till opening time, we are conservative in that we sleep slightly more
            sleep_duration = np.ceil((sleep_till_time - now).total_seconds())
            print(f"Sleeping for {sleep_duration} seconds")
            time.sleep(sleep_duration)
            now = pd.Timestamp.now()

    def _refresh_selections(self, date: pd.Timestamp):
        self._select_date(date - pd.offsets.Day(1))
        self._select_date(date)

    def _reserve_time(self, time: int):
        if time < 12:
            time_text = f'{time}:00 AM'
        elif time == 12:
            time_text = '12:00 PM'
        else:
            time_text = f'{time % 12}:00 PM'

        # searches the time boxes which upon selection brings us to the booking page
        elements = [e for e in self._driver.find_elements(By.CSS_SELECTOR, 'div.start-time.ng-binding.ng-scope') if e.text == time_text]

        if len(elements) == 0:  # no matching timings, continue
            return False

        for e in elements:
            try:
                e.click()  # clicks on the time box and enter the booking page
                book_now_css = 'a.btn.btn-primary.ng-binding'
                self._check_element((By.CSS_SELECTOR, book_now_css), "Could not find 'Book Now' button, this is CRITICAL")

                # book the court
                book_now_button: WebElement = self._driver.find_element(By.CSS_SELECTOR, book_now_css)
                book_now_button.click()
                self._check_element((By.CSS_SELECTOR, 'h1.banner-title.ng-scope'), "Could not locate success banner! THIS IS CRITICAL TOO")

                # if success, return straight-away
                return True
            except:
                # on error move to next element
                pass

        return False

    def _check_element(self,
                       locator: tuple[str, str],
                       err_post_message='',
                       wait=1):
        try:
            assert wait > 0, "wait must be a positive number"
            element_present = ec.presence_of_element_located(locator)
            WebDriverWait(self._driver, wait).until(element_present)
        except TimeoutException as e:
            if not (err_post_message := err_post_message.strip()):
                raise e
            raise TimeoutException(f"{e.msg}\n{err_post_message}", screen=e.screen, stacktrace=e.stacktrace)
