#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2019/02/19
author: lujie
"""

import matplotlib
import numpy as np
from IPython import embed
from scipy.ndimage import uniform_filter

def extract_features(imgs, feature_fns, verbose = False):
    '''
    Given pixel data for images and several feature functions that can operate on
    single images, apply all feature functions to all images, concatenating the
    feature vectors for each image and storing the features for all images in
    a single matrix.

    Inputs:
    - imgs: N x H X W X C array of pixel data for N images.
    - feature_fns: List of k feature functions. The ith feature function should
      take as input an H x W x D array and return a (one-dimensional) array of
      length F_i.
    - verbose: Boolean; if true, print progress.

    Returns:
    An array of shape (N, F_1 + ... + F_k) where each column is the concatenation
    of all features for a single image.
    '''
    num_img = imgs.shape[0]
    if num_img == 0:
        return np.array([])

    # Use the first image to determine feature dimensions
    feature_dims, first_image_features = [], []
    for feature_fn in feature_fns:
        feats = feature_fn(imgs[0].squeeze())
        assert len(feats.shape) == 1, 'Feature functions must be one-dimensional'
        feature_dims.append(feats.size)
        first_image_features.append(feats)

    # Now that we know the dimensions of the features, we can allocate a single
    # big array to store all features as columns.
    total_feature_dim = sum(feature_dims)
    imgs_features = np.zeros((num_img, total_feature_dim))
    imgs_features[0] = np.hstack(first_image_features).T    # concat on row

    # Extract features for the rest of the images.
    for i in range(1, num_img):
        idx = 0
        for feature_fn, feature_dim in zip(feature_fns, feature_dims):
            next_idx = idx + feature_dim
            imgs_features[i, idx:next_idx] = feature_fn(imgs[i].squeeze())
            idx = next_idx
        if verbose and i % 1000 == 0:
            print('Done extracting features for %d / %d images' % (i, num_img))
    return imgs_features

def rgb2gray(rgb):
    ''' convert RGB image to grayscale '''
    return np.dot(rgb[...,:3], [0.299, 0.587, 0.144])

def hog_feature(img):
    '''
    Compute Histogram of Gradient (HOG) feature for an image
    Parameters: an input grayscale or rgb image
    Returns: Histogram of Gradient (HOG) feature
    Modified from skimage.feature.hog http://pydoc.net/Python/scikits-image/0.4.2/skimage.feature.hog
    Reference : Histograms of Oriented Gradients for Human Detection Navneet Dalal and Bill Triggs, CVPR 2005
    '''
    # convert rgb to grayscale if needed
    img = rgb2gray(img) if img.ndim == 3 else np.at_least_2d(img)

    img_y, img_x = img.shape[0],  img.shape[1]
    orientations = 9 # number of gradient bins
    cx, cy = (8, 8) # pixels per cell

    gx, gy = np.zeros(img.shape), np.zeros(img.shape)
    gx[:, :-1] = np.diff(img, n = 1, axis = 1) # compute gradient on x-direction
    gy[:-1, :] = np.diff(img, n = 1, axis = 0) # compute gradient on y-direction
    grad_mag = np.sqrt(gx ** 2 + gy ** 2) # gradient magnitude
    grad_ori = np.arctan2(gy, (gx + 1e-15)) * (180 / np.pi) + 90 # gradient orientation

    n_cellsx, n_cellsy = int(np.floor(img_x / cx)), int(np.floor(img_y / cy))
    # compute orientations integral images
    orientation_histogram = np.zeros((n_cellsx, n_cellsy, orientations))

    for i in range(orientations):
        # create new integral image for this orientation
        # isolate orientations in this range
        temp_ori = np.where(grad_ori < 180 / orientations * (i + 1), grad_ori, 0)
        temp_ori = np.where(grad_ori >= 180 / orientations * i, temp_ori, 0)
        # select magnitudes for those orientations
        temp_mag = np.where( temp_ori > 0, grad_mag, 0)
        orientation_histogram[:,:,i] = uniform_filter(temp_mag, size=(cx, cy))[cx//2::cx, cy//2::cy].T  # [4, 12, 20, 28] * [4, 12, 20, 28]
    return orientation_histogram.ravel()

def color_histogram_hsv(im, nbin = 10, xmin = 0, xmax = 255, normalized = True):
    '''
      Compute color histogram for an image using hue.

      Inputs:
      - im: H x W x C array of pixel data for an RGB image.
      - nbin: Number of histogram bins. (default: 10)
      - xmin: Minimum pixel value (default: 0)
      - xmax: Maximum pixel value (default: 255)
      - normalized: Whether to normalize the histogram (default: True)

      Returns:
        1D vector of length nbin giving the color histogram over the hue of the input image.
    '''
    bins = np.linspace(xmin, xmax, nbin + 1)
    hsv = matplotlib.colors.rgb_to_hsv(im / xmax) * xmax
    imhist, bin_edges = np.histogram(hsv[:,:,0], bins = bins, density = normalized)
    imhist = imhist * np.diff(bin_edges)
    return imhist