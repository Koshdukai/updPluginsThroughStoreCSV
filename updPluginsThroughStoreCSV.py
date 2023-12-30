import os
import requests
import pandas as pd
from zipfile import ZipFile
import chardet
import shutil
import tempfile
from datetime import datetime

# URL of the CSV file
store_url = 'https://www.fullbucket.de/music/'
# this is the variable to change if you want to keep updated any of these plugin sources instead:
#url = 'http://getdunne.net/Krakli/'
#url = 'http://getdunne.net/GyL/'
#The above sources came from https://github.com/sdunnemucklow/VSTManager

# Function to sanitize file name
def sanitize_filename(filename):
	invalid_chars = r'<>"?*\|'
	for char in invalid_chars:
		filename = filename.replace(char, '_')
	invalid_chars = r':/\\'
	for char in invalid_chars:
		filename = filename.replace(char, '-')
	return filename

# Function to detect file encoding
def detect_encoding(file_path):
	with open(file_path, 'rb') as f:
		result = chardet.detect(f.read())
	return result['encoding']

csv_url = f"{store_url}store.csv"
print(f"\nUsing {csv_url}\n")
# Download CSV file
response = requests.get(csv_url)
with open('store.csv', 'wb') as csv_file:
	csv_file.write(response.content)

# Detect encoding of the CSV file
csv_encoding = detect_encoding('store.csv')

# Read CSV file using pandas with detected encoding and error handling
with open('store.csv', 'r', encoding=csv_encoding, errors='replace') as file:
	df = pd.read_csv(file)

# Iterate through rows
for index, row in df.iterrows():
	plugin = sanitize_filename(row['name'])
	url = row['url']
	plugin_version = row['folder']  # Get the name of the sub-folder within the ZIP
	#Clean up the description
	description = sanitize_filename(row['desc']).replace(' Simulation', '').replace('Korg', 'KORG')
	
	#Customize some of the descriptions for nicer sub-folder names
	if plugin == "Bucket Pops":
		description = description.replace('Rhythm Machine', 'KORG Mini Pops-7 Rhythm Machine (1966)')
	plugin_folder = f"{description} = {plugin}"

	# Create sub-folder if not exists
	subfolder_path = os.path.join(os.getcwd(), plugin_folder)

	version_file_path = os.path.join(subfolder_path, f"LastVersion={plugin_version}.txt")
	# Check if version file already exists
	if os.path.exists(version_file_path):
		print(f"{plugin_folder}: Up-to-date with version {plugin_version}")
		continue  # Skip to the next iteration

	os.makedirs(subfolder_path, exist_ok=True)
	# Create a version file with the current date and time
	current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	with open(version_file_path, 'w') as version_file:
		version_file.write(f"Version information for {plugin_version}\nCreated on: {current_datetime}")
	#this file will help skipping download if the latest is already the one we have ;)

	# Download and save the zip content to a temporary file
	with requests.get(url, stream=True) as response:
		with tempfile.NamedTemporaryFile(delete=False) as temp_zip:
			temp_zip.write(response.content)

	# Extract zip file
	print(subfolder_path)
	with ZipFile(temp_zip.name, 'r') as zip_ref:
		# Get the list of extracted files and directories
		zip_contents = zip_ref.namelist()

		# Identify the common path prefix
		common_prefix = os.path.commonprefix(zip_contents)

		# Move everything inside the common prefix to subfolder_path
		for item in zip_contents:
			item_path = os.path.join(subfolder_path, item[len(common_prefix):])
			if item.endswith('/'):	# If it's a directory, create it
				os.makedirs(item_path, exist_ok=True)
			else:
				with zip_ref.open(item) as source, open(item_path, 'wb') as dest:
					shutil.copyfileobj(source, dest)

	# Clean up: remove the temporary zip file
	os.remove(temp_zip.name)

# Clean up: remove the downloaded CSV file
os.remove('store.csv')

print("\nDownload and extraction completed successfully.\n")
