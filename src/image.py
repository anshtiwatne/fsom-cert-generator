#!/usr/bin/env python3
# pylint: skip-file

import os
from pathlib import Path
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


def svg_to_png(svg_string, download_dir: Path, file_name):
	chrome_options = Options()
	chrome_options.add_argument("--headless")

	prefs = {
		"download.default_directory": str(download_dir.absolute()),
		"download.prompt_for_download": False,
		"download.directory_upgrade": True,
		"safebrowsing.enabled": True,
	}

	chrome_options.add_experimental_option("prefs", prefs)
	service = Service(Path("bin", "chromedriver.exe"))
	driver = webdriver.Chrome(service=service, options=chrome_options)

	html_content = f"""
	<html>
	<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" integrity="sha512-BNaRQnYJYiPSqHHDb58B0yaPfCu+Wgds8Gp/gU33kqBtgNS4tSPHuGibyoeqMV/TJlSKda6FXzoEyYGjTe+vXA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
	<body>
		<div id="cert" style="display: flex; width: min-content;">{svg_string}</div>
		<canvas id="canvas"></canvas>
		<script>
			async function certDownload() {{
				const certificateRef = document.getElementById('cert')
				try {{
					if (!certificateRef) return
					const canvas = await html2canvas(certificateRef, {{
						scale: 5,
					}})
					const image = canvas.toDataURL('image/png')
					const a = document.createElement('a')

					a.href = image
					a.download = "{file_name}"
					a.click()
				}} catch (error) {{
					console.error('Error downloading the chart:', error)
				}}
			}}
			certDownload()
		</script>
	</body>
	</html>
	"""

	with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
		tmp_file.write(html_content.encode("UTF-8"))
		tmp_file_path = tmp_file.name

	driver.get(f"file://{tmp_file_path}")
	WebDriverWait(driver, 20).until(lambda _: (download_dir / file_name).exists())
	driver.quit()

	os.remove(tmp_file_path)
