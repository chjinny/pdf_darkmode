import subprocess
import base64
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image 
from io import BytesIO
import io
from rembg.bg import remove
import cv2
import bs4
from tqdm import tqdm
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import chromedriver_autoinstaller
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
from base64 import b64decode
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium import webdriver

def convert_pdf_to_html(pdf_path, html_path):
    subprocess.call([
        "pdf2htmlEX", 
        pdf_path,
        html_path, 
    ])

def uri_to_array(data_uri):
    encoded_image = data_uri.split(",")[1]
    decoded_image = base64.b64decode(encoded_image)

    img = Image.open(BytesIO(decoded_image)).convert('RGB')
    pixels = np.asarray(img, dtype='uint8')
    return pixels

def segment(img):
    success, data = cv2.imencode('.jpg', img)
    rm = remove(data.tobytes())
    rm = np.array(Image.open(io.BytesIO(rm)).convert("RGB"))
    rm = cv2.cvtColor(rm, cv2.COLOR_RGB2BGR)
    return rm

def array_to_uri(array):
    data = base64.b64encode(array.tobytes()).decode('utf-8')
    pil_img = Image.fromarray(array)
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
    string = f"data:image/jpeg;base64,{new_image_string}"
    # with open("./sample.txt", "w") as w:
    #     w.write(string)
    return string

def convert_to_dark(html_path):
    # background
    with open(html_path, "r") as f:
        lines = f.readlines()
    
    count = 0
    for i, line in enumerate(tqdm(lines, desc="convert text")):
        if "background-color:transparent" in line:
            lines[i] = lines[i].replace("background-color:transparent", "background-color:black")
            count += 1
        if "position:relative;background-color:white" in line:
            lines[i] = lines[i].replace("position:relative;background-color:white", "position:relative;background-color:black")
            count += 1
        if ".fc0{color:rgb(0,0,0);}" in line:
            lines[i] = lines[i].replace(".fc0{color:rgb(0,0,0);}", 
            ".fc0{color:rgb(255,255,255);text-shadow:-5px -5px 0 #000,5px -5px 0 #000,-5px 5px 0 #000,5px 5px 0 #000;  }")
        
        if count > 2:
            break

    with open(html_path, "w") as f:
        for line in lines:
            f.write(line)

    # image
    with open(html_path, "r") as f:
        soup = bs4.BeautifulSoup(f, "html.parser")
    
    for img in tqdm(soup.find_all('img'), desc="convert bg&img"):
        img_urls = img['src']
        if not "data:image/png" in img_urls:
            continue
        array = uri_to_array(img_urls)
        array = segment(array)
        url = array_to_uri(array)
        img['src'] = url
    
    with open(html_path, "w", encoding='utf-8') as file:
        file.write(str(soup))

def html_to_pdf(html_path, pdf_path):
    chromedriver_autoinstaller.install()  
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(f'file://{ os.path.abspath(html_path)}')

    a = driver.execute_cdp_cmd(
        "Page.printToPDF", {"path": pdf_path, "format": 'A4'})
    # Import only b64decode function from the base64 module

    # Define the Base64 string of the PDF file
    b64 = a['data']

    # Decode the Base64 string, making sure that it contains only valid characters
    bytes = b64decode(b64, validate=True)

    # Perform a basic validation to make sure that the result is a valid PDF file
    # Be aware! The magic number (file signature) is not 100% reliable solution to validate PDF files
    # Moreover, if you get Base64 from an untrusted source, you must sanitize the PDF contents
    if bytes[0:4] != b'%PDF':
        raise ValueError('Missing the PDF file signature')

    os.remove(html_path)

    # Write the PDF contents to a local file
    f = open(pdf_path, 'wb')
    f.write(bytes)
    f.close()

if __name__ == "__main__":
    with open("./config.json", "r") as j:
        config = json.load(j)
    input_dir = config["input_dir"]
    output_dir = config["output_dir"]
    for (path, dir, files) in os.walk(input_dir):
        for file in files:
            f_list = file.split(".")
            if len(f_list) != 2:
                continue
            file_name, ext = f_list
            if ext != "pdf":
                continue
            input_path = os.path.join(path, file)
            html_path = os.path.join(output_dir, f"{file_name}.html")
            output_path = os.path.join(output_dir, f"{file_name}.pdf")
            convert_pdf_to_html(input_path, html_path)
            convert_to_dark(html_path)
            html_to_pdf(html_path, output_path)