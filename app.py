from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
from transformers import pipeline
import torch

app = Flask(__name__)

# Configuración del dispositivo
device = 0 if torch.cuda.is_available() else -1


###########################
#### CREAR Singletons
###########################

def model_translator_es_en():
    return pipeline("translation", model="Helsinki-NLP/opus-mt-es-en", device=device)


def model_translator_en_es():
    return pipeline("translation", model="Helsinki-NLP/opus-mt-en-es", device=device)


def model_corrector():
    return pipeline('text2text-generation', model='facebook/bart-large', device=device)


# Inicialización de modelos
translator_es_en = model_translator_es_en()
translator_en_es = model_translator_en_es()
corrector = model_corrector()


###########################
#### MODELOS DE DATOS
###########################

class TextRequest(BaseModel):
    text: str


class TextResponse(BaseModel):
    corrected_text: str


@app.route("/correct", methods=["POST"])
def correct_text():
    try:
        # Validar y parsear el JSON de la solicitud
        data = TextRequest(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    input_text = data.text

    # Traducir el texto al inglés
    prompt_en = translator_es_en(input_text)[0]['translation_text']

    # Usar el modelo para corregir el texto en inglés
    prompt = f"{prompt_en}"
    corrected_text_en = corrector(prompt, max_length=512, num_return_sequences=1)[0]['generated_text']

    # Traducir el texto corregido de vuelta al español
    corrected_text_es = translator_en_es(corrected_text_en)[0]['translation_text']

    response = TextResponse(corrected_text=corrected_text_es)

    return jsonify(response.dict())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
