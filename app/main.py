#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import json
import os
import uuid
import wave

import numpy as np
from flask import Flask, make_response, jsonify, request, Response
from pydub import AudioSegment

from vosk import Model, KaldiRecognizer, SpkModel

model_path = "model"
smodel_path = "smodel"

app = Flask(__name__)


def cosine_dist(x, y):
    nx = np.array(x)
    ny = np.array(y)
    score = np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)
    return score


# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = {'wav'}
app.config['ALLOWED_ACTION_TYPES'] = {'smile', 'blink'}


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/v1/pattern/extract', methods=['POST'])
def extract():
    # if request.files[''].content_type == 'audio/pcm':
    if request.content_type != 'audio/pcm':
        return jsonify(code='BPE-002001', message='Неверный Content-Type HTTP-запроса'), 400
    # file = request.files['']
    filename = 'audio_' + str(uuid.uuid4()) + '.wav'
    file = AudioSegment.from_file(io.BytesIO(request.get_data()), format="wav").export(filename, format='wav')

    if file and allowed_file(file.name):
        # if file and allowed_file(file.filename):
        #     wf = wave.open(file, "rb")

        wf = wave.open(filename, "rb")

        rec = KaldiRecognizer(model, smodel, wf.getframerate())
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)
        try:
            res = json.loads(rec.FinalResult())
            os.remove(filename)
            return Response(bytes(" ".join(str(x) for x in res["spk"]), encoding='utf8'),
                            mimetype='application/octet-stream'), 200
        except KeyError:
            os.remove(filename)
            return jsonify(code='BPE-002003', message='Не удалось прочитать биометрический образец'), 400
    else:
        os.remove(filename)
        return jsonify(code='BPE-002003', message='Не удалось прочитать биометрический образец'), 400


@app.route('/v1/pattern/compare', methods=['POST'])
def compare():
    # if request.files['bio_feature'].content_type == 'application/octet-stream' and request.files['bio_template'].content_type == 'application/octet-stream':
    if request.mimetype != 'multipart/form-data':
        return jsonify(code='BPE-002001', message='Неверный Content-Type HTTP-запроса'), 400
    try:
        # bio_feature_data = request.files['bio_feature'].stream.read()
        # bio_template_data = request.files['bio_template'].stream.read()
        bio_feature_data = request.form['bio_feature']
        bio_template_data = request.form['bio_template']

        # bio_feature = [float(x) for x in bio_feature_data.decode("utf-8").split()]
        # bio_template = [float(y) for y in bio_template_data.decode("utf-8").split()]
        bio_feature = [float(x) for x in bio_feature_data.split()]
        bio_template = [float(y) for y in bio_template_data.split()]

        result = cosine_dist(bio_template, bio_feature)
        return jsonify(score=result), 200
    except KeyError:
        return jsonify(code='BPE-002004', message='Не удалось прочитать биометрический шаблон'), 400

        return jsonify(code='BPE-002001', message='Неверный Content-Type HTTP-запроса'), 400


if __name__ == "__main__":
    model = Model(model_path)
    smodel = SpkModel(smodel_path)

    # threading.Thread(target=app.run).start()
    # Only for debugging while developing
    app.run(host="0.0.0.0", debug=True, port=5000)
