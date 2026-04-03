import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle

class ChurnPredictor:
    """Class to train and predict customer churn using Random Forest."""
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        
    def generate_training_data(self, n_samples=1000):
        """Generates mock training data with features related to churn."""
        np.random.seed(42)
        # Features: tenure_days, log_frequency, total_spend, customer_support_calls
        tenure = np.random.randint(1, 365, n_samples)
        freq = np.random.randint(1, 30, n_samples)
        spend = tenure * freq * np.random.uniform(0.5, 2.0, n_samples)
        support_calls = np.random.randint(0, 10, n_samples)
        
        # Target: 1 if churned, 0 otherwise (Higher support calls and low freq = high churn)
        # Probabilistic logic for mock target
        prob = (support_calls * 0.1) + (1 / (freq + 1) * 0.5) - (tenure * 0.0001)
        churn = (prob + np.random.normal(0, 0.1, n_samples) > 0.5).astype(int)
        
        df = pd.DataFrame({
            "tenure": tenure,
            "frequency": freq,
            "total_spend": spend,
            "support_calls": support_calls,
            "churn": churn
        })
        return df

    def train(self):
        """Trains the Random Forest model."""
        data = self.generate_training_data()
        X = data.drop("churn", axis=1)
        y = data["churn"]
        
        self.model.fit(X, y)
        self.is_trained = True
        return self.model.score(X, y)

    def predict_churn(self, features_df):
        """Predicts churn probability for given user features."""
        if not self.is_trained:
            self.train()
        
        # features_df expects: tenure, frequency, total_spend, support_calls
        probs = self.model.predict_proba(features_df)
        # Returning probability of class 1 (churn)
        return probs[:, 1]
