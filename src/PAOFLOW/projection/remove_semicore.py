"""Helpers to remove semicore bands from projection data.

This module provides a utility to drop selected DFT bands (e.g. deep
semicore states) from the projection arrays (`U`, `my_eigsmat`) before
running the PAO Hamiltonian construction.

The function updates `data_controller.data_arrays` and
`data_controller.data_attributes` in-place.
"""
from __future__ import annotations

from typing import Iterable, Optional
import re

import numpy as np


def remove_semicore_states(
    data_controller,
    *,
    energy_cut: Optional[float] = None,
    band_indices: Optional[Iterable[int]] = None,
    strategy: str = "avg",
    verbose: bool = True,
):
    """Remove bands from `U` and `my_eigsmat`.

    Parameters
    ----------
    data_controller : DataController
        The project's `DataController` instance.
    energy_cut : float, optional
        If provided, bands whose representative energy is <= `energy_cut`
        are removed. Representative energy is computed per `strategy`.
    band_indices : iterable of int, optional
        Explicit global band indices to remove (0-based). If provided,
        `energy_cut` is ignored.
    strategy : {'avg','max','min'}
        When `energy_cut` is used, choose how to compute the band energy
        across k-points: average, maximum or minimum of `my_eigsmat[b]`.
    verbose : bool
        Print brief status messages.

    Notes
    -----
    - Expects `arrays['U']` shape `(nawf, nbnds, nkpnts, nspin)` and
      `arrays['my_eigsmat']` shape `(nbnds, nkpnts, nspin)`.
    - Updates `attributes['nbnds']` and, if present, clamps `attributes['bnd']`.
    - Does NOT attempt to update any already-built `Hks`, `HRs`, etc.; call
      this helper before building PAO Hamiltonian.
    """
    arrays, attr = data_controller.data_dicts()

    if 'U' not in arrays or 'my_eigsmat' not in arrays:
        raise KeyError('Required arrays `U` and `my_eigsmat` not found.')

    U = arrays['U']
    my_eigsmat = arrays['my_eigsmat']

    if U.ndim != 4 or my_eigsmat.ndim != 3:
        raise ValueError('Unexpected shapes for `U` or `my_eigsmat`.')

    # Determine axis ordering: `U` can be (nawf, nbnds, nkpnts, nspin)
    # or (nbnds, nawf, nkpnts, nspin). Use attributes when available.
    nbnds_attr = int(attr.get('nbnds', my_eigsmat.shape[0]))
    nawf_attr = int(attr.get('nawf', U.shape[1] if U.shape[0] == nbnds_attr else U.shape[0]))
    nkpnts_attr = int(attr.get('nkpnts', my_eigsmat.shape[1]))

    # locate axes
    axis_candidates = {0: U.shape[0], 1: U.shape[1], 2: U.shape[2], 3: U.shape[3]}
    # find band axis (matches nbnds_attr)
    band_axes = [ax for ax, s in axis_candidates.items() if s == nbnds_attr]
    if not band_axes:
        # fallback: if nbnds_attr not reliable, assume axis 0 is nawf and axis1 is nbnds
        band_axis = 1
    else:
        band_axis = band_axes[0]

    # find nawf axis
    nawf_axes = [ax for ax, s in axis_candidates.items() if s == nawf_attr and ax != band_axis]
    nawf_axis = nawf_axes[0] if nawf_axes else (0 if band_axis == 1 else 1)

    # nkpnts axis should be axis with size matching my_eigsmat.shape[1]
    nk_axes = [ax for ax, s in axis_candidates.items() if s == my_eigsmat.shape[1]]
    nk_axis = nk_axes[0] if nk_axes else 2

    nspin = U.shape[3]

    if band_indices is not None:
        remove_idx = sorted(set(int(i) for i in band_indices if 0 <= int(i) < my_eigsmat.shape[0]))
    elif energy_cut is not None:
        # Collapse spin by taking average over spin channels
        if nspin > 1:
            eigs = np.mean(my_eigsmat, axis=2)
        else:
            eigs = my_eigsmat[..., 0]

        if strategy == 'avg':
            band_rep = np.mean(eigs, axis=1)
        elif strategy == 'max':
            band_rep = np.max(eigs, axis=1)
        elif strategy == 'min':
            band_rep = np.min(eigs, axis=1)
        else:
            raise ValueError('Unknown strategy: %s' % strategy)

        remove_idx = [int(i) for i, e in enumerate(band_rep) if e <= energy_cut]
    else:
        raise ValueError('Either `energy_cut` or `band_indices` must be provided.')

    if len(remove_idx) == 0:
        if verbose:
            print('remove_semicore_states: no bands selected for removal.')
        return

    # compute keep indices relative to my_eigsmat/band numbering
    nbnds_old = my_eigsmat.shape[0]
    keep_bands = [i for i in range(nbnds_old) if i not in remove_idx]

    # Update my_eigsmat by selecting remaining bands (axis 0)
    my_eigsmat_new = my_eigsmat[keep_bands, :, :].copy()

    # Update U by removing along the band axis we detected
    slicer = [slice(None)] * 4
    # Use np.take to select keep indices along band_axis
    U_new = np.take(U, keep_bands, axis=band_axis).copy()

    arrays['U'] = U_new
    arrays['my_eigsmat'] = my_eigsmat_new

    # Update attributes: nbnds reduced by number removed
    old_nbnds = int(attr.get('nbnds', nbnds_old))
    new_nbnds = my_eigsmat_new.shape[0]
    attr['nbnds'] = new_nbnds
    if 'bnd' in attr and attr['bnd'] > attr['nbnds']:
        if verbose:
            print('Clamping attribute `bnd` from %d to %d' % (attr['bnd'], attr['nbnds']))
        attr['bnd'] = attr['nbnds']

    if verbose:
        print(
            'remove_semicore_states: removed %d bands (indices=%s); nbnds: %d -> %d'
            % (len(remove_idx), remove_idx, old_nbnds, attr['nbnds'])
        )

    # Optionally remove semicore orbitals from the PAO basis itself if a
    # mapping is present in attributes (e.g. {'Fe': ['3D','3P']}). This
    # updates arrays['basis'] and reduces the nawf dimension of `U`.
    semicfg = attr.get('semicore_orbitals') or attr.get('nosemicore_orbitals')
    if semicfg:
        basis = arrays.get('basis')
        if basis is None:
            if verbose:
                print('remove_semicore_states: semicore orbitals requested but `basis` not available; skipping orbital removal')
        else:
            # Identify orbital indices to remove
            orb_remove = []
            for i, b in enumerate(basis):
                atom = re.split(r'\d+', b.get('atom', ''))[0]
                lab = b.get('label', '').strip()
                if len(lab) == 2:
                    lab = lab[0] + lab[1].upper()
                labs = semicfg.get(atom, [])
                if lab in labs:
                    orb_remove.append(i)

            if len(orb_remove) == 0:
                if verbose:
                    print('remove_semicore_states: no matching orbitals found in basis; skipping orbital removal')
            else:
                orb_remove = sorted(set(orb_remove))
                # build keep list for orbitals
                nawf_old = len(basis)
                keep_orbs = [i for i in range(nawf_old) if i not in orb_remove]

                # remove orbitals from basis and store
                basis_new = [basis[i] for i in keep_orbs]
                arrays['basis'] = basis_new

                # remove orbitals from U along detected nawf axis
                U_after_orb = np.take(U_new if 'U_new' in locals() else U, keep_orbs, axis=nawf_axis)

                # also update Dnm if present using new basis
                if 'Dnm' in arrays:
                    Dnm = np.empty((len(basis_new), len(basis_new), 3))
                    for ii in range(len(basis_new)):
                        for jj in range(len(basis_new)):
                            for k in range(3):
                                Dnm[ii, jj, k] = basis_new[ii]['tau'][k] - basis_new[jj]['tau'][k]
                    arrays['Dnm'] = Dnm

                # replace U in arrays with orbital-reduced version
                arrays['U'] = U_after_orb

                # update attribute nawf
                old_nawf = int(attr.get('nawf', nawf_old))
                attr['nawf'] = len(basis_new)
                if verbose:
                    print('remove_semicore_states: removed %d orbitals (indices=%s); nawf: %d -> %d' % (len(orb_remove), orb_remove, old_nawf, attr['nawf']))

                # Recompute shells and jchia metadata from the new basis so
                # downstream symmetry machinery (pao_sym) builds consistent
                # rotation blocks. This mirrors the construction in
                # `build_pswfc_basis_all`.
                try:
                    atoms_list = arrays.get('atoms', [])
                    shells_new = {}
                    jchia_new = {}
                    for at in atoms_list:
                        # collect basis entries for this atom in order
                        entries = [b for b in basis_new if b.get('atom') == at]
                        if len(entries) == 0:
                            continue
                        a_shells = []
                        last_label = None
                        for b in entries:
                            lab = b.get('label', '')
                            if lab != last_label:
                                # deduce angular momentum from label (SPDF)
                                try:
                                    l = 'SPDF'.find(lab[1].upper())
                                except Exception:
                                    l = b.get('l', None)
                                if l is None or l == -1:
                                    # fallback: skip malformed label
                                    last_label = lab
                                    continue
                                a_shells.append(l)
                                last_label = lab

                        if len(a_shells) > 0:
                            shells_new[at] = a_shells
                            # reconstruct jchia entry the same way as in the
                            # original builder so spin-orbit indices align
                            if attr.get('dftSO'):
                                jchi = []
                                s = 0.5
                                for l in a_shells:
                                    if l == 0:
                                        jchi.append(0.5)
                                        s = 0.5
                                    else:
                                        jchi.append(l - s)
                                        s = -s
                                jchia_new[at] = jchi

                    if shells_new:
                        arrays['shells'] = shells_new
                        if attr.get('dftSO'):
                            arrays['jchia'] = jchia_new
                        if verbose:
                            print('remove_semicore_states: reconstructed shells/jchia for symmetry from reduced basis')
                except Exception as e:
                    if verbose:
                        print('remove_semicore_states: failed to rebuild shells/jchia:', e)

    # Note: higher-level arrays (Hks, HRs, etc.) that depend on the original
    # bandset must be rebuilt by the caller.


