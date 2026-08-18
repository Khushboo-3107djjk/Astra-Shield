import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from pathlib import Path
import random
import numpy as np

# Set random seed for reproducibility
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

def get_data_loaders(data_dir, batch_size=8):
    # Standard ResNet normalization
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'test': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    image_datasets = {}
    dataloaders = {}
    dataset_sizes = {}

    for split in ['train', 'val', 'test']:
        split_dir = Path(data_dir) / split
        if split_dir.exists() and len(list(split_dir.glob('*/*'))) > 0:
            image_datasets[split] = datasets.ImageFolder(split_dir, data_transforms[split])
            dataloaders[split] = DataLoader(
                image_datasets[split], batch_size=batch_size, shuffle=(split == 'train'), num_workers=0
            )
            dataset_sizes[split] = len(image_datasets[split])
            
    return dataloaders, dataset_sizes, image_datasets.get('train').classes if 'train' in image_datasets else []

def train_model(model, dataloaders, dataset_sizes, criterion, optimizer, num_epochs=10, save_path='best_classifier.pth'):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    best_acc = 0.0

    for epoch in range(num_epochs):
        print(f'Epoch {epoch+1}/{num_epochs}', flush=True)
        print('-' * 10, flush=True)

        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase not in dataloaders:
                continue
                
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                # forward
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f'{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}', flush=True)

            # Deep copy the model if it's the best validation so far
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                torch.save(model.state_dict(), save_path)
                print(f"🌟 Saved new best model to {save_path}", flush=True)

        print()

    print(f'Best Val Accuracy: {best_acc:4f}')
    return model

def build_model(num_classes):
    """Builds ResNet50 matching our DisasterClassifier architecture"""
    # Use pretrained ResNet50
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    
    # Freeze base layers for faster transfer learning (optional)
    for param in model.parameters():
        param.requires_grad = False
        
    # Replace final layer
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    
    return model

if __name__ == '__main__':
    print("🚀 ASTRA-SHIELD: 4-Class Classifier Training Setup")
    
    # Expected locations
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'datasets'
    output_dir = project_root / 'models' / 'classifier'
    save_path = output_dir / 'disaster_classifier.pth'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dataloaders, dataset_sizes, classes = get_data_loaders(data_dir)
    
    if not dataloaders or 'train' not in dataloaders:
        print("❌ Dataset not found or empty. Please populate ml/datasets/train/")
        print("Required classes: normal, flood, wildfire, cyclone, landslide, earthquake, drought")
        exit(1)
        
    print(f"Found {len(classes)} classes: {classes}")
    for split, size in dataset_sizes.items():
        print(f" - {split.capitalize()} split: {size} images")
        
    # Initialize model
    model = build_model(num_classes=len(classes))
    
    # Loss and optimizer (only optimizing the final fc layer)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=0.001)
    
    print("\nStarting Training (Transfer Learning)...")
    model = train_model(model, dataloaders, dataset_sizes, criterion, optimizer, num_epochs=2, save_path=str(save_path))
