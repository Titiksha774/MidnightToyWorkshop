import os
import struct

import numpy as np
from sklearn.neural_network import MLPClassifier

CLASSES = ["Idle", "Swipe Left", "Swipe Right", "Swipe Up", "Swipe Down", "Push", "Wind Up"]
rng = np.random.default_rng(42)


def make_samples(n_per_class=1500):
    X, y = [], []
    directions = {1: (-1, 0, 0), 2: (1, 0, 0), 3: (0, 1, 0), 4: (0, -1, 0), 5: (0, 0, 1)}
    for _ in range(n_per_class):
        d = rng.normal(0, 0.02, 3)
        X.append([*d, np.linalg.norm(d) * rng.uniform(1.0, 2.5)])
        y.append(0)
        for label, direction in directions.items():
            length = rng.uniform(0.12, 0.6)
            d = np.array(direction, float) * length + rng.normal(0, 0.25 * length, 3)
            X.append([*d, np.linalg.norm(d) * rng.uniform(1.0, 1.4)])
            y.append(label)
        d = rng.normal(0, 0.04, 3)
        X.append([*d, rng.uniform(0.2, 0.9)])
        y.append(6)
    return np.array(X, np.float32), np.array(y)


X, y = make_samples()
clf = MLPClassifier(hidden_layer_sizes=(16,), activation="relu", max_iter=600, random_state=0)
clf.fit(X, y)
print("training accuracy:", round(clf.score(X, y), 3))

W1, b1 = clf.coefs_[0].astype(np.float32), clf.intercepts_[0].astype(np.float32)
W2, b2 = clf.coefs_[1].astype(np.float32), clf.intercepts_[1].astype(np.float32)


def varint(v):
    out = b""
    v &= (1 << 64) - 1
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


def f_varint(field, v):
    return varint(field << 3) + varint(v)


def f_bytes(field, data):
    if isinstance(data, str):
        data = data.encode()
    return varint((field << 3) | 2) + varint(len(data)) + data


def tensor(name, array):
    out = b"".join(f_varint(1, d) for d in array.shape)
    out += f_varint(2, 1)
    out += f_bytes(8, name)
    out += f_bytes(9, array.astype("<f4").tobytes())
    return out


def value_info(name, shape):
    dims = b"".join(f_bytes(1, f_varint(1, d)) for d in shape)
    tensor_type = f_varint(1, 1) + f_bytes(2, dims)
    return f_bytes(1, name) + f_bytes(2, f_bytes(1, tensor_type))


def node(op, inputs, outputs, name, attributes=b""):
    out = b"".join(f_bytes(1, i) for i in inputs)
    out += b"".join(f_bytes(2, o) for o in outputs)
    return out + f_bytes(3, name) + f_bytes(4, op) + attributes


def int_attribute(name, value):
    return f_bytes(5, f_bytes(1, name) + f_varint(3, value) + f_varint(20, 2))


graph = b"".join([
    f_bytes(1, node("Gemm", ["features", "W1", "b1"], ["hidden"], "dense1")),
    f_bytes(1, node("Relu", ["hidden"], ["hidden_relu"], "relu1")),
    f_bytes(1, node("Gemm", ["hidden_relu", "W2", "b2"], ["logits"], "dense2")),
    f_bytes(1, node("Softmax", ["logits"], ["probabilities"], "softmax", int_attribute("axis", 1))),
    f_bytes(2, "gesture_classifier"),
    f_bytes(5, tensor("W1", W1)),
    f_bytes(5, tensor("b1", b1)),
    f_bytes(5, tensor("W2", W2)),
    f_bytes(5, tensor("b2", b2)),
    f_bytes(11, value_info("features", [1, 4])),
    f_bytes(12, value_info("probabilities", [1, len(CLASSES)])),
])

model = (
    f_varint(1, 8)
    + f_bytes(2, "Lab8VR gesture trainer")
    + f_bytes(7, graph)
    + f_bytes(8, f_bytes(1, "") + f_varint(2, 13))
)

out_path = os.path.join(os.path.dirname(__file__), "..", "Assets", "ML", "GestureClassifier.onnx")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "wb") as f:
    f.write(model)
print("saved", os.path.normpath(out_path), len(model), "bytes")


def predict(x):
    h = np.maximum(0, x @ W1 + b1)
    z = h @ W2 + b2
    e = np.exp(z - z.max())
    return e / e.sum()


for name, x in [("still", [0.01, 0, 0, 0.02]), ("right", [0.35, 0.02, 0, 0.38]),
                ("up", [0, 0.3, 0.03, 0.33]), ("push", [0.02, 0, 0.4, 0.42]),
                ("circle", [0.03, -0.02, 0.01, 0.45])]:
    p = predict(np.array(x, np.float32))
    print(f"{name:>6} -> {CLASSES[int(p.argmax())]} ({p.max():.2f})")
