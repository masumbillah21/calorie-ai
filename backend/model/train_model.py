"""
CalorieAI - Food Recognition Model Training
Dataset: Food-101 (https://www.kaggle.com/datasets/dansbecker/food-101)
Model: MobileNetV2 transfer learning
Classes: 101 food categories
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_PHASE1 = 10
EPOCHS_PHASE2 = 20
DATASET_DIR = BASE_DIR / "dataset" / "food-101" / "images"
MODEL_OUT = BASE_DIR / "food_model.keras"
CLASS_OUT = BASE_DIR / "class_names.json"
PLOT_OUT = BASE_DIR / "training_history.png"


def ensure_dataset_exists() -> None:
    if DATASET_DIR.is_dir():
        return

    raise FileNotFoundError(
        f"Food-101 images were not found at {DATASET_DIR}. "
        "Run `make download-dataset` or place the dataset there before training."
    )


def build_datasets():
    train_gen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=25,
        width_shift_range=0.15,
        height_shift_range=0.15,
        shear_range=0.1,
        zoom_range=0.2,
        horizontal_flip=True,
        brightness_range=[0.85, 1.15],
        fill_mode="nearest",
        validation_split=0.2,
    )

    val_gen = ImageDataGenerator(rescale=1.0 / 255, validation_split=0.2)

    train_ds = train_gen.flow_from_directory(
        str(DATASET_DIR),
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
    )
    val_ds = val_gen.flow_from_directory(
        str(DATASET_DIR),
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
    )

    return train_ds, val_ds


def save_class_names(train_ds) -> dict[str, str]:
    class_names = {str(index): name for name, index in train_ds.class_indices.items()}
    with CLASS_OUT.open("w", encoding="utf-8") as file:
        json.dump(class_names, file, indent=2)
    return class_names


def build_model(num_classes: int):
    base_model = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    model = models.Sequential(
        [
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.BatchNormalization(),
            layers.Dense(1024, activation="relu"),
            layers.Dropout(0.45),
            layers.Dense(512, activation="relu"),
            layers.Dropout(0.3),
            layers.Dense(num_classes, activation="softmax"),
        ]
    )

    return model, base_model


def compile_model(model, learning_rate: float) -> None:
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate),
        loss="categorical_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.TopKCategoricalAccuracy(k=5, name="top5_acc"),
        ],
    )


def build_callbacks():
    return [
        ModelCheckpoint(
            str(MODEL_OUT),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.3,
            patience=3,
            min_lr=1e-7,
            verbose=1,
        ),
    ]


def plot_history(history_phase1, history_phase2) -> None:
    train_acc = history_phase1.history["accuracy"] + history_phase2.history["accuracy"]
    val_acc = (
        history_phase1.history["val_accuracy"]
        + history_phase2.history["val_accuracy"]
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(train_acc, label="Train", color="#4ade80")
    ax.plot(val_acc, label="Validation", color="#60a5fa")
    ax.set_title("Food Recognition Accuracy")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(PLOT_OUT, dpi=150)
    plt.close(fig)
    print(f"Saved training curve to: {PLOT_OUT}")


def main() -> None:
    ensure_dataset_exists()

    train_ds, val_ds = build_datasets()
    class_names = save_class_names(train_ds)
    print(
        f"Found {len(class_names)} food classes | "
        f"Train: {train_ds.samples} | Val: {val_ds.samples}"
    )

    model, base_model = build_model(len(class_names))
    callbacks = build_callbacks()

    print("\nPhase 1: training classifier head...")
    compile_model(model, learning_rate=1e-3)
    history_phase1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_PHASE1,
        callbacks=callbacks,
    )

    print("\nPhase 2: fine-tuning last 40 base layers...")
    base_model.trainable = True
    for layer in base_model.layers[:-40]:
        layer.trainable = False

    compile_model(model, learning_rate=1e-4)
    history_phase2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_PHASE2,
        callbacks=callbacks,
    )

    plot_history(history_phase1, history_phase2)
    print("")
    print(f"Model saved to: {MODEL_OUT}")
    print(f"Class names saved to: {CLASS_OUT}")


if __name__ == "__main__":
    main()
