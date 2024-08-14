#!/usr/bin/env python3
# pylint: skip-file

import csv
import tomllib
from string import Template
from pathlib import Path
from datetime import date
from image import svg_to_png

SRC = Path("src")
TEMPLATES = Path("templates")

with open(SRC / "config.toml", "rb") as f:
	cert_config = tomllib.load(f)

with open(TEMPLATES / "certificate.svg", "r", encoding="UTF-8") as f:
	cert_template = Template(f.read())

with open(TEMPLATES / "email.txt", "r", encoding="UTF-8") as f:
	email_template = Template(f.read())

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


def generate_certificates():
	"""Generate PDF certificates using runners.csv and template.svg"""

	for runner in runners:
		runner["name"] = runner["name"].upper()
		cert = cert_template.substitute(runner | cert_config)
		runner_dir = Path("out", runner["email"])
		svg_to_png(cert, runner_dir, "fsom-certificate.png")

		with open(runner_dir / "email.txt", "w", encoding="UTF-8") as f:
			f.write(email_template.substitute(runner | cert_config))


if __name__ == "__main__":
	generate_certificates()
