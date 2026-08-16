#!/usr/bin/env python3
"""arap.py — As-Rigid-As-Possible image deformation, clean-room.

The same deformation family Adobe Photoshop's Puppet Warp uses (ARAP,
Sorkine & Alexa 2007). Implemented from the published method, not from any
repo's code:

  1. Delaunay triangular mesh over the character's bounding box.
  2. Cotangent-weighted Laplacian.
  3. Two-step ARAP solve: local rotations (SVD) + global sparse solve
     with pinned handles (joints) held at target positions.
  4. Per-triangle affine warp of the image (barycentric sampling).

Handles: anchor pins hold the body still; moving pins (joints, dragged
parts) drive the deformation. Used by both the puppet mode (manual pins)
and the mocap mode (BVH joints) of ae-motion — ONE engine, both jobs.
"""

from __future__ import annotations

import numpy as np
from PIL import Image
from scipy.spatial import Delaunay
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve


# ------------------------------------------------------------------ mesh
def mesh_rect(width, height, delta):
    """Vertices (n,2) int + faces (m,3) int over a [0,width]x[0,height] box."""
    xs = np.arange(0, width + delta, delta, dtype=float)
    ys = np.arange(0, height + delta, delta, dtype=float)
    xs = np.clip(xs, 0, width)
    ys = np.clip(ys, 0, height)
    gx, gy = np.meshgrid(xs, ys)
    inner = np.column_stack((gx.ravel(), gy.ravel()))
    # border points at delta/2 spacing for a denser rim
    bx = np.arange(delta / 2, width, delta)
    by = np.arange(delta / 2, height, delta)
    rim = []
    for x in bx:
        rim.append((x, 0.0)); rim.append((x, height))
    for y in by:
        rim.append((0.0, y)); rim.append((width, y))
    corners = [(0.0, 0.0), (width, 0.0), (0.0, height), (width, height)]
    points = np.vstack([inner, np.array(rim), np.array(corners)])
    points = np.unique(np.round(points, 2), axis=0)
    tri = Delaunay(points)
    return points.astype(np.float64), tri.simplices.astype(np.int64)


# ------------------------------------------------------------ laplacian
def cotangent_laplacian(verts, faces):
    """Cotangent-weighted Laplacian (n,n) sparse matrix."""
    n = len(verts)
    rows, cols, vals = [], [], []
    for a, b, c in faces:
        for (i, j, k) in ((a, b, c), (b, c, a), (c, a, b)):
            e1 = verts[j] - verts[i]
            e2 = verts[k] - verts[i]
            cot = float(np.dot(e1, e2) / max(1e-9, abs(np.cross(e1, e2))))
            w = 0.5 * cot
            rows += [i, j]
            cols += [j, i]
            vals += [-w, -w]
            rows.append(i); cols.append(i); vals.append(w)
    L = coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
    return L


def _rot2(cov):
    """Best-fit 2D rotation from a covariance matrix (Kabsch, 2x2)."""
    u, _, vt = np.linalg.svd(cov)
    r = u @ vt
    if np.linalg.det(r) < 0:
        u[:, -1] *= -1
        r = u @ vt
    return r


def arap_solve(verts, faces, handles, targets, iterations=4):
    """Two-step ARAP, vectorised. handles: indices; targets: (h,2).
    Returns deformed vertices (n,2)."""
    n = len(verts)
    L = cotangent_laplacian(verts, faces)

    # edge list (i, j, w) with cotangent weights
    rows, cols = L.nonzero()
    edges = np.array([[i, j, -L[i, j]] for i, j in zip(rows, cols)
                      if i < j], dtype=np.float64)
    ei = edges[:, 0].astype(int)
    ej = edges[:, 1].astype(int)
    w = edges[:, 2]

    p = verts.copy()
    p0 = verts.copy()
    rot = np.repeat(np.eye(2)[None], n, axis=0)

    # per-edge rest vectors (constant)
    e0 = p0[ei] - p0[ej]                       # (E,2)

    for _ in range(iterations):
        # --- local step (vectorised) ---
        e1 = p[ei] - p[ej]                     # (E,2)
        cov = np.einsum("e,ei,ej->eij", w, e1, e0)
        acc = np.zeros((n, 2, 2))
        np.add.at(acc, ei, cov)
        np.add.at(acc, ej, cov)
        u, _, vt = np.linalg.svd(acc)
        r = u @ vt
        det = np.linalg.det(r)
        fix = det < 0
        if fix.any():
            u[fix, :, 1] *= -1
            r = u @ vt
        rot = r

        # --- global step (vectorised) ---
        r_avg = 0.5 * (rot[ei] + rot[ej])      # (E,2,2)
        contrib = w[:, None] * np.einsum("eij,ej->ei", r_avg, e0)
        b = np.zeros((n, 2))
        np.add.at(b, ei, contrib)
        np.add.at(b, ej, -contrib)

        # pin handles
        Lp = L.tolil(copy=True)
        for h_idx, target in zip(handles, targets):
            Lp[h_idx] = 0
            Lp[h_idx, h_idx] = 1
            b[h_idx] = target
        p = spsolve(Lp.tocsr(), b)
    return np.asarray(p)


