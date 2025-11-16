from flask import Flask, request, jsonify
from docx import Document
import subprocess
import os
import logging

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
            try:
                doc = Document(temp_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                logger.info(f"Successfully extracted text from .docx file")
            except Exception as e:
                logger.error(f"Error reading .docx: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Could not read .docx file: {str(e)}'
                }), 500
        
        elif filename.endswith('.doc'):
            # Для .doc используем antiword (линукс команда)
            try:
                result = subprocess.run(
                    ['antiword', temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    logger.error(f"antiword failed: {result.stderr}")
                    return jsonify({
                        'status': 'error',
                        'message': f'antiword failed: {result.stderr}'
                    }), 500
                text = result.stdout
                logger.info(f"Successfully extracted text from .doc file using antiword")
            except FileNotFoundError:
                logger.error("antiword command not found")
                return jsonify({
                    'status': 'error',
                    'message': 'antiword not installed on system'
                }), 500
            except subprocess.TimeoutExpired:
                logger.error("antiword timeout")
                return jsonify({
                    'status': 'error',
                    'message': 'File processing timeout'
                }), 500
            except Exception as e:
                logger.error(f"antiword error: {str(e)}")
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
            'text': text,
            'file_type': 'docx' if filename.endswith('.docx') else 'doc'
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