__all__ = ['remove_semicore_states']


def mask_orbitals_by_band_threshold(
    data_controller, *, threshold=0.05, mode='max', verbose=True
):
    """Mask (zero) orbital contributions per (orbital,band) when they are
    weak across all k-points.

    Rule implemented: for each orbital i and band n compute the per-k
    contribution c_k = sum_sigma |U_{i n k sigma}|^2. If ``mode=='max'``
    and max_k c_k <= threshold the orbital is considered insignificant for
    that band and all U_{i n k sigma} are set to zero. ``mode=='mean'``
    uses the k-averaged value instead.

    This implements the behaviour you described: keep the orbital for the
    band if it is significant in any k, otherwise zero it globally (for
    that band).
    """
    arrays, attr = data_controller.data_dicts()

    if 'U' not in arrays:
        raise KeyError('mask_orbitals_by_band_threshold: `U` not found')

    U = arrays['U']

    if U.ndim != 4:
        raise ValueError('mask_orbitals_by_band_threshold: unexpected U.ndim')

    # Detect axis ordering similarly to remove_semicore_states
    nbnds_attr = int(attr.get('nbnds', 0))
    nawf_attr = int(attr.get('nawf', 0))

    axis_candidates = {0: U.shape[0], 1: U.shape[1], 2: U.shape[2], 3: U.shape[3]}
    band_axes = [ax for ax, s in axis_candidates.items() if s == nbnds_attr]
    if band_axes:
        band_axis = band_axes[0]
    else:
        # fallback heuristic
        band_axis = 1

    nawf_axes = [ax for ax, s in axis_candidates.items() if s == nawf_attr and ax != band_axis]
    nawf_axis = nawf_axes[0] if nawf_axes else (0 if band_axis == 1 else 1)

    # canonicalise to (nawf, nbnds, nkpnts, nspin)
    if (nawf_axis, band_axis) == (0, 1):
        Uc = U.copy()
        transposed_back = None
    elif (nawf_axis, band_axis) == (1, 0):
        Uc = np.transpose(U, (1, 0, 2, 3)).copy()
        transposed_back = (1, 0, 2, 3)
    else:
        # attempt a more general permutation
        perm = [nawf_axis, band_axis, 2, 3]
        # fill missing indices
        perm = [p if p in perm else [i for i in range(4) if i not in perm][0] for p in range(4)]
        try:
            Uc = np.transpose(U, tuple(perm)).copy()
            transposed_back = tuple(np.argsort(perm))
        except Exception:
            raise ValueError('mask_orbitals_by_band_threshold: failed to canonicalise U axes')

    nawf, nbnds, nkpnts, nspin = Uc.shape

    masked = 0
    for i in range(nawf):
        for n in range(nbnds):
            # per-k contributions summed over spin
            per_k = np.sum(np.abs(Uc[i, n, :, :]) ** 2, axis=1)
            if mode == 'max':
                val = np.max(per_k) if per_k.size > 0 else 0.0
            elif mode == 'mean':
                val = np.mean(per_k) if per_k.size > 0 else 0.0
            else:
                raise ValueError('Unknown mode: %s' % mode)

            if val <= float(threshold):
                # zero contributions for this orbital/band across all k and spins
                Uc[i, n, :, :] = 0.0
                masked += 1

    # map back to original layout
    if transposed_back is not None:
        U_new = np.transpose(Uc, transposed_back)
    else:
        U_new = Uc

    arrays['U'] = U_new

    # Broadcast updated U so downstream modules see it (best-effort)
    try:
        data_controller.broadcast_single_array('U', dtype=complex, root=0)
    except Exception:
        pass

    if verbose and masked > 0:
        print('mask_orbitals_by_band_threshold: zeroed %d (orbital,band) pairs with threshold=%s' % (masked, threshold))

    return masked
