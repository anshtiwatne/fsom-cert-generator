#!/usr/bin/env python3
# pylint: disable=import-error, redefined-outer-name
"""Send emails with certificate attachments from the out directory."""

import smtplib
import ssl
import tomllib
from concurrent.futures import ThreadPoolExecutor
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SRC = Path("src")
OUT = Path("out")
ATTACHMENTS = Path("attachments")
CONTEXT = ssl.create_default_context()

with open(SRC / "config.toml", "rb") as f:
	email_config = tomllib.load(f)["email"]


def send_email(recipient: str, body: str, certificate: Path):
	"""Send an email with the certificate attached."""

	msg = MIMEMultipart()
	msg["Subject"] = email_config["subject"]
	msg["From"] = email_config["sender"]
	msg["To"] = recipient
	msg.attach(MIMEText(body, "html"))

	with open(certificate, "rb") as f:
		msg.attach(MIMEApplication(f.read(), Name=certificate.name))

	for attachment in ATTACHMENTS.iterdir():
		if not attachment.is_file():
			continue
		with open(attachment, "rb") as f:
			msg.attach(MIMEApplication(f.read(), Name=attachment.name))

	# SMTP is not thread-safe, so we need to create a new connection for each thread
	with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=CONTEXT) as server:
		server.login(email_config["sender"], email_config["password"])
		server.send_message(msg, email_config["sender"], recipient)


def send_cert_email(folder: Path):
	"""Send an email with the certificate attached to the recipient."""

	email_file = folder / "email.html"
	certificate_file = folder / "certificate.png"

	if not email_file.exists() or not certificate_file.exists():
		return

	with open(email_file, "r", encoding="UTF-8") as f:
		body = f.read()

	recipient = folder.name
	send_email(recipient, body, certificate_file)


def main():
	"""Send certificates to all recipients."""

	with ThreadPoolExecutor(max_workers=10) as executor:
		futures = [
			executor.submit(send_cert_email, folder)
			for folder in OUT.iterdir()
			if folder.is_dir()
		]
		for future in futures:
			future.result()


if __name__ == "__main__":
	main()
