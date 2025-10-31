# PAOFLOW to TB2J Integration

This directory contains examples and tools for converting PAOFLOW tight-binding Hamiltonians to TB2J format for calculating magnetic exchange interactions.

## Approach: Standalone Converter

Instead of modifying PAOFLOW code, we use a **standalone converter tool** that reads existing PAOFLOW output and converts it to TB2J format. This approach:

- ✅ Works with any PAOFLOW version (no code modifications needed)
- ✅ Converts existing output without re-running PAOFLOW
- ✅ Maintains separation between PAOFLOW and format conversion
- ✅ Easy to maintain and update independently

## Quick Start

### 1. Generate Hamiltonian with PAOFLOW

Use PAOFLOW's existing `write_Hamiltonian()` method:

**For VASP** (see `example_export_for_TB2J.py`):
```python
from PAOFLOW import PAOFLOW

paoflow = PAOFLOW(savedir='./nscf_nspin2/', outputdir='./output/', dft="VASP")
paoflow.projections(basispath='../BASIS/', configuration={'Fe':['3D','4S','4P']})
paoflow.projectability()
paoflow.pao_hamiltonian()
paoflow.write_Hamiltonian('hamiltonian.dat')  # Creates _0 and _1 files
```

**For Quantum ESPRESSO** (see `example_export_QE_for_TB2J.py`):
```python
from PAOFLOW import PAOFLOW

paoflow = PAOFLOW.PAOFLOW(savedir='fe.save', outputdir='output/', dft='QE')
paoflow.read_atomic_proj_QE()
paoflow.projectability()
paoflow.pao_hamiltonian()
paoflow.write_Hamiltonian('hamiltonian.dat')  # Creates _0 and _1 files
paoflow.finish_execution()
```

### 2. Convert to TB2J Format

Use the standalone converter tool:

```bash
cd ../../tools/paoflow2tb2j
python paoflow2tb2j.py --input ../../examples/TB2J_example/output/ \
                       --input-prefix hamiltonian.dat \
                       --output-prefix Fe
```

This creates TB2J-compatible files:
- `Fe.up_hr.dat` (spin-up)
- `Fe.dn_hr.dat` (spin-down)

### 3. Use with TB2J

```bash
wann2J --path output/ \
       --prefix_up Fe.up \
       --prefix_down Fe.dn \
       --posfile POSCAR \
       --elements Fe \
       --efermi 0.0 \
       --kmesh 10 10 10
```

## Files in This Directory

- **`example_export_for_TB2J.py`** - VASP example
- **`example_export_QE_for_TB2J.py`** - Quantum ESPRESSO example
- **`README.md`** - This file

## Converter Tool

The standalone converter is located in `../../tools/paoflow2tb2j/`:

- **`paoflow2tb2j.py`** - Main converter script
- **`README.md`** - Detailed usage instructions

See `../../tools/paoflow2tb2j/README.md` for complete documentation.

## Workflow Summary

```
┌─────────────────┐
│   PAOFLOW       │
│ (existing code) │
└────────┬────────┘
         │ write_Hamiltonian()
         ▼
┌─────────────────┐
│ hamiltonian_0   │ (spin-up, Wannier90 format)
│ hamiltonian_1   │ (spin-down, Wannier90 format)
└────────┬────────┘
         │ paoflow2tb2j.py
         ▼
┌─────────────────┐
│  Fe.up_hr.dat   │ (TB2J naming)
│  Fe.dn_hr.dat   │ (TB2J naming)
└────────┬────────┘
         │ wann2J
         ▼
┌─────────────────┐
│   TB2J Output   │ (Exchange interactions)
└─────────────────┘
```

## TB2J Command Reference

Key points for TB2J usage:
- `--prefix_up` and `--prefix_down`: Use the prefix without `_hr.dat` extension
- TB2J automatically looks for `{prefix_up}_hr.dat` and `{prefix_down}_hr.dat`
- `--elements`: Specify the magnetic elements in your system
- `--efermi`: Fermi energy in eV (usually 0 if shifted in PAOFLOW)
- `--kmesh`: k-point mesh for integration

## Output Format

The converter creates files in Wannier90 `_hr.dat` format:

```
PAOFLOW to TB2J Converter
<number of Wannier functions>
<number of R vectors>
<degeneracy weights>
<Rx> <Ry> <Rz> <i> <j> <Re[H(R)_ij]> <Im[H(R)_ij]>
...
```

## Spin Components

- **nspin=1** (non-spin-polarized): Single file `{prefix}_hr.dat`
- **nspin=2** (spin-polarized): Two files
  - `{prefix}.up_hr.dat` for spin-up channel
  - `{prefix}.dn_hr.dat` for spin-down channel

## Technical Notes

1. PAOFLOW's `write_Hamiltonian()` already outputs in Wannier90 format
2. The converter mainly renames files to TB2J's expected convention
3. For binary `.npy` files, the converter also performs Fourier transform
4. The Hamiltonian is in real space (HRs), obtained by FFT from k-space
5. Grid is automatically padded to ensure odd dimensions

## References

- PAOFLOW: https://github.com/marcobn/PAOFLOW
- TB2J: https://github.com/mailhexu/TB2J
- Wannier90: http://www.wannier.org/
