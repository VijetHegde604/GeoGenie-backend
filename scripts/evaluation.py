# evaluate_placeai.py

import os
import glob
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# ⬇️ change this to whatever your file is called, e.g. "search_and_embed"
from embed_generator import  get_embedder
from search_image import get_search_engine

TEST_DIR = Path("test_augmented")

# -------------------------------------------------------------------
# 1. Setup: labels from folder names
# -------------------------------------------------------------------
class_names = sorted(d for d in os.listdir(TEST_DIR)
                     if (TEST_DIR / d).is_dir())
label_to_idx = {name: i for i, name in enumerate(class_names)}
idx_to_label = {i: name for name, i in label_to_idx.items()}

print("Classes:", class_names)

# Load your global instances
search_engine = get_search_engine()
embedder = get_embedder()

# -------------------------------------------------------------------
# 2. Prediction using your CLIP + FAISS
# -------------------------------------------------------------------
def predict_label(image_path: str) -> str:
    """
    Uses your EmbeddingGenerator + ImageSearch.
    We take the best FAISS match as the predicted class.
    (No threshold here so everything gets mapped to some class,
    which is what we want for a confusion matrix.)
    """
    embedding = embedder.generate_embedding(image_path)
    results = search_engine.search(embedding, k=1)
    if not results:
        # if DB empty or something weird, fallback
        return None
    return results[0]["place_name"]

# -------------------------------------------------------------------
# 3. Run through test set
# -------------------------------------------------------------------
y_true = []
y_pred = []

for class_name in class_names:
    class_dir = TEST_DIR / class_name
    for img_path in glob.glob(str(class_dir / "*")):
        if not os.path.isfile(img_path):
            continue

        true_idx = label_to_idx[class_name]

        try:
            pred_label = predict_label(img_path)
        except Exception as e:
            print(f"Error predicting {img_path}: {e}")
            continue

        if pred_label is None or pred_label not in label_to_idx:
            # treat unknown / None as misclass (could also map to an 'Unknown' class)
            continue

        pred_idx = label_to_idx[pred_label]
        y_true.append(true_idx)
        y_pred.append(pred_idx)

y_true = np.array(y_true)
y_pred = np.array(y_pred)

overall_acc = (y_true == y_pred).mean()
print(f"Overall accuracy on augmented test set: {overall_acc:.4f}")

# -------------------------------------------------------------------
# 4. Confusion matrix
# -------------------------------------------------------------------
cm = confusion_matrix(y_true, y_pred, labels=range(len(class_names)))

fig, ax = plt.subplots(figsize=(10, 10))
disp = ConfusionMatrixDisplay(confusion_matrix=cm,
                              display_labels=class_names)
disp.plot(include_values=False, xticks_rotation=90, ax=ax, cmap="Blues")
ax.set_title("Confusion Matrix for PlaceAI (Augmented Test Set)")
plt.tight_layout()
plt.savefig("placeai_confusion_matrix.png", dpi=300)
plt.close()
print("Saved placeai_confusion_matrix.png")

# -------------------------------------------------------------------
# 5. Per-label accuracy bar graph
# -------------------------------------------------------------------
cm_sum = cm.sum(axis=1)
per_label_acc = cm.diagonal() / cm_sum

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(range(len(class_names)), per_label_acc)
ax.set_xticks(range(len(class_names)))
ax.set_xticklabels(class_names, rotation=90)
ax.set_ylim(0, 1.0)
ax.set_ylabel("Accuracy")
ax.set_xlabel("Label")
ax.set_title("Per-Label Accuracy for PlaceAI (Augmented Test Set)")
plt.tight_layout()
plt.savefig("placeai_per_label_accuracy.png", dpi=300)
plt.close()
print("Saved placeai_per_label_accuracy.png")
