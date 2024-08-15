#!/usr/bin/env python3
# pylint: disable=redefined-outer-name
"""Generate certificates and emails for marathon runners form runners.csv"""

import csv
import os
import tempfile
import tomllib
from datetime import date
from pathlib import Path
from string import Template

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

SRC = Path("src")
TEMPLATES = Path("templates")

with open(SRC / "config.toml", "rb") as f:
	cert_config = tomllib.load(f)["certificate"]

with open(TEMPLATES / "certificate.svg", "r", encoding="UTF-8") as f:
	cert_template = Template(f.read())

with open(TEMPLATES / "email.html", "r", encoding="UTF-8") as f:
	email_template = Template(f.read())

with open(TEMPLATES / "selenium.html", "r", encoding="UTF-8") as f:
	html_template = Template(f.read())

with open(SRC / "runners.csv", "r", encoding="UTF-8") as f:
	runners = list(csv.DictReader(f))


cert_config.update(
	{
		"heading": cert_config["marathon"].upper(),
		"humanized_date": date.fromisoformat(cert_config["date"]).strftime(
			"%B %#d, %Y"
		),  # use %#d for Windows and %-d for Unix
		"cert_title": cert_config["title"],
		"year": date.fromisoformat(cert_config["date"]).year,
	}
)

chrome_options = Options()
chrome_options.add_argument("--headless")

prefs = {
	"download.prompt_for_download": False,
	"download.directory_upgrade": True,
}

chrome_options.add_experimental_option("prefs", prefs)
service = Service(Path("bin", "chromedriver.exe"))
driver = webdriver.Chrome(service=service, options=chrome_options)


def svg_to_png(svg_str, download_dir: Path, file_name):
	"""Convert SVG string to PNG image using headless Chrome"""

	page = html_template.substitute({"svg": svg_str, "file_name": file_name})
	driver.execute_cdp_cmd(
		"Page.setDownloadBehavior",
		{"behavior": "allow", "downloadPath": str(download_dir.absolute())},
	)

	with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
		tmp_file.write(page.encode("UTF-8"))
		tmp_file_path = tmp_file.name

	driver.get(f"file://{tmp_file_path}")
	WebDriverWait(driver, 20).until(lambda _: (download_dir / file_name).exists())
	os.remove(tmp_file_path)


def generate_certificates():
	"""Generate PDF certificates using runners.csv and template.svg"""

	for runner in runners:
		runner_dir = Path("out", runner["email"])
		runner_dir.mkdir(parents=True, exist_ok=True)

		with open(runner_dir / "email.html", "w", encoding="UTF-8") as f:
			f.write(email_template.substitute(runner | cert_config))

		runner["name"] = runner["name"].upper()
		cert = cert_template.substitute(runner | cert_config)
		svg_to_png(cert, runner_dir, "certificate.png")

	driver.quit()


if __name__ == "__main__":
	generate_certificates()
