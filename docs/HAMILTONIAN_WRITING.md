# PAOFLOW Hamiltonian Writing Documentation

## Overview

PAOFLOW creates tight-binding Hamiltonians from DFT calculations and can write them to files in various formats. This document describes all methods for writing Hamiltonians, with special focus on spin-dependent components.

## Hamiltonian Generation

The tight-binding Hamiltonian is constructed using:

```python
paoflow.pao_hamiltonian()
```

This creates:
- `Hks`: Hamiltonian in k-space (shape: `[nawf, nawf, nk1, nk2, nk3, nspin]`)
- `HRs`: Hamiltonian in real space (obtained by Fourier transform)

Where:
- `nawf`: Number of Wannier functions
- `nk1, nk2, nk3`: k-point grid dimensions
- `nspin`: Number of spin channels (1 or 2)

## Writing Methods

### 1. ACBN0 Format (K-space)

**Method**: `write_Hk_acbn0()`

**When called**: Automatically when `acbn0=True` is set in PAOFLOW initialization

**Output files**:

For `nspin=1` (non-spin-polarized):
- `kham.txt` or `kham.npy`: Hamiltonian in k-space
- `kovp.txt` or `kovp.npy`: Overlap matrix (if `acbn0=True`)
- `k.txt`: k-points
- `wk.txt`: k-point weights

For `nspin=2` (spin-polarized):
- `kham_up.txt` or `kham_up.npy`: Spin-up Hamiltonian
- `kham_down.txt` or `kham_dn.npy`: Spin-down Hamiltonian
- `kovp.txt` or `kovp.npy`: Overlap matrix (if `acbn0=True`)
- `k.txt`: k-points
- `wk.txt`: k-point weights

**Format**: Complex numbers written as real and imaginary parts
**Binary option**: Use `write_binary=True` in `pao_hamiltonian()` for `.npy` files

### 2. Z2Pack/Wannier90 Format (Real space)

**Method**: `paoflow.write_Hamiltonian(fname='hamiltonian.dat')`

**Output files**:

For `nspin=1`:
- `{fname}`: Single Hamiltonian file

For `nspin=2`:
- `{fname}_0`: Spin-up Hamiltonian
- `{fname}_1`: Spin-down Hamiltonian

**Format**: Wannier90 `_hr.dat` format (real-space Hamiltonian)

```
Header comment
<number of Wannier functions>
<number of R vectors>
<degeneracy weights for each R vector>
<Rx> <Ry> <Rz> <orb_i> <orb_j> <Re[H(R)_ij]> <Im[H(R)_ij]>
...
```

**Usage**:
```python
paoflow.pao_hamiltonian()
paoflow.write_Hamiltonian('my_hamiltonian.dat')
```

### 3. TB2J Format (Real space, spin-labeled)

**Method**: `paoflow.write_Hamiltonian_TB2J(prefix='paoflow')`

**Output files**:

For `nspin=1`:
- `{prefix}_hr.dat`: Single Hamiltonian

For `nspin=2`:
- `{prefix}.up_hr.dat`: Spin-up Hamiltonian
- `{prefix}.dn_hr.dat`: Spin-down Hamiltonian

**Format**: Same as Wannier90 `_hr.dat` format, but with naming convention expected by TB2J

**Usage**:
```python
paoflow.pao_hamiltonian()
paoflow.write_Hamiltonian_TB2J(prefix='MyMaterial')
```

**TB2J Integration**:
```bash
wann2J --path ./output/ \
       --prefix_up MyMaterial.up \
       --prefix_down MyMaterial.dn \
       --posfile POSCAR \
       --elements Fe \
       --efermi 0.0 \
       --kmesh 10 10 10
```

### 4. BoltzTraP2 Format

**Method**: `write4bt2(data_controller)`

This is a lower-level function that writes:
- `{prefix}.energy`: Energy eigenvalues
- `{prefix}.structure`: Crystal structure

Note: This format does NOT include full Hamiltonian matrix elements, only eigenvalues.

## Spin Component Summary

| Method | nspin=1 | nspin=2 |
|--------|---------|---------|
| `write_Hk_acbn0()` | `kham.txt` | `kham_up.txt`, `kham_down.txt` |
| `write_Hamiltonian()` | `{fname}` | `{fname}_0`, `{fname}_1` |
| `write_Hamiltonian_TB2J()` | `{prefix}_hr.dat` | `{prefix}.up_hr.dat`, `{prefix}.dn_hr.dat` |

## Key Routines

1. **`do_build_pao_hamiltonian.py`**: Constructs the PAO Hamiltonian from DFT projections
   - `build_Hks()`: Builds Hamiltonian in k-space
   - `do_Hks_to_HRs()`: Fourier transforms to real space

2. **`DataController.write_Hk_acbn0()`**: Writes k-space Hamiltonian and overlap matrix

3. **`DataController.write_HRs()`**: Writes real-space Hamiltonian in Z2Pack format

4. **`DataController.write_HRs_TB2J()`**: Writes real-space Hamiltonian in TB2J format

## Example: Complete Workflow for TB2J

```python
from PAOFLOW import PAOFLOW

# Initialize with spin-polarized calculation
paoflow = PAOFLOW(savedir='./nscf_nspin2/',  
                  outputdir='./output/', 
                  verbose=True,
                  dft="VASP")

# Setup basis projections (for VASP)
basis_path = '../../../BASIS/'
basis_config = {'Fe': ['3D', '4S', '4P']}
paoflow.projections(basispath=basis_path, configuration=basis_config)

# Build Hamiltonian
paoflow.projectability()
paoflow.pao_hamiltonian()

# Export for TB2J
paoflow.write_Hamiltonian_TB2J(prefix='Fe')

# This creates:
# - Fe.up_hr.dat (spin-up channel)
# - Fe.dn_hr.dat (spin-down channel)
```

## Technical Details

### K-space vs Real-space

- **K-space (Hks)**: Direct output from DFT projection
  - Shape: `[nawf, nawf, nkpnts, nspin]`
  - Used for band structure calculations
  
- **Real-space (HRs)**: Fourier transform of Hks
  - Shape: `[nawf, nawf, nk1, nk2, nk3, nspin]`
  - Used for real-space analysis and Wannier-based methods
  - Automatically padded to ensure odd grid dimensions

### Spin Channels

- `nspin=1`: Non-spin-polarized or spin-orbit coupled calculations
- `nspin=2`: Collinear spin-polarized calculations
  - Channel 0: Spin-up
  - Channel 1: Spin-down

### File Formats

**Text format**: Human-readable, larger file size
- Real and imaginary parts on separate lines
- Complex number: `real_part imaginary_part`

**Binary format** (`.npy`): Compact, faster I/O
- NumPy array format
- Load with `np.load(filename)`

## Verification

To verify spin components are correctly separated:

```python
import numpy as np

# Load k-space Hamiltonians
H_up = np.load('output/kham_up.npy')
H_dn = np.load('output/kham_dn.npy')

# Check shapes
print(f"Spin-up shape: {H_up.shape}")
print(f"Spin-down shape: {H_dn.shape}")

# Check if they differ
print(f"Identical: {np.allclose(H_up, H_dn)}")
```

## References

1. PAOFLOW paper: Comp. Mat. Sci. 200, 110828 (2021)
2. TB2J: https://github.com/mailhexu/TB2J
3. Wannier90: http://www.wannier.org/
