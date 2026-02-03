import os
import sys
import numpy as np
import pandas as pd
from dataclasses import dataclass
from src.exception import CustomException
from src.logger import logging
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from catboost import CatBoostRegressor
from xgboost import XGBRegressor

@dataclass
class ModelTrainerConfig:
    trained_model_file_path = os.path.join("artifacts", "model.pkl")

class ModelTrainer:
    def __init__(self):
        self.model_trainer_config = ModelTrainerConfig()
    
    def initate_model_trainer(self, train_array, test_array):
        try:
            logging.info("Splitting training and test input data")
            X_train, y_train, X_test, y_test = (
                train_array[:, :-1],
                train_array[:, -1],
                test_array[:, :-1],
                test_array[:, -1]
            )
            
            models = {
                "Linear Regression": LinearRegression(),
                "Lasso": Lasso(),
                "Ridge": Ridge(),
                "K-Neighbors Regressor": KNeighborsRegressor(),
                "Decision Tree": DecisionTreeRegressor(),
                "Random Forest Regressor": RandomForestRegressor(),
                "XGBRegressor": XGBRegressor(), 
                "CatBoosting Regressor": CatBoostRegressor(verbose=False),
                "AdaBoost Regressor": AdaBoostRegressor()
            }
            
            model_report: dict = self.evaluate_models(X_train, y_train, X_test, y_test, models)
            print(model_report)
            logging.info(f"Model Report: {model_report}")
            
            # Get best model score
            best_model_score = max(sorted(model_report.values()))
            best_model_name = list(model_report.keys())[
                list(model_report.values()).index(best_model_score)
            ]
            best_model = models[best_model_name]
            
            if best_model_score < 0.6:
                raise CustomException("No best model found")
            logging.info(f"Best found model on both training and testing dataset is {best_model_name}")
            
            # Train model on full training data
            best_model.fit(X_train, y_train)
            
            # Save the model
            import pickle
            with open(self.model_trainer_config.trained_model_file_path, 'wb') as f:
                pickle.dump(best_model, f)
            
            predicted = best_model.predict(X_test)
            r2_square = r2_score(y_test, predicted)
            return r2_square
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def evaluate_models(self, X_train, y_train, X_test, y_test, models):
        try:
            report = {}
            
            for i in range(len(list(models))):
                model = list(models.values())[i]
                model.fit(X_train, y_train)  # Train model
                
                # Make predictions
                y_train_pred = model.predict(X_train)
                y_test_pred = model.predict(X_test)
                
                # Evaluate Train and Test dataset
                model_train_mae, model_train_rmse, model_train_r2 = self.evaluate_model(y_train, y_train_pred)
                model_test_mae, model_test_rmse, model_test_r2 = self.evaluate_model(y_test, y_test_pred)
                
                report[list(models.keys())[i]] = model_test_r2
                
            return report
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def evaluate_model(self, true, predicted):
        try:
            mae = mean_absolute_error(true, predicted)
            mse = mean_squared_error(true, predicted)
            rmse = np.sqrt(mean_squared_error(true, predicted))
            r2_square = r2_score(true, predicted)
            return mae, rmse, r2_square
        except Exception as e:
            raise CustomException(e, sys)

