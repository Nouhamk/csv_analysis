from flask import Blueprint, request, jsonify
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

csv_routes = Blueprint('csv_routes', __name__)

@csv_routes.route('/upload-csv', methods=['POST'])
def upload_csv():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier envoyé'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400

        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Seuls les fichiers CSV sont autorisés'}), 400

        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        container_name = os.getenv('CONTAINER_NAME', 'csv-import')
        email = request.form.get('email')

        if not connect_str:
            return jsonify({'error': 'La configuration Azure Blob Storage est manquante'}), 500

        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_client = blob_service_client.get_container_client(container_name)

        if not container_client.exists():
            container_client.create_container()

        blob_name = f"{file.filename}"
        blob_client = container_client.get_blob_client(blob_name)

        blob_client.upload_blob(
            file.read(),
            overwrite=True,
            metadata={'user_email': email}
        )

        return jsonify({
            'message': 'Fichier CSV uploadé avec succès',
            'filename': file.filename,
            'email': email,
            'container': container_name
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de l\'upload : {str(e)}',
        }), 500

@csv_routes.route('/get-analysis', methods=['GET'])
def get_analysis():
    try:
        connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        client = MongoClient(connection_string)

        db = client['csvdata']
        collection = db['csvdata']

        analyses = list(collection.find().sort('timestamp', -1).limit(10))

        for analysis in analyses:
            analysis['_id'] = str(analysis['_id'])

        client.close()

        return jsonify(analyses), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@csv_routes.route('/latest-analysis', methods=['GET'])
def get_latest():
    try:
        connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        client = MongoClient(connection_string)

        db = client['csvdata']
        collection = db['csvdata']

        latest = collection.find_one(sort=[('timestamp', -1)])

        latest['_id'] = str(latest['_id'])

        client.close()

        return jsonify(latest), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500