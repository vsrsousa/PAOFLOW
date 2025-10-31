# paoflow2tb2j - PAOFLOW to TB2J Converter

A standalone tool to convert PAOFLOW Hamiltonian output to TB2J Wannier90 format without modifying PAOFLOW code.

## Why This Tool?

PAOFLOW already writes Hamiltonians in various formats. This standalone converter reads existing PAOFLOW output and converts it to the specific format and naming convention expected by TB2J, avoiding the need to modify PAOFLOW itself.

## Installation

No installation required! This is a standalone Python script.

**Requirements:**
- Python 3.6+
- NumPy
- SciPy (optional, for .npy format conversion)

## Usage

### Quick Start

```bash
# Convert from PAOFLOW write_Hamiltonian() output
python paoflow2tb2j.py --input output/ --input-prefix hamiltonian.dat --output-prefix Fe

# Convert from binary .npy files
python paoflow2tb2j.py --input output/ --format npy --nk 12 12 12 --output-prefix Fe
```

### Workflow

#### Step 1: Generate Hamiltonian with PAOFLOW

**For VASP:**
```python
from PAOFLOW import PAOFLOW

paoflow = PAOFLOW(savedir='./nscf_nspin2/', outputdir='./output/', dft="VASP")
paoflow.projections(basispath='../BASIS/', configuration={'Fe':['3D','4S','4P']})
paoflow.projectability()
paoflow.pao_hamiltonian()

# Write Hamiltonian in real space (recommended for TB2J)
paoflow.write_Hamiltonian('hamiltonian.dat')
paoflow.finish_execution()
```

**For Quantum ESPRESSO:**
```python
from PAOFLOW import PAOFLOW

paoflow = PAOFLOW.PAOFLOW(savedir='fe.save', outputdir='output/', dft='QE')
paoflow.read_atomic_proj_QE()
paoflow.projectability()
paoflow.pao_hamiltonian()

# Write Hamiltonian in real space
paoflow.write_Hamiltonian('hamiltonian.dat')
paoflow.finish_execution()
```

This creates files in `output/`:
- `hamiltonian.dat_0` (spin-up)
- `hamiltonian.dat_1` (spin-down)

#### Step 2: Convert to TB2J Format

```bash
python paoflow2tb2j.py --input output/ \
                       --input-prefix hamiltonian.dat \
                       --output-prefix Fe
```

This creates TB2J-compatible files:
- `Fe.up_hr.dat` (spin-up)
- `Fe.dn_hr.dat` (spin-down)

#### Step 3: Use with TB2J

```bash
wann2J --path output/ \
       --prefix_up Fe.up \
       --prefix_down Fe.dn \
       --posfile POSCAR \
       --elements Fe \
       --efermi 0.0 \
       --kmesh 10 10 10
```

## Command-Line Options

```
usage: paoflow2tb2j.py [-h] --input INPUT [--input-prefix INPUT_PREFIX]
                       [--output-prefix OUTPUT_PREFIX] [--format {hr,npy}]
                       [--nk NK1 NK2 NK3]

optional arguments:
  -h, --help            show this help message and exit
  --input, -i INPUT     Input directory containing PAOFLOW output
  --input-prefix, -p INPUT_PREFIX
                        Prefix of PAOFLOW Hamiltonian files (default: hamiltonian.dat)
  --output-prefix, -o OUTPUT_PREFIX
                        Prefix for TB2J output files (default: tb2j)
  --format, -f {hr,npy}
                        Input format: hr (write_Hamiltonian output) or npy (write_binary output)
  --nk NK1 NK2 NK3      k-point grid dimensions (required for --format npy)
```

## Input Formats

### Format 1: Real-space Hamiltonian (Recommended)

From `paoflow.write_Hamiltonian()`:
- Already in Wannier90 format
- Files: `{prefix}_0`, `{prefix}_1` (spin-polarized) or `{prefix}` (non-spin-polarized)
- This is the easiest format to convert

### Format 2: Binary k-space Hamiltonian

From `paoflow.pao_hamiltonian(write_binary=True)` with `acbn0=True`:
- Files: `kham_up.npy`, `kham_dn.npy`
- Requires k-point grid dimensions via `--nk`
- Converter performs Fourier transform to real space

## Examples

### Example 1: Convert Real-Space Hamiltonian

```bash
# PAOFLOW output in output/ directory
# Files: hamiltonian.dat_0, hamiltonian.dat_1

python paoflow2tb2j.py --input output/ \
                       --input-prefix hamiltonian.dat \
                       --output-prefix FeCo

# Creates: FeCo.up_hr.dat, FeCo.dn_hr.dat
```

### Example 2: Convert Binary Files

```bash
# PAOFLOW output with write_binary=True
# Files: kham_up.npy, kham_dn.npy
# k-mesh: 12x12x12

python paoflow2tb2j.py --input output/ \
                       --format npy \
                       --nk 12 12 12 \
                       --output-prefix FeCo

# Creates: FeCo.up_hr.dat, FeCo.dn_hr.dat
```

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

For spin-polarized calculations:
- `{prefix}.up_hr.dat` - Spin-up channel
- `{prefix}.dn_hr.dat` - Spin-down channel

For non-spin-polarized:
- `{prefix}_hr.dat` - Single Hamiltonian

## Advantages of Standalone Approach

1. **No PAOFLOW modifications**: Works with any PAOFLOW version
2. **Flexible**: Convert existing output without re-running PAOFLOW
3. **Reusable**: Keep converter separate from main PAOFLOW codebase
4. **Maintainable**: Easy to update if TB2J format changes

## Technical Details

- The converter reads PAOFLOW's Wannier90-format output
- For spin-polarized calculations, it renames files to TB2J convention
- For binary files, it performs Fourier transform from k-space to real-space
- Grid padding ensures odd dimensions as required by many tight-binding codes

## Troubleshooting

**Error: "Could not find PAOFLOW Hamiltonian files"**
- Check that PAOFLOW ran successfully
- Verify the correct output directory and prefix
- Ensure you called `paoflow.write_Hamiltonian()` in your PAOFLOW script

**Error: "Must specify k-point grid dimensions"**
- When using `--format npy`, you must provide `--nk NK1 NK2 NK3`
- Get these values from your PAOFLOW input or output

## References

- PAOFLOW: https://github.com/marcobn/PAOFLOW
- TB2J: https://github.com/mailhexu/TB2J
- Wannier90: http://www.wannier.org/

## License

GNU General Public License v3.0 (same as PAOFLOW)
