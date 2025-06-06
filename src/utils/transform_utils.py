import torch
from torch.utils.data import DataLoader
from src.utils.landmarks import normalize_landmarks
from src.config.hyperparameters import data_hyperparameters
from src.transforms.image_landmark_transform import RandomRotateFlip


def compute_data_mean_std(dataloader: DataLoader) -> tuple:
    """
    Computes the mean and standard deviation of a given dataset.

    Args:
        dataloader (DataLoader): A DataLoader object containing the dataset.

    Returns:
        tuple: A tuple containing the mean and standard deviation of the dataset.
    """
    mean, std = 0., 0.
    total_sum = 0.
    total_squared_sum = 0.
    total_num = 0

    for images, _ in dataloader:
        flattened_images = images.view(-1)  # (B*H*W)-shaped 1D tensor
        total_num += flattened_images.numel()  # total num of pixels
        total_sum += flattened_images.sum().item()  # sum of all pixel values
        total_squared_sum += flattened_images.pow(2).sum().item()  # sum of squared pixel values
        
    # Compute mean and std
    mean = total_sum / total_num
    std = (total_squared_sum / total_num - mean ** 2) ** 0.5  # sqrt(E[x**2] - E[x]**2)  -  std formula
    return mean, std


def denormalize(tensor: torch.Tensor, mean=data_hyperparameters["grayscale_mean"], std=data_hyperparameters["grayscale_std"]):
    """
    Denormalize a tensor by multiplying each channel by a standard deviation value, 
    and then adding a mean value to each channel. This is the inverse of the 
    standard normalization process. This function assumes that the tensor is
    in the range [0,1].

    Args:
        tensor: A tensor of values to be denormalized, shape (C, H, W)
        mean: A list of mean values to add to each channel of the tensor.
        std: A list of standard deviation values to multiply each channel of the tensor by.

    Returns:
        tensor: The denormalized tensor.
    """
    for t, m, s in zip(tensor, mean, std):
        t.mul_(s).add_(m) 
        
    return tensor


def transform_image_and_landmarks(image, landmarks, transforms, rotate_flip=True, rotation_range=data_hyperparameters["rotation_range"], hflip_prob=data_hyperparameters["hflip_prob"], normalize=True):
    """
    Apply a given transformation to an image and its associated landmarks.

    Args:
        image: The image to be transformed, a PIL Image.
        landmarks: The associated landmarks, shape (n_landmarks, 3) in range [0, 1].
        transforms: A torchvision transform to apply to the image.
        rotate_flip: If True, apply a random rotation and horizontal flip to the image and landmarks.
        rotation_range: The range of angles to randomly rotate the image and landmarks.
        hflip_prob: The probability of horizontally flipping the image and landmarks.
        normalize: If True, normalize the landmarks relative to the wrist.

    Returns:
        tuple: The transformed image and landmarks. The image is a tensor in shape (3, height, width),
        and the landmarks are a tensor in shape (n_landmarks, 3) in range [-1, 1].
    """
    if rotate_flip:
        rotate_flip_transform = RandomRotateFlip(rotation_range=rotation_range, horizontal_flip_prob=hflip_prob, return_tensor=False)
        image, landmarks = rotate_flip_transform(image, landmarks)  # landmarks are transformed, but still in range [0, 1], so we need to normalize and scale them
        
    if normalize:
        landmarks = normalize_landmarks(landmarks)
    
    return transforms(image), torch.from_numpy(landmarks)  # `image tensor` in shape (3, height, width); `landmarks tensor` in shape (n_landmarks, 3)  (n_landmarks = 21 in our case)