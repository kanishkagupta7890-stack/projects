from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.components.model_trainer import ModelTrainer

class TrainPipeline:
    def __init__(self):
        self.data_ingestion = DataIngestion()
        self.data_transformation = DataTransformation()
        self.model_trainer = ModelTrainer()
    
    def run_pipeline(self):
        try:
            # Data Ingestion
            train_path, test_path = self.data_ingestion.initiate_data_ingestion()
            
            # Data Transformation
            train_array, test_array, _ = self.data_transformation.initiate_data_transformation(train_path, test_path)
            
            # Model Training
            r2_score = self.model_trainer.initate_model_trainer(train_array, test_array)
            
            print(f"Model training completed with R2 score: {r2_score}")
            return r2_score
            
        except Exception as e:
            raise e

if __name__ == "__main__":
    train_pipeline = TrainPipeline()
    train_pipeline.run_pipeline()

