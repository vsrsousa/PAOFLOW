# PAOFLOW to TB2J Integration Example

This example demonstrates how to export tight-binding Hamiltonians from PAOFLOW for use with TB2J to calculate magnetic exchange interactions.

## Overview

TB2J (Tight-Binding to J) is a tool for calculating magnetic exchange interactions using the magnetic force theorem. It requires tight-binding Hamiltonians in Wannier90 format.

PAOFLOW can export its tight-binding Hamiltonians in a format compatible with TB2J using the `write_Hamiltonian_TB2J()` method.

## Workflow

### 1. Generate Tight-Binding Hamiltonian with PAOFLOW

For a spin-polarized calculation:

```python
from PAOFLOW import PAOFLOW

# Initialize PAOFLOW with your DFT data
paoflow = PAOFLOW(savedir='./nscf_nspin2/',  
                  outputdir='./output_TB2J/', 
                  verbose=True,
                  dft="VASP")  # or "QE" for Quantum ESPRESSO

# Define basis (for VASP)
basis_path = '../../../BASIS/'
basis_config = {'Fe':['3D','4S','4P']}  # Example for Fe
paoflow.projections(basispath=basis_path, configuration=basis_config)

# Build the tight-binding Hamiltonian
paoflow.projectability()
paoflow.pao_hamiltonian()

# Export Hamiltonian in TB2J format
paoflow.write_Hamiltonian_TB2J(prefix='MyMaterial')
```

This will create two files in the `output_TB2J` directory:
- `MyMaterial.up_hr.dat` - Spin-up Hamiltonian
- `MyMaterial.dn_hr.dat` - Spin-down Hamiltonian

### 2. Use with TB2J

Once you have the Hamiltonian files, you can use TB2J to calculate exchange interactions:

```bash
# You need a structure file (POSCAR for VASP, or any ASE-compatible format)
wann2J --path ./output_TB2J/ \
       --prefix_up MyMaterial.up \
       --prefix_down MyMaterial.dn \
       --posfile POSCAR \
       --elements Fe \
       --efermi 0.0 \
       --kmesh 10 10 10
```

Key points:
- `--prefix_up` and `--prefix_down`: Use the prefix without `_hr.dat` extension
- TB2J will automatically look for `{prefix_up}_hr.dat` and `{prefix_down}_hr.dat`
- `--elements`: Specify the magnetic elements in your system
- `--efermi`: Fermi energy (in eV, usually 0 if you shifted it in PAOFLOW)
- `--kmesh`: k-point mesh for integration

## Output Format

The Hamiltonian files are written in Wannier90 `_hr.dat` format:

```
PAOFLOW Generated for TB2J
<number of Wannier functions>
<number of R vectors>
<degeneracy weights>
<Rx> <Ry> <Rz> <i> <j> <Re[H(R)_ij]> <Im[H(R)_ij]>
...
```

## Spin Components

- **nspin=1** (non-spin-polarized): Creates a single file `{prefix}_hr.dat`
- **nspin=2** (spin-polarized): Creates two files:
  - `{prefix}.up_hr.dat` for spin-up channel
  - `{prefix}.dn_hr.dat` for spin-down channel

## Notes

1. The Hamiltonian is written in real space (HRs), which is obtained by Fourier transforming the k-space Hamiltonian (Hks)
2. The code automatically pads the grid to ensure an odd number of points in each direction
3. For TB2J calculations, you typically want a dense k-point mesh in your DFT calculation
4. Make sure your PAOFLOW calculation includes the magnetic atoms in the projection basis

## References

- TB2J: https://github.com/mailhexu/TB2J
- PAOFLOW: https://github.com/marcobn/PAOFLOW
