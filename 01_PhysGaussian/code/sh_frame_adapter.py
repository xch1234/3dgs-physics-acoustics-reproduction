"""Convert inverse material rotation from the simulation basis to world basis."""
import torch


def inverse_rotation_to_world(inverse_rotation,preprocessing_rotations):
    if inverse_rotation is None or not preprocessing_rotations:return inverse_rotation
    Q=torch.eye(3,dtype=inverse_rotation.dtype,device=inverse_rotation.device)
    for rotation in preprocessing_rotations:
        Q=rotation.to(dtype=Q.dtype,device=Q.device)@Q
    return Q.transpose(-1,-2)@inverse_rotation@Q
