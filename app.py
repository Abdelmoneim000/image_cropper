# -*- coding: utf-8 -*-
"""Copy of Crop_CLIP.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1egkUyXz5GUVUKwNEZFyVmUuzwMpvYbkp
"""


#@title import
import glob
import pprint as pp
import time
from urllib.parse import parse_qs, urlparse
import clip
import numpy as np
import requests
import torch
from PIL import Image
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import os
from io import BytesIO

#@title Create Flask app
app = Flask(__name__)

#@title ADD CORS
CORS(app)

#@title Module initialization
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, preprocess = clip.load("ViT-B/32", device=device)
yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

#@title Process image files
def process_image(url):
    response = requests.get(url)
    img1 = Image.open(BytesIO(response.content)).convert("RGB")
    return img1

#@title Crop image
def crop_image(img):
    results = yolo_model(img)
    dirpath = tempfile.mkdtemp()
    results.crop(save_dir=dirpath)
    path = os.path.join(dirpath, 'crops', '**', '*.jpg')

    cropped_images = []
    for file in glob.glob(path, recursive=True):
        cropped_images.append(Image.open(file).convert('RGB'))

    return cropped_images

#@title Get similar image
def get_similar_image(cropped_images, search_query):
    images = torch.stack([preprocess(im) for im in cropped_images]).to(device)
    with torch.no_grad():
        image_features = clip_model.encode_image(images)
        image_features /= image_features.norm(dim=-1, keepdim=True)

    with torch.no_grad():
        text_encoded = clip_model.encode_text(clip.tokenize(search_query).to(device))
        text_encoded /= text_encoded.norm(dim=-1, keepdim=True)

    similarity = text_encoded.cpu().numpy() @ image_features.cpu().numpy().T
    similarity = similarity[0]
    scores, top_images = similarity_top(similarity, cropped_images, N=1)

    return top_images[0]

#@title Get the top N similar images
def similarity_top(similarity_list, image_list, N):
    results = zip(range(len(similarity_list)), similarity_list)
    results = sorted(results, key=lambda x: x[1], reverse=True)
    top_images = []
    scores = []
    for index, score in results[:N]:
        scores.append(score)
        top_images.append(image_list[index])
    return scores, top_images

#@title Import the necessary library for search
from re import search


#@title Adding routes to the app
@app.route('/crop', methods=['POST'])
def crop():
    data = request.get_json()
    url = data.get('url')
    search_query = data.get('query', 'jack daniels')
    # print necessary data of the request to make sure the request is received
    print(url, search_query)
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        img = process_image(url)
        cropped_images = crop_image(img)

        if not cropped_images:
            return jsonify({'error': 'No images were cropped'}), 500

        similar_image = get_similar_image(cropped_images, search_query)

        buffer = BytesIO()
        similar_image.save(buffer, format="JPEG")
        buffer.seek(0)

        return send_file(buffer, mimetype='image/jpeg'), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#@title Run app
@app.route('/')
def heme():
    return "hello world"

if __name__ == '__main__':
    app.run()
