"""
Machine Learning Models for Price Prediction and Signal Enhancement
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Try to import deep learning libraries
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch not available. Deep learning models disabled.")


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


# Deep Learning Models (PyTorch)
if TORCH_AVAILABLE:
    
    class LSTMModel(nn.Module):
        """
        LSTM model for time series prediction
        """
        
        def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
            super(LSTMModel, self).__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            
            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout if num_layers > 1 else 0,
                batch_first=True
            )
            
            self.fc = nn.Linear(hidden_size, 1)
            
        def forward(self, x):
            # x shape: (batch, seq_len, input_size)
            lstm_out, _ = self.lstm(x)
            # Take last output
            last_output = lstm_out[:, -1, :]
            prediction = self.fc(last_output)
            return prediction
    
    
    class GRUModel(nn.Module):
        """
        GRU model for time series prediction
        Faster than LSTM, often similar performance
        """
        
        def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
            super(GRUModel, self).__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            
            self.gru = nn.GRU(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout if num_layers > 1 else 0,
                batch_first=True
            )
            
            self.fc = nn.Linear(hidden_size, 1)
            
        def forward(self, x):
            gru_out, _ = self.gru(x)
            last_output = gru_out[:, -1, :]
            prediction = self.fc(last_output)
            return prediction
    
    
    class TransformerModel(nn.Module):
        """
        Transformer model for time series prediction
        Better for capturing long-range dependencies
        """
        
        def __init__(self, input_size: int, d_model: int = 64, nhead: int = 4, 
                     num_layers: int = 2, dropout: float = 0.1):
            super(TransformerModel, self).__init__()
            
            self.input_projection = nn.Linear(input_size, d_model)
            
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dropout=dropout,
                batch_first=True
            )
            
            self.transformer = nn.TransformerEncoder(
                encoder_layer,
                num_layers=num_layers
            )
            
            self.fc = nn.Linear(d_model, 1)
            
        def forward(self, x):
            # Project input to d_model dimensions
            x = self.input_projection(x)
            
            # Transformer encoding
            transformer_out = self.transformer(x)
            
            # Take mean of sequence
            pooled = transformer_out.mean(dim=1)
            
            prediction = self.fc(pooled)
            return prediction
    
    
    class DeepLearningPredictor:
        """
        Deep learning predictor with LSTM, GRU, and Transformer models
        """
        
        def __init__(self, model_type: str = 'lstm', seq_length: int = 60):
            """
            Args:
                model_type: 'lstm', 'gru', or 'transformer'
                seq_length: Sequence length for time series
            """
            self.model_type = model_type
            self.seq_length = seq_length
            self.model = None
            self.scaler = MinMaxScaler()
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
        def prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
            """
            Prepare sequences for time series prediction
            """
            X, y = [], []
            
            for i in range(len(data) - self.seq_length):
                X.append(data[i:i + self.seq_length])
                y.append(data[i + self.seq_length, 0])  # Predict close price
            
            return np.array(X), np.array(y)
        
        def train(self, df: pd.DataFrame, epochs: int = 50, batch_size: int = 32) -> Dict:
            """
            Train deep learning model
            """
            # Prepare data
            features = df[['Open', 'High', 'Low', 'Close', 'Volume']].values
            scaled_data = self.scaler.fit_transform(features)
            
            X, y = self.prepare_sequences(scaled_data)
            
            if len(X) < 100:
                return {
                    'success': False,
                    'message': 'Insufficient data for training'
                }
            
            # Train/test split
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Convert to tensors
            X_train = torch.FloatTensor(X_train).to(self.device)
            y_train = torch.FloatTensor(y_train).unsqueeze(1).to(self.device)
            X_test = torch.FloatTensor(X_test).to(self.device)
            y_test = torch.FloatTensor(y_test).unsqueeze(1).to(self.device)
            
            # Initialize model
            input_size = X_train.shape[2]
            
            if self.model_type == 'lstm':
                self.model = LSTMModel(input_size).to(self.device)
            elif self.model_type == 'gru':
                self.model = GRUModel(input_size).to(self.device)
            elif self.model_type == 'transformer':
                self.model = TransformerModel(input_size).to(self.device)
            else:
                return {
                    'success': False,
                    'message': f'Unknown model type: {self.model_type}'
                }
            
            # Training setup
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            
            # Training loop
            train_losses = []
            test_losses = []
            
            for epoch in range(epochs):
                self.model.train()
                
                # Mini-batch training
                for i in range(0, len(X_train), batch_size):
                    batch_X = X_train[i:i+batch_size]
                    batch_y = y_train[i:i+batch_size]
                    
                    optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                
                # Evaluation
                self.model.eval()
                with torch.no_grad():
                    train_pred = self.model(X_train)
                    test_pred = self.model(X_test)
                    
                    train_loss = criterion(train_pred, y_train).item()
                    test_loss = criterion(test_pred, y_test).item()
                    
                    train_losses.append(train_loss)
                    test_losses.append(test_loss)
            
            # Calculate metrics
            with torch.no_grad():
                test_pred = self.model(X_test).cpu().numpy()
                y_test_np = y_test.cpu().numpy()
                
                mse = np.mean((test_pred - y_test_np) ** 2)
                rmse = np.sqrt(mse)
                mae = np.mean(np.abs(test_pred - y_test_np))
            
            return {
                'success': True,
                'model_type': self.model_type,
                'epochs': epochs,
                'final_train_loss': train_losses[-1],
                'final_test_loss': test_losses[-1],
                'rmse': float(rmse),
                'mae': float(mae),
                'num_samples': len(X)
            }
        
        def predict(self, df: pd.DataFrame, steps_ahead: int = 1) -> Dict:
            """
            Predict future prices
            """
            if self.model is None:
                return {
                    'success': False,
                    'message': 'Model not trained'
                }
            
            # Prepare data
            features = df[['Open', 'High', 'Low', 'Close', 'Volume']].values
            scaled_data = self.scaler.transform(features)
            
            # Get last sequence
            last_sequence = scaled_data[-self.seq_length:]
            
            # Predict
            self.model.eval()
            with torch.no_grad():
                X = torch.FloatTensor(last_sequence).unsqueeze(0).to(self.device)
                prediction = self.model(X).cpu().numpy()[0, 0]
            
            # Inverse transform
            dummy = np.zeros((1, 5))
            dummy[0, 3] = prediction  # Close price is 4th column
            prediction_original = self.scaler.inverse_transform(dummy)[0, 3]
            
            current_price = df['Close'].iloc[-1]
            
            return {
                'success': True,
                'current_price': float(current_price),
                'predicted_price': float(prediction_original),
                'predicted_change_pct': float((prediction_original / current_price - 1) * 100),
                'model_type': self.model_type
            }


else:
    # Placeholder classes if PyTorch not available
    class DeepLearningPredictor:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch not available. Install with: pip install torch")
