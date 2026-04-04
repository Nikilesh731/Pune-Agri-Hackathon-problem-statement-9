"""
ML Priority Layer for Agricultural Document Processing
Uses RandomForestClassifier to predict application priority and processing queue
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os
from datetime import datetime


class ApplicationPriorityModel:
    """ML model for predicting application priority and processing queue"""
    
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.label_encoders = {}
        self.feature_columns = [
            'document_type',
            'missing_fields_count',
            'extraction_confidence',
            'classification_confidence',
            'risk_flags_count',
            'has_aadhaar',
            'has_mobile',
            'has_address',
            'requested_amount_present',
            'grievance_flag',
            'insurance_flag'
        ]
        self.is_trained = False
        self.model_path = os.path.join(os.path.dirname(__file__), 'priority_model.pkl')
        
        # Try to load existing model
        self._load_model()
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            # Save both model and encoders together
            model_data = {
                'model': self.model,
                'label_encoders': self.label_encoders
            }
            joblib.dump(model_data, self.model_path)
            print(f"Saved priority model and encoders to {self.model_path}")
        except Exception as e:
            print(f"Could not save model: {e}")
    
    def _load_model(self):
        """Load trained model from disk if available"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                if isinstance(model_data, dict) and 'model' in model_data and 'label_encoders' in model_data:
                    self.model = model_data['model']
                    self.label_encoders = model_data['label_encoders']
                    self.is_trained = True
                    print(f"Loaded priority model and encoders from {self.model_path}")
                else:
                    # Legacy model loading (model only)
                    self.model = model_data
                    self.is_trained = True
                    print(f"Loaded legacy priority model from {self.model_path}")
        except Exception as e:
            print(f"Could not load model: {e}")
            self.is_trained = False
    
    def _extract_features(self, extracted_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from extracted data for ML prediction"""
        structured_data = extracted_data.get("structured_data", {})
        missing_fields = extracted_data.get("missing_fields", [])
        risk_flags = extracted_data.get("risk_flags", [])
        
        # Document type (categorical)
        document_type = extracted_data.get("document_type", "unknown")
        
        # Numeric features
        missing_fields_count = len(missing_fields)
        extraction_confidence = extracted_data.get("confidence", 0)
        classification_confidence = extracted_data.get("classification_confidence", 0)
        risk_flags_count = len(risk_flags)
        
        # Binary features
        has_aadhaar = bool(structured_data.get("aadhaar_number") or structured_data.get("aadhar"))
        has_mobile = bool(structured_data.get("mobile_number") or structured_data.get("phone"))
        has_address = bool(structured_data.get("address") or structured_data.get("village") or structured_data.get("district"))
        
        # Amount present
        amount_fields = ["amount", "claim_amount", "subsidy_amount", "loan_amount", "requested_amount"]
        requested_amount_present = any(field in structured_data for field in amount_fields)
        
        # Document type flags
        grievance_flag = document_type == "grievance"
        insurance_flag = document_type == "insurance_claim"
        
        features = np.array([[
            document_type,
            missing_fields_count,
            extraction_confidence,
            classification_confidence,
            risk_flags_count,
            int(has_aadhaar),
            int(has_mobile),
            int(has_address),
            int(requested_amount_present),
            int(grievance_flag),
            int(insurance_flag)
        ]])
        
        return features
    
    def _encode_features(self, features: np.ndarray) -> np.ndarray:
        """Encode categorical features for ML model"""
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(features, columns=self.feature_columns)
        
        # Encode document_type if not already encoded
        if 'document_type' not in self.label_encoders:
            self.label_encoders['document_type'] = LabelEncoder()
            # Fit on all possible document types
            all_types = ['scheme_application', 'subsidy_claim', 'grievance', 'insurance_claim', 'farmer_record', 'supporting_document', 'unknown']
            self.label_encoders['document_type'].fit(all_types)
        
        # Transform categorical columns
        if 'document_type' in df.columns:
            df['document_type'] = self.label_encoders['document_type'].transform(df['document_type'])
        
        return df.values.astype(float)
    
    def train_model(self, training_data: List[Dict[str, Any]]):
        """
        Train the priority model with historical data
        
        Args:
            training_data: List of historical application data with features and labels
        """
        if len(training_data) < 10:
            print("Insufficient training data. Using rule-based approach.")
            return
        
        # Prepare training data
        X = []
        y = []
        
        for data in training_data:
            extracted_data = data.get("extracted_data", {})
            features = self._extract_features(extracted_data)
            encoded_features = self._encode_features(features)
            
            # Get priority label (should be in training data)
            priority = data.get("priority", "NORMAL")  # Default to NORMAL
            
            X.append(encoded_features[0])
            y.append(priority)
        
        # Encode target variable
        if 'priority' not in self.label_encoders:
            self.label_encoders['priority'] = LabelEncoder()
        
        y_encoded = self.label_encoders['priority'].fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        print(f"Model training complete. Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
        
        self.is_trained = True
        self._save_model()
    
    def predict(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict priority and processing queue for application
        
        Args:
            extracted_data: Extracted data from document processing
            
        Returns:
            Dictionary with priority_score, queue, and review_type
        """
        if not self.is_trained:
            # Use rule-based approach if model not trained
            return self._rule_based_prediction(extracted_data)
        
        try:
            # Extract and encode features
            features = self._extract_features(extracted_data)
            encoded_features = self._encode_features(features)
            
            # Make prediction
            prediction = self.model.predict(encoded_features)[0]
            probabilities = self.model.predict_proba(encoded_features)[0]
            
            # Decode prediction with safe fallback
            try:
                if 'priority' in self.label_encoders:
                    priority = self.label_encoders['priority'].inverse_transform([prediction])[0]
                else:
                    # Fallback: map numeric prediction to priority
                    priority_mapping = {0: "LOW", 1: "NORMAL", 2: "HIGH"}
                    priority = priority_mapping.get(int(prediction), "NORMAL")
                confidence = max(probabilities)
            except Exception as decode_error:
                print(f"ML decoding failed: {decode_error}")
                return self._rule_based_prediction(extracted_data)
            
            # Map priority to queue and review type
            queue, review_type = self._map_priority_to_queue(priority, confidence)
            
            # Calculate priority score (0-1)
            priority_score = self._calculate_priority_score(extracted_data, priority, confidence)
            
            return {
                "priority_score": round(priority_score, 3),
                "queue": queue,
                "review_type": review_type,
                "model_confidence": round(confidence, 3),
                "prediction_method": "trained_random_forest" if self.is_trained else "rule_based_fallback"
            }
            
        except Exception as e:
            print(f"ML prediction failed: {e}")
            return self._rule_based_prediction(extracted_data)
    
    def _rule_based_prediction(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based prediction when ML model is not available"""
        structured_data = extracted_data.get("structured_data", {})
        missing_fields = extracted_data.get("missing_fields", [])
        risk_flags = extracted_data.get("risk_flags", [])
        confidence = extracted_data.get("confidence", 0)
        document_type = extracted_data.get("document_type", "unknown")
        
        # Calculate priority score
        priority_score = 0.5  # Base score
        
        # Adjust based on confidence
        if confidence > 0.8:
            priority_score += 0.2
        elif confidence < 0.5:
            priority_score -= 0.2
        
        # Adjust based on missing fields
        if len(missing_fields) == 0:
            priority_score += 0.1
        elif len(missing_fields) > 3:
            priority_score -= 0.2
        
        # Adjust based on risk flags
        if len(risk_flags) == 0:
            priority_score += 0.1
        elif len(risk_flags) > 2:
            priority_score -= 0.2
        
        # Document type adjustments
        if document_type == "grievance":
            priority_score += 0.3  # Grievances get higher priority
        elif document_type == "insurance_claim":
            priority_score += 0.1
        
        # Amount-based adjustments
        amount_fields = ["amount", "claim_amount", "subsidy_amount"]
        for field in amount_fields:
            if field in structured_data:
                try:
                    amount = float(str(structured_data[field]).replace(",", "").replace("₹", "").replace("$", ""))
                    if amount > 100000:
                        priority_score += 0.2
                    elif amount > 50000:
                        priority_score += 0.1
                except:
                    pass
                break
        
        # Clamp between 0 and 1
        priority_score = max(0, min(1, priority_score))
        
        # Determine queue and review type
        if priority_score > 0.7:
            queue = "HIGH_PRIORITY"
            review_type = "AUTO"
        elif priority_score > 0.4:
            queue = "NORMAL"
            review_type = "AUTO"
        else:
            queue = "LOW"
            review_type = "MANUAL_REVIEW"
        
        # Special cases for manual review
        if confidence < 0.3 or len(missing_fields) > 5 or len(risk_flags) > 3:
            review_type = "MANUAL_REVIEW"
            queue = "LOW"
        
        return {
            "priority_score": round(priority_score, 3),
            "queue": queue,
            "review_type": review_type,
            "model_confidence": 1.0,  # Rule-based confidence
            "prediction_method": "rule_based_fallback"
        }
    
    def _map_priority_to_queue(self, priority: str, confidence: float) -> tuple:
        """Map ML priority to queue and review type"""
        priority = priority.upper()
        
        if priority == "HIGH" and confidence > 0.6:
            return "HIGH_PRIORITY", "AUTO"
        elif priority == "NORMAL" or (priority == "HIGH" and confidence <= 0.6):
            return "NORMAL", "AUTO"
        else:
            return "LOW", "MANUAL_REVIEW"
    
    def _calculate_priority_score(self, extracted_data: Dict[str, Any], priority: str, confidence: float) -> float:
        """Calculate 0-1 priority score"""
        base_scores = {
            "HIGH": 0.8,
            "NORMAL": 0.5,
            "LOW": 0.2
        }
        
        base_score = base_scores.get(priority.upper(), 0.5)
        
        # Adjust by confidence
        adjusted_score = base_score * confidence + (1 - confidence) * 0.5
        
        # Additional adjustments based on data quality
        missing_fields = extracted_data.get("missing_fields", [])
        if len(missing_fields) == 0:
            adjusted_score += 0.1
        elif len(missing_fields) > 3:
            adjusted_score -= 0.1
        
        return max(0, min(1, adjusted_score))
    
    def generate_training_data(self, historical_applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate training data from historical applications
        
        Args:
            historical_applications: List of historical application records
            
        Returns:
            List of training examples with features and labels
        """
        training_data = []
        
        for app in historical_applications:
            # Extract features from application
            extracted_data = app.get("extractedData", {})
            
            # Determine priority label based on historical outcomes
            priority = self._infer_priority_from_outcome(app)
            
            training_example = {
                "extracted_data": extracted_data,
                "priority": priority
            }
            
            training_data.append(training_example)
        
        return training_data
    
    def _infer_priority_from_outcome(self, application: Dict[str, Any]) -> str:
        """
        Infer priority label from historical application outcome
        
        Args:
            application: Historical application record
            
        Returns:
            Priority label (HIGH, NORMAL, LOW)
        """
        status = application.get("status", "").upper()
        processing_time = application.get("processing_time_days", 0)
        extracted_data = application.get("extractedData", {})
        confidence = extracted_data.get("confidence", 0)
        
        # Rules to infer priority from outcomes
        if status == "APPROVED" and processing_time <= 2:
            return "HIGH"
        elif status == "APPROVED" and processing_time <= 5:
            return "NORMAL"
        elif status == "REJECTED" or processing_time > 7:
            return "LOW"
        elif confidence > 0.8 and status == "APPROVED":
            return "HIGH"
        elif confidence < 0.5 or status in ["NEEDS_REVIEW", "UNDER_REVIEW"]:
            return "LOW"
        else:
            return "NORMAL"


# Singleton instance for the application
_priority_model = None

def get_priority_model() -> ApplicationPriorityModel:
    """Get or create the singleton priority model instance"""
    global _priority_model
    if _priority_model is None:
        _priority_model = ApplicationPriorityModel()
    return _priority_model

def predict_application_priority(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to predict application priority
    
    Args:
        extracted_data: Extracted data from document processing
        
    Returns:
        Priority prediction results
    """
    model = get_priority_model()
    return model.predict(extracted_data)
