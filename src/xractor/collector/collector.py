from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class Collector:
    def __init__(self, headless=True, fast_load=False):
        """
        Initializes a Selenium web instance with customizable options.

        Args:
            headless (bool): If True, runs the browser in headless mode.
            fast_load (bool): If True, sets the page load strategy to 'eager'.
        """
        self.options = Options()

        # Configure options for a headless browser if specified
        if headless:
            self.options.add_argument('--no-sandbox')
            self.options.add_argument('--headless=new')
            self.options.add_argument('--disable-dev-shm-usage')

        # Configure options for faster page loads if specified
        if fast_load:
            self.options.page_load_strategy = 'eager'

    def get_driver(self):
        """
        Creates and returns a Selenium WebDriver instance with configured options.

        Returns:
            webdriver.Chrome: A configured Chrome WebDriver instance.
        """
        # Install ChromeDriver if not already installed and create a WebDriver instance
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        return driver
