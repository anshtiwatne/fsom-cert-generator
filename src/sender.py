#!/usr/bin/env python3
# pylint: disable=import-error, redefined-outer-name

import smtplib
import ssl
import tomllib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SRC = Path("src")
OUT = Path("out")

with open(SRC / "config.toml", "rb") as f:
	email_config = tomllib.load(f)["email"]


def send_email(server: smtplib.SMTP_SSL, recipient: str, body: str, attachment: Path):
	"""Send an email with the certificate attached."""

	msg = MIMEMultipart()
	msg["Subject"] = email_config["subject"]
	msg["From"] = email_config["sender"]
	msg["To"] = recipient
	msg.attach(MIMEText(body, "plain"))

	with open(attachment, "rb") as f:
		msg.attach(MIMEApplication(f.read(), Name=attachment.name))

	server.send_message(msg, email_config["sender"], recipient)


def send_certificates():
	"""Send certificates to all recipients."""

	context = ssl.create_default_context()
	with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
		server.login(email_config["sender"], email_config["password"])

		for folder in OUT.iterdir():
			if not folder.is_dir():
				continue

			email_file = folder / "email.txt"
			certificate_file = folder / "fsom-certificate.png"

			if not email_file.exists() or not certificate_file.exists():
				continue
			
			with open(email_file, "r", encoding="UTF-8") as f:
				body = f.read()

			recipient = folder.name
			send_email(server, recipient, body, certificate_file)


if __name__ == "__main__":
	send_certificates()