# ------------------------------------------------------------ image warp
def warp_image(img, src_verts, faces, dst_verts, bg=(255, 255, 255)):
    """Full-frame vectorised triangle warp via Delaunay point location.

    For every output pixel, find the destination triangle it falls in
    (scipy's C-accelerated find_simplex), recover its barycentric
    coordinates from the simplex transforms, and gather the same point
    from the matching source triangle. O(H*W) in numpy — no Python
    triangle loop."""
    h, w = img.shape[:2]
    ch = img.shape[2] if img.ndim == 3 else 1
    flat = img.reshape(h * w, -1) if img.ndim == 3 else img.ravel()
    out = np.full((h, w, max(ch, 1)),
                  np.array(bg, dtype=np.float64) if ch > 1 else float(bg[0]),
                  dtype=np.float64)
    ys, xs = np.mgrid[0:h, 0:w]
    pts = np.column_stack((xs.ravel().astype(np.float64),
                           ys.ravel().astype(np.float64)))

    tri = Delaunay(dst_verts)
    simplex = tri.find_simplex(pts)          # (H*W,) triangle id per pixel
    valid = simplex >= 0
    if not valid.any():
        out = np.clip(out, 0, 255).astype(np.uint8)
        return out if ch > 1 else out[:, :, 0]

    vid = valid.nonzero()[0]
    sid = simplex[vid]
    px = pts[vid, 0]
    py = pts[vid, 1]

    # barycentric coordinates of each pixel in its destination triangle
    # (closed-form, fully vectorised)
    tris = tri.simplices[sid]                # (V,3) vertex ids in dst mesh
    dv = dst_verts[tris]                     # (V,3,2)
    v0, v1, v2 = dv[:, 0], dv[:, 1], dv[:, 2]
    den = ((v1[:, 1] - v2[:, 1]) * (v0[:, 0] - v2[:, 0]) +
           (v2[:, 0] - v1[:, 0]) * (v0[:, 1] - v2[:, 1]))
    safe = np.where(np.abs(den) < 1e-9, 1e-9, den)
    b1 = ((v1[:, 1] - v2[:, 1]) * (px - v2[:, 0]) +
          (v2[:, 0] - v1[:, 0]) * (py - v2[:, 1])) / safe
    b2 = ((v2[:, 1] - v0[:, 1]) * (px - v2[:, 0]) +
          (v0[:, 0] - v2[:, 0]) * (py - v2[:, 1])) / safe
    b0 = 1.0 - b1 - b2

    s = src_verts[tris]                      # (V,3,2) source tri verts
    sx = b0 * s[:, 0, 0] + b1 * s[:, 1, 0] + b2 * s[:, 2, 0]
    sy = b0 * s[:, 0, 1] + b1 * s[:, 1, 1] + b2 * s[:, 2, 1]
    six = np.clip(np.round(sx).astype(int), 0, w - 1)
    siy = np.clip(np.round(sy).astype(int), 0, h - 1)
    src_idx = siy * w + six

    if ch > 1:
        out_flat = out.reshape(h * w, -1)
        out_flat[vid] = flat[src_idx]
    else:
        out_flat = out.reshape(h * w)
        out_flat[vid] = flat[src_idx]
    out = np.clip(out, 0, 255).astype(np.uint8)
    return out if ch > 1 else out[:, :, 0]


def deform_image(img, pins, targets, delta=18, anchor_rim=True,
                 bg=(255, 255, 255)):
    """One-shot ARAP deformation of an image array (RGB or RGBA).
    pins: [(x,y)...] source pin positions (in image px).
    targets: [(x,y)...] new pin positions.
    anchor_rim: fix mesh border so the drawing does not slide.
    bg: fill colour for pixels dragged in from outside (per-channel).
    """
    h, w = img.shape[:2]
    verts, faces = mesh_rect(w, h, delta)
    # nearest mesh vertex for each pin
    handle_idx = []
    for x, y in pins:
        d = (verts[:, 0] - x) ** 2 + (verts[:, 1] - y) ** 2
        handle_idx.append(int(np.argmin(d)))
    # rim anchors (border vertices stay fixed)
    anchors = []
    atargets = []
    if anchor_rim:
        for i, (x, y) in enumerate(verts):
            if (x <= 0.6 or x >= w - 0.6 or y <= 0.6 or y >= h - 0.6):
                anchors.append(i)
                atargets.append([x, y])
    all_idx = np.array(handle_idx + anchors, dtype=int)
    all_tgt = np.vstack([np.asarray(targets, float), np.asarray(atargets, float)])
    new_verts = arap_solve(verts, faces, all_idx, all_tgt)
    return warp_image(img, verts, faces, new_verts, bg=bg)
