import os
import sys
import pickle
import pandas as pd
import logging

from src.exception import CustomException

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)


class PredictPipeline:
    def __init__(self):
        # Get project root (two levels up from src/pipeline/)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.model_path = os.path.join(project_root, 'artifacts', 'model.pkl')
        self.preprocessor_path = os.path.join(project_root, 'artifacts', 'preprocessor.pkl')
        
        # Load model and preprocessor
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(self.preprocessor_path, 'rb') as f:
            self.preprocessor = pickle.load(f)
        
        logging.info("Model and preprocessor loaded successfully")
    
    def predict(self, features):
        """Make prediction using the model"""
        try:
            logging.info("Making prediction")
            
            # Transform features using preprocessor
            X = self.preprocessor.transform(features)
            
            # Make prediction
            prediction = self.model.predict(X)[0]
            
            logging.info(f"Prediction: {prediction}")
            return prediction
        except Exception as e:
            logging.error(f"Error in prediction: {e}")
            raise CustomException(e, sys)


def predict_features(gender, ethnicity, parental_level_of_education, lunch, 
                     test_preparation_course, reading_score, writing_score):
    """Create a dataframe from input features"""
    data = {
        'gender': [gender],
        'race/ethnicity': [ethnicity],
        'parental level of education': [parental_level_of_education],
        'lunch': [lunch],
        'test preparation course': [test_preparation_course],
        'reading score': [reading_score],
        'writing score': [writing_score]
    }
    
    df = pd.DataFrame(data)
    return df


if __name__ == "__main__":
    # Test the pipeline
    pipeline = PredictPipeline()
    
    test_data = predict_features(
        gender='male',
        ethnicity='group A',
        parental_level_of_education='high school',
        lunch='standard',
        test_preparation_course='none',
        reading_score=70,
        writing_score=75
    )
    
    prediction = pipeline.predict(test_data)
    print(f"Predicted Math Score: {prediction}")

