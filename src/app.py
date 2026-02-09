from flask import Flask, render_template, request, jsonify
import os
import sys
import argparse
import logging
import importlib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import prediction functions from predict_pipeline module
predict_pipeline_module = importlib.import_module('src.pipeline.predict_pipeline')
PredictPipeline = predict_pipeline_module.PredictPipeline
predict_features = predict_pipeline_module.predict_features

app = Flask(__name__)

# Set template folder explicitly
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Initialize prediction pipeline
pipeline = PredictPipeline()

logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route('/predictdata', methods=['GET', 'POST'])
def predict_datapoint():
    if request.method == 'POST':
        try:
            # Get form data
            gender = request.form.get('gender')
            ethnicity = request.form.get('ethnicity')
            parental_level_of_education = request.form.get('parental_level_of_education')
            lunch = request.form.get('lunch')
            test_preparation_course = request.form.get('test_preparation_course')
            reading_score = float(request.form.get('reading_score'))
            writing_score = float(request.form.get('writing_score'))
            
            logging.info(f"Received data: gender={gender}, ethnicity={ethnicity}, "
                        f"education={parental_level_of_education}, lunch={lunch}, "
                        f"test_course={test_preparation_course}, reading={reading_score}, "
                        f"writing={writing_score}")
            
            # Create features dataframe
            features_df = predict_features(
                gender=gender,
                ethnicity=ethnicity,
                parental_level_of_education=parental_level_of_education,
                lunch=lunch,
                test_preparation_course=test_preparation_course,
                reading_score=reading_score,
                writing_score=writing_score
            )
            
            # Make prediction
            result = pipeline.predict(features_df)
            
            logging.info(f"Prediction result: {result}")
            
            return jsonify({'prediction': round(result, 2)})
        except Exception as e:
            logging.error(f"Error during prediction: {e}")
            return jsonify({'error': str(e)}), 500
    
    return render_template('home.html', results='')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()
    
    print(f'Template folder: {app.template_folder}')
    print(f'Starting Flask app on port {args.port}...')
    app.run(host='0.0.0.0', port=args.port, debug=True)

