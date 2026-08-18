import os
import torch
from torchvision import datasets, transforms, models
import torch.nn as nn
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from pathlib import Path
import numpy as np

device = torch.device('cpu')

# Model
num_classes = 4
model = models.resnet50(weights=None)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, num_classes)
model.load_state_dict(torch.load('ml/models/classifier/disaster_classifier.pth', map_location=device))
model = model.to(device)
model.eval()

# Data
test_dir = 'ml/datasets/test'
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
test_dataset = datasets.ImageFolder(test_dir, transform)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=8, shuffle=False)

classes = test_dataset.classes
print(f'ASTRA-SHIELD 4-Class Classifier Evaluation')
print(f'Classes: {classes}')

all_preds = []
all_labels = []

with torch.no_grad():
    for inputs, labels in test_loader:
        inputs = inputs.to(device)
        outputs = model(inputs)
        _, preds = torch.max(outputs, 1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.numpy())

acc = accuracy_score(all_labels, all_preds)
print(f'\nTest Accuracy: {acc:.4f}')

print('\nConfusion Matrix:')
print(confusion_matrix(all_labels, all_preds))

print('\nClassification Report:')
print(classification_report(all_labels, all_preds, target_names=classes))
