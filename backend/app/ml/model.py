"""
予想スコア用の超軽量ニューラルネットワーク（numpyのみ、外部MLフレームワーク不使用）。

入力: build_features() が生成する特徴量ベクトル
出力: 0〜1 の「能力スコア」（sigmoid）
"""
import numpy as np

HIDDEN_DIM = 6


class SimpleNN:
    """1隠れ層 (tanh) + 出力層 (sigmoid) のシンプルなMLP。"""

    def __init__(self, input_dim: int, hidden_dim: int = HIDDEN_DIM, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.W1 = rng.normal(0, 0.5, (input_dim, hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        self.W2 = rng.normal(0, 0.5, (hidden_dim, 1))
        self.b2 = np.zeros(1)

    def forward(self, X: np.ndarray) -> np.ndarray:
        z1 = X @ self.W1 + self.b1
        a1 = np.tanh(z1)
        z2 = a1 @ self.W2 + self.b2
        a2 = 1 / (1 + np.exp(-z2))
        self._cache = (X, a1, a2)
        return a2.flatten()

    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 300, lr: float = 0.05) -> None:
        """フルバッチ勾配降下法でMSE損失を最小化する（既存の重みからウォームスタート）。"""
        n = X.shape[0]
        y = y.reshape(-1, 1)
        for _ in range(epochs):
            pred = self.forward(X)
            X_in, a1, a2 = self._cache
            error = (a2 - y)  # dL/da2, MSE勾配

            d2 = error * a2 * (1 - a2)  # シグモイド微分込み
            grad_W2 = a1.T @ d2 / n
            grad_b2 = d2.mean(axis=0)

            d1 = (d2 @ self.W2.T) * (1 - a1 ** 2)  # tanh微分込み
            grad_W1 = X_in.T @ d1 / n
            grad_b1 = d1.mean(axis=0)

            self.W1 -= lr * grad_W1
            self.b1 -= lr * grad_b1
            self.W2 -= lr * grad_W2
            self.b2 -= lr * grad_b2

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.forward(X)

    def to_dict(self) -> dict:
        return {
            "input_dim": self.input_dim,
            "hidden_dim": self.hidden_dim,
            "W1": self.W1.tolist(),
            "b1": self.b1.tolist(),
            "W2": self.W2.tolist(),
            "b2": self.b2.tolist(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SimpleNN":
        model = cls(data["input_dim"], data["hidden_dim"])
        model.W1 = np.array(data["W1"])
        model.b1 = np.array(data["b1"])
        model.W2 = np.array(data["W2"])
        model.b2 = np.array(data["b2"])
        return model
