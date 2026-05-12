"""
Machine Learning Models for Price Prediction and Signal Enhancement
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


class MLPredictor:
    """
    Machine Learning predictor for stock movements
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.classifier = None
        self.regressor = None
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for ML models
        """
        features = pd.DataFrame(index=df.index)
        
        # Price-based features
        features['returns_1d'] = df['Close'].pct_change()
        features['returns_5d'] = df['Close'].pct_change(5)
        features['returns_20d'] = df['Close'].pct_change(20)
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            features[f'sma_{period}'] = df['Close'].rolling(period).mean()
            features[f'price_to_sma_{period}'] = df['Close'] / features[f'sma_{period}']
        
        # Volatility features
        features['volatility_20d'] = df['Close'].pct_change().rolling(20).std()
        features['volatility_60d'] = df['Close'].pct_change().rolling(60).std()
        
        # Volume features
        features['volume_sma_20'] = df['Volume'].rolling(20).mean()
        features['volume_ratio'] = df['Volume'] / features['volume_sma_20']
        
        # Momentum indicators
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        features['macd_diff'] = features['macd'] - features['macd_signal']
        
        # Bollinger Bands
        sma_20 = df['Close'].rolling(20).mean()
        std_20 = df['Close'].rolling(20).std()
        features['bb_upper'] = sma_20 + (2 * std_20)
        features['bb_lower'] = sma_20 - (2 * std_20)
        features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / sma_20
        features['bb_position'] = (df['Close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
        
        # Price patterns
        features['high_low_ratio'] = df['High'] / df['Low']
        features['close_open_ratio'] = df['Close'] / df['Open']
        
        # Lag features
        for lag in [1, 2, 3, 5]:
            features[f'return_lag_{lag}'] = features['returns_1d'].shift(lag)
        
        return features.dropna()
    
    def train_direction_classifier(self, df: pd.DataFrame, lookahead: int = 5) -> Dict:
        """
        Train classifier to predict price direction
        
        Args:
            df: DataFrame with OHLC data
            lookahead: Days ahead to predict
        
        Returns:
            Training metrics
        """
        features_df = self.prepare_features(df)
        
        # Create target: 1 if price goes up, 0 if down
        future_returns = df['Close'].pct_change(lookahead).shift(-lookahead)
        target = (future_returns > 0).astype(int)
        
        # Align features and target
        common_index = features_df.index.intersection(target.index)
        X = features_df.loc[common_index]
        y = target.loc[common_index]
        
        # Remove NaN
        valid_idx = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_idx]
        y = y[valid_idx]
        
        if len(X) < 100:
            return {
                'success': False,
                'message': 'Insufficient data for training'
            }
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            random_state=42
        )
        
        self.classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.classifier.score(X_train_scaled, y_train)
        test_score = self.classifier.score(X_test_scaled, y_test)
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.classifier.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return {
            'success': True,
            'train_accuracy': float(train_score),
            'test_accuracy': float(test_score),
            'num_samples': len(X),
            'num_features': len(X.columns),
            'top_features': feature_importance.head(10).to_dict('records')
        }
    
    def predict_direction(self, df: pd.DataFrame) -> Dict:
        """
        Predict price direction for next period
        """
        if self.classifier is None:
            return {
                'success': False,
                'message': 'Model not trained. Call train_direction_classifier first.'
            }
        
        features_df = self.prepare_features(df)
        
        if len(features_df) == 0:
            return {
                'success': False,
                'message': 'Insufficient data for prediction'
            }
        
        # Get latest features
        latest_features = features_df.iloc[[-1]]
        
        # Scale
        latest_scaled = self.scaler.transform(latest_features)
        
        # Predict
        prediction = self.classifier.predict(latest_scaled)[0]
        probability = self.classifier.predict_proba(latest_scaled)[0]
        
        return {
            'success': True,
            'prediction': 'UP' if prediction == 1 else 'DOWN',
            'probability_up': float(probability[1]),
            'probability_down': float(probability[0]),
            'confidence': float(max(probability))
        }
    
    def train_price_regressor(self, df: pd.DataFrame, lookahead: int = 5) -> Dict:
        """
        Train regressor to predict future price
        """
        features_df = self.prepare_features(df)
        
        # Create target: future price
        target = df['Close'].shift(-lookahead)
        
        # Align
        common_index = features_df.index.intersection(target.index)
        X = features_df.loc[common_index]
        y = target.loc[common_index]
        
        # Remove NaN
        valid_idx = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_idx]
        y = y[valid_idx]
        
        if len(X) < 100:
            return {
                'success': False,
                'message': 'Insufficient data for training'
            }
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # Scale
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Gradient Boosting
        self.regressor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        self.regressor.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.regressor.score(X_train_scaled, y_train)
        test_score = self.regressor.score(X_test_scaled, y_test)
        
        # Predictions
        y_pred = self.regressor.predict(X_test_scaled)
        mae = np.mean(np.abs(y_test - y_pred))
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        return {
            'success': True,
            'train_r2': float(train_score),
            'test_r2': float(test_score),
            'mae': float(mae),
            'mape': float(mape),
            'num_samples': len(X)
        }
    
    def predict_price(self, df: pd.DataFrame) -> Dict:
        """
        Predict future price
        """
        if self.regressor is None:
            return {
                'success': False,
                'message': 'Model not trained. Call train_price_regressor first.'
            }
        
        features_df = self.prepare_features(df)
        
        if len(features_df) == 0:
            return {
                'success': False,
                'message': 'Insufficient data for prediction'
            }
        
        # Get latest
        latest_features = features_df.iloc[[-1]]
        latest_scaled = self.scaler.transform(latest_features)
        
        # Predict
        predicted_price = self.regressor.predict(latest_scaled)[0]
        current_price = df['Close'].iloc[-1]
        
        return {
            'success': True,
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'predicted_change_pct': float((predicted_price / current_price - 1) * 100)
        }


class EnsembleSignalGenerator:
    """
    Combine multiple signals using ensemble methods
    """
    
    @staticmethod
    def weighted_ensemble(signals: Dict[str, int], weights: Dict[str, float]) -> Dict:
        """
        Combine signals with weights
        
        Args:
            signals: Dict of signal_name -> signal_value (-1, 0, 1)
            weights: Dict of signal_name -> weight (0-1)
        
        Returns:
            Ensemble signal and confidence
        """
        weighted_sum = sum(signals[name] * weights.get(name, 1.0) for name in signals)
        total_weight = sum(weights.get(name, 1.0) for name in signals)
        
        ensemble_score = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Determine signal
        if ensemble_score > 0.3:
            signal = 'BUY'
        elif ensemble_score < -0.3:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        confidence = abs(ensemble_score)
        
        return {
            'signal': signal,
            'score': float(ensemble_score),
            'confidence': float(confidence),
            'individual_signals': signals,
            'weights': weights
        }
    
    @staticmethod
    def majority_vote(signals: Dict[str, int]) -> Dict:
        """
        Simple majority voting
        """
        votes = list(signals.values())
        
        buy_votes = sum(1 for v in votes if v > 0)
        sell_votes = sum(1 for v in votes if v < 0)
        neutral_votes = sum(1 for v in votes if v == 0)
        
        total_votes = len(votes)
        
        if buy_votes > sell_votes and buy_votes > neutral_votes:
            signal = 'BUY'
            confidence = buy_votes / total_votes
        elif sell_votes > buy_votes and sell_votes > neutral_votes:
            signal = 'SELL'
            confidence = sell_votes / total_votes
        else:
            signal = 'NEUTRAL'
            confidence = neutral_votes / total_votes
        
        return {
            'signal': signal,
            'confidence': float(confidence),
            'buy_votes': buy_votes,
            'sell_votes': sell_votes,
            'neutral_votes': neutral_votes,
            'total_votes': total_votes
        }
