"""
Machine Learning Citation Classifier

This module provides a machine learning-based classifier for legal citations
that can identify valid citations with high accuracy without requiring API calls.
"""

import os
import logging
import sqlite3
import re
import numpy as np
import pickle
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("citation_classifier")


class CitationClassifier:
    """
    A machine learning classifier for legal citations that can identify
    valid citations with high accuracy without requiring API calls.
    """

    def __init__(self):
        """Initialize the classifier."""
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "citations.db"
        )
        self.model_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "ml_models"
        )
        self.vectorizer_path = os.path.join(self.model_dir, "citation_vectorizer.pkl")
        self.model_path = os.path.join(self.model_dir, "citation_classifier.pkl")
        self.vectorizer = None
        self.model = None

        # Create model directory if it doesn't exist
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

        # Load the model if it exists
        self._load_model()

    def _load_model(self):
        """Load the trained model and vectorizer if they exist."""
        try:
            if os.path.exists(self.vectorizer_path) and os.path.exists(self.model_path):
                with open(self.vectorizer_path, "rb") as f:
                    self.vectorizer = pickle.load(f)

                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)

                logger.info("Loaded existing model and vectorizer")
                return True
            else:
                logger.info("No existing model found")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def _save_model(self):
        """Save the trained model and vectorizer."""
        try:
            with open(self.vectorizer_path, "wb") as f:
                pickle.dump(self.vectorizer, f)

            with open(self.model_path, "wb") as f:
                pickle.dump(self.model, f)

            logger.info("Saved model and vectorizer")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def _extract_features(self, citation):
        """Extract features from a citation for classification."""
        features = {}

        # Basic length features
        features["length"] = len(citation)
        features["word_count"] = len(citation.split())

        # Check for common patterns
        features["has_v"] = 1 if " v. " in citation else 0
        features["has_digits"] = 1 if re.search(r"\d", citation) else 0
        features["has_reporter"] = 0

        # Check for common reporters
        reporters = [
            "U.S.",
            "S.Ct.",
            "L.Ed.",
            "F.",
            "F.2d",
            "F.3d",
            "F.Supp.",
            "Wn.",
            "Wn.2d",
            "Wn. App.",
            "P.",
            "P.2d",
            "P.3d",
        ]

        for reporter in reporters:
            if reporter in citation:
                features["has_reporter"] = 1
                features[f"reporter_{reporter.replace('.', '')}"] = 1
            else:
                features[f"reporter_{reporter.replace('.', '')}"] = 0

        # Check for volume and page pattern
        vol_page_pattern = re.search(r"(\d+)\s+[A-Za-z\.\s]+\s+(\d+)", citation)
        if vol_page_pattern:
            features["has_vol_page"] = 1
            features["volume"] = int(vol_page_pattern.group(1))
            features["page"] = int(vol_page_pattern.group(2))
        else:
            features["has_vol_page"] = 0
            features["volume"] = 0
            features["page"] = 0

        # Check for year pattern
        year_pattern = re.search(r"\((\d{4})\)", citation)
        if year_pattern:
            features["has_year"] = 1
            features["year"] = int(year_pattern.group(1))
        else:
            features["has_year"] = 0
            features["year"] = 0

        return features

    def _get_training_data(self):
        """Get training data from the database."""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all citations
            cursor.execute("SELECT citation_text, found FROM citations")
            rows = cursor.fetchall()

            # Close the connection
            conn.close()

            if not rows:
                logger.error("No citations found in the database")
                return None, None

            # Prepare training data
            citations = []
            labels = []

            for row in rows:
                citation_text = row[0]
                found = row[1]

                if citation_text:
                    citations.append(citation_text)
                    labels.append(1 if found else 0)

            logger.info(f"Retrieved {len(citations)} citations for training")

            return citations, labels

        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return None, None

    def train(self, force=False):
        """Train the classifier on the citation database."""
        # Check if model already exists and force is False
        if self.model is not None and not force:
            logger.info("Model already exists. Use force=True to retrain.")
            return True

        # Get training data
        citations, labels = self._get_training_data()

        if not citations or not labels:
            logger.error("No training data available")
            return False

        try:
            # Create feature vectors
            logger.info("Creating feature vectors...")
            self.vectorizer = TfidfVectorizer(
                analyzer="char_wb", ngram_range=(2, 5), max_features=5000
            )

            X_text = self.vectorizer.fit_transform(citations)

            # Extract additional features
            logger.info("Extracting additional features...")
            additional_features = []

            for citation in citations:
                features = self._extract_features(citation)
                additional_features.append(
                    [
                        features["length"],
                        features["word_count"],
                        features["has_v"],
                        features["has_digits"],
                        features["has_reporter"],
                        features["has_vol_page"],
                        features["volume"],
                        features["page"],
                        features["has_year"],
                        features["year"],
                    ]
                )

            # Combine text features with additional features
            X_additional = np.array(additional_features)
            X_combined = np.hstack((X_text.toarray(), X_additional))

            # Split into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(
                X_combined, labels, test_size=0.2, random_state=42
            )

            # Train the model
            logger.info("Training the model...")
            self.model = RandomForestClassifier(
                n_estimators=100, max_depth=10, random_state=42
            )

            self.model.fit(X_train, y_train)

            # Evaluate the model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            logger.info(f"Model trained with accuracy: {accuracy:.4f}")
            logger.info(
                "\nClassification Report:\n" + classification_report(y_test, y_pred)
            )

            # Save the model
            self._save_model()

            return True

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False

    def predict(self, citation):
        """
        Predict whether a citation is valid.
        Returns a confidence score between 0 and 1.
        """
        if not self.model or not self.vectorizer:
            logger.error("Model not trained. Call train() first.")
            return 0.0

        try:
            # Create feature vector
            X_text = self.vectorizer.transform([citation])

            # Extract additional features
            features = self._extract_features(citation)
            X_additional = np.array(
                [
                    features["length"],
                    features["word_count"],
                    features["has_v"],
                    features["has_digits"],
                    features["has_reporter"],
                    features["has_vol_page"],
                    features["volume"],
                    features["page"],
                    features["has_year"],
                    features["year"],
                ]
            ).reshape(1, -1)

            # Combine text features with additional features
            X_combined = np.hstack((X_text.toarray(), X_additional))

            # Make prediction
            prediction = self.model.predict_proba(X_combined)[0]

            # Return confidence score for the positive class
            return prediction[1]

        except Exception as e:
            logger.error(f"Error predicting citation '{citation}': {e}")
            return 0.0

    def classify_citation(self, citation):
        """
        Classify a citation and return a detailed result.
        """
        confidence = self.predict(citation)

        # Extract features for explanation
        features = self._extract_features(citation)

        # Determine classification
        is_valid = confidence >= 0.7  # Threshold can be adjusted

        # Create explanation
        explanation = []

        if features["has_reporter"]:
            explanation.append("Contains a recognized legal reporter")
        else:
            explanation.append("Does not contain a recognized legal reporter")

        if features["has_vol_page"]:
            explanation.append(
                f"Contains volume ({features['volume']}) and page ({features['page']}) numbers"
            )
        else:
            explanation.append("Missing volume and page number pattern")

        if features["has_year"]:
            explanation.append(f"Contains a year ({features['year']})")
        else:
            explanation.append("Missing year")

        if features["has_v"]:
            explanation.append("Contains 'v.' (versus) indicating a case name")
        else:
            explanation.append("Missing 'v.' (versus) in case name")

        # Return classification result
        return {
            "citation": citation,
            "is_valid": is_valid,
            "confidence": confidence,
            "features": features,
            "explanation": explanation,
            "classification_date": datetime.now().isoformat(),
        }

    def batch_classify(self, citations):
        """
        Classify a batch of citations.
        Returns a list of classification results.
        """
        results = []

        for citation in citations:
            result = self.classify_citation(citation)
            results.append(result)

        return results


# Example usage
if __name__ == "__main__":
    classifier = CitationClassifier()

    # Train the model
    classifier.train()

    # Example citations
    citations = [
        "410 U.S. 113",  # Roe v. Wade
        "347 U.S. 483",  # Brown v. Board of Education
        "5 U.S. 137",  # Marbury v. Madison
        "198 Wn.2d 271",  # Washington Supreme Court case
        "175 Wn. App. 1",  # Washington Court of Appeals case
        "Smith v. Jones, 123 Invalid 456",  # Invalid citation
    ]

    # Classify each citation
    for citation in citations:
        result = classifier.classify_citation(citation)
        print(f"Citation: {citation}")
        print(f"Valid: {result['is_valid']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Explanation: {', '.join(result['explanation'])}")
        print()
