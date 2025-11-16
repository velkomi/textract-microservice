from flask import Flask, request, jsonify
from docx import Document
import os
import logging
import subprocess

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья сервиса"""
    return jsonify({'status': 'ok', 'message': 'Microservice is running'}), 200

@app.route('/extract_text', methods=['POST'])
def extract_text():
    """
    Извлечение текста из документов (doc, docx)
    Ожидает multipart/form-data с файлом в поле 'file'
    """
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'Empty filename'}), 400
        
        temp_path = f'/tmp/{file.filename}'
        file.save(temp_path)
        logger.info(f"Processing file: {file.filename}")
        
        filename = file.filename.lower()
        text = ""
        
        if filename.endswith('.docx'):
            # Парсинг .docx через python-docx
            doc = Document(temp_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        elif filename.endswith('.doc'):
            # Для .doc используем textract
            try:
                text = textract.process(temp_path).decode('utf-8')
            except Exception as e:
                logger.error(f"Textract error: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Could not process .doc file: {str(e)}'
                }), 500
        
        else:
            return jsonify({
                'status': 'error',
                'message': 'Only .doc and .docx files are supported'
            }), 400
        
        # Удаление временного файла
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'status': 'success',
            'filename': file.filename,
            'text': text
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
