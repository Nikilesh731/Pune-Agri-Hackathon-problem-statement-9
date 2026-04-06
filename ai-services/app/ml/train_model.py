#!/usr/bin/env python3
"""
Random Forest Model Training for Agricultural Document Processing
Trains RandomForestClassifier on extracted features for risk assessment
"""

import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from typing import Dict, Any, List, Tuple
import os
import json

from app.ml.feature_extractor import FeatureExtractor

class RandomForestModel:
    """Random Forest classifier for document risk assessment"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), 'model.pkl')
        self.feature_extractor = FeatureExtractor()
        self.model = None
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        
        # Try to load existing model
        self.load_model()
    
    def create_training_data(self) -> Tuple[List[List[float]], List[str]]:
        """
        Create synthetic training data based on realistic scenarios
        
        Returns:
            Tuple of (features, labels) for training
        """
        print("[ML] Creating synthetic training data...")
        
        training_samples = []
        
        # Low risk samples (complete data, high confidence)
        for i in range(50):
            sample = {
                'extracted_data': {
                    'document_type': np.random.choice(['scheme_application', 'subsidy_claim']),
                    'confidence': np.random.uniform(0.8, 1.0),
                    'missing_fields': [],
                    'risk_flags': [],
                    'canonical': {
                        'applicant': {
                            'name': f'Farmer {i}',
                            'aadhaar_number': '123456789012',
                            'mobile_number': '9876543210'
                        },
                        'agriculture': {
                            'land_size': '5 acres'
                        },
                        'request': {
                            'requested_amount': '50000'
                        }
                    }
                },
                'risk_level': 'low'
            }
            training_samples.append(sample)
        
        # Medium risk samples (some missing fields, medium confidence)
        for i in range(40):
            sample = {
                'extracted_data': {
                    'document_type': np.random.choice(['insurance_claim', 'farmer_record']),
                    'confidence': np.random.uniform(0.5, 0.8),
                    'missing_fields': np.random.choice(['land_size', 'crop_name'], size=np.random.randint(0, 2)).tolist(),
                    'risk_flags': ['medium_confidence'],
                    'canonical': {
                        'applicant': {
                            'name': f'Farmer {i}',
                            'aadhaar_number': '123456789012' if i % 2 == 0 else '',
                            'mobile_number': '9876543210' if i % 3 == 0 else ''
                        },
                        'agriculture': {
                            'land_size': '3 acres' if i % 2 == 0 else ''
                        },
                        'request': {
                            'requested_amount': '75000' if i % 3 == 0 else ''
                        }
                    }
                },
                'risk_level': 'medium'
            }
            training_samples.append(sample)
        
        # High risk samples (many missing fields, low confidence)
        for i in range(30):
            sample = {
                'extracted_data': {
                    'document_type': np.random.choice(['grievance', 'supporting_document']),
                    'confidence': np.random.uniform(0.1, 0.5),
                    'missing_fields': np.random.choice(['name', 'aadhaar_number', 'mobile_number', 'land_size'], size=np.random.randint(2, 4)).tolist(),
                    'risk_flags': ['low_confidence', 'missing_critical_fields'],
                    'canonical': {
                        'applicant': {
                            'name': f'Farmer {i}' if i % 3 == 0 else '',
                            'aadhaar_number': '',
                            'mobile_number': ''
                        },
                        'agriculture': {
                            'land_size': ''
                        },
                        'request': {
                            'requested_amount': ''
                        }
                    }
                },
                'risk_level': 'high'
            }
            training_samples.append(sample)
        
        # Extract features and labels
        features, labels = self.feature_extractor.get_training_data_from_samples(training_samples)
        
        print(f"[ML] Created {len(features)} training samples")
        print(f"[ML] Risk distribution - Low: {labels.count('low')}, Medium: {labels.count('medium')}, High: {labels.count('high')}")
        
        return features, labels
    
    def train(self, features: List[List[float]] = None, labels: List[str] = None) -> Dict[str, Any]:
        """
        Train the Random Forest model
        
        Args:
            features: Training features (optional, will generate if None)
            labels: Training labels (optional, will generate if None)
            
        Returns:
            Training metrics
        """
        print("[ML] Training Random Forest model...")
        
        # Create training data if not provided
        if features is None or labels is None:
            features, labels = self.create_training_data()
        
        # Convert to numpy arrays
        X = np.array(features)
        y = np.array(labels)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Split data for validation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Create and train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Decode predictions for report
        y_test_decoded = self.label_encoder.inverse_transform(y_test)
        y_pred_decoded = self.label_encoder.inverse_transform(y_pred)
        
        report = classification_report(y_test_decoded, y_pred_decoded, output_dict=True)
        
        print(f"[ML] Training completed - Accuracy: {accuracy:.3f}")
        print(f"[ML] Feature importance: {dict(zip(self.feature_extractor.get_feature_names(), self.model.feature_importances_))}")
        
        self.is_trained = True
        
        # Save model
        self.save_model()
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'feature_importance': dict(zip(self.feature_extractor.get_feature_names(), self.model.feature_importances_)),
            'n_samples': len(features),
            'n_features': len(features[0]) if features else 0
        }
    
    def predict(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make prediction on extracted data
        
        Args:
            extracted_data: Dictionary containing extraction results
            
        Returns:
            Prediction results with risk level and decision
        """
        if not self.is_trained or self.model is None:
            print("[ML] Model not trained, using default prediction")
            return self._default_prediction(extracted_data)
        
        try:
            # Extract features
            features = self.feature_extractor.extract_features(extracted_data)
            X = np.array([features])
            
            # Make prediction
            prediction_encoded = self.model.predict(X)[0]
            prediction_proba = self.model.predict_proba(X)[0]
            
            # Decode prediction
            risk_level = self.label_encoder.inverse_transform([prediction_encoded])[0]
            confidence = max(prediction_proba)
            
            # Determine auto decision based on risk level and confidence
            auto_decision = self._determine_decision(risk_level, confidence)
            
            print(f"[ML] Prediction - Risk: {risk_level}, Confidence: {confidence:.3f}, Decision: {auto_decision}")
            
            return {
                'risk_level': risk_level,
                'auto_decision': auto_decision,
                'confidence_score': float(confidence),
                'features_used': self.feature_extractor.get_feature_names(),
                'feature_values': features
            }
            
        except Exception as e:
            print(f"[ML] Prediction error: {e}")
            return self._default_prediction(extracted_data)
    
    def _determine_decision(self, risk_level: str, confidence: float) -> str:
        """Determine automatic decision based on risk level and confidence"""
        if risk_level == 'low' and confidence > 0.7:
            return 'approve'
        elif risk_level == 'high' or confidence < 0.5:
            return 'manual_review'
        else:
            return 'manual_review'
    
    def _default_prediction(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide default prediction when model is not available"""
        # Simple rule-based fallback
        missing_count = len(extracted_data.get('missing_fields', []))
        confidence = extracted_data.get('confidence', 0.5)
        
        if missing_count == 0 and confidence > 0.8:
            risk_level = 'low'
            auto_decision = 'approve'
        elif missing_count > 2 or confidence < 0.5:
            risk_level = 'high'
            auto_decision = 'manual_review'
        else:
            risk_level = 'medium'
            auto_decision = 'manual_review'
        
        return {
            'risk_level': risk_level,
            'auto_decision': auto_decision,
            'confidence_score': confidence,
            'features_used': self.feature_extractor.get_feature_names(),
            'feature_values': [0.0] * len(self.feature_extractor.get_feature_names()),
            'fallback_used': True
        }
    
    def save_model(self):
        """Save the trained model to disk"""
        if self.model is None:
            print("[ML] No model to save")
            return
        
        model_data = {
            'model': self.model,
            'label_encoder': self.label_encoder,
            'feature_names': self.feature_extractor.get_feature_names(),
            'is_trained': self.is_trained,
            'training_date': str(np.datetime64('now'))
        }
        
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"[ML] Model saved to {self.model_path}")
        except Exception as e:
            print(f"[ML] Error saving model: {e}")
    
    def load_model(self) -> bool:
        """Load trained model from disk"""
        if not os.path.exists(self.model_path):
            print("[ML] No saved model found")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.label_encoder = model_data['label_encoder']
            self.is_trained = model_data.get('is_trained', False)
            
            print(f"[ML] Model loaded from {self.model_path}")
            print(f"[ML] Model trained on: {model_data.get('training_date', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"[ML] Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if not self.is_trained or self.model is None:
            return {
                'is_trained': False,
                'model_path': self.model_path,
                'message': 'Model not trained yet'
            }
        
        return {
            'is_trained': True,
            'model_path': self.model_path,
            'n_features': len(self.feature_extractor.get_feature_names()),
            'feature_names': self.feature_extractor.get_feature_names(),
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth,
            'classes': list(self.label_encoder.classes_)
        }

# Global model instance
_model_instance = None

def get_model() -> RandomForestModel:
    """Get or create global model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = RandomForestModel()
    return _model_instance

def train_and_save_model() -> Dict[str, Any]:
    """Train and save the model (convenience function)"""
    model = get_model()
    return model.train()

def predict_risk(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Make prediction on extracted data (convenience function)"""
    model = get_model()
    return model.predict(extracted_data)

if __name__ == "__main__":
    # Train model when run directly
    print("Training Random Forest model...")
    metrics = train_and_save_model()
    print(f"Training completed: {metrics}")
