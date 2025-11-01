#!/usr/bin/env python3
"""
paoflow2tb2j - Standalone converter for PAOFLOW Hamiltonians to TB2J format

This script reads Hamiltonian output from PAOFLOW and converts it to the
Wannier90 format expected by TB2J for calculating magnetic exchange interactions.

Author: PAOFLOW Development Team
License: GNU General Public License v3.0
"""

import numpy as np
import argparse
import os
import sys
from pathlib import Path


def zero_pad(HR, nk1, nk2, nk3, pad1, pad2, pad3):
    """
    Zero-pad the Hamiltonian in real space to ensure odd grid dimensions.
    
    Args:
        HR: Hamiltonian array in real space
        nk1, nk2, nk3: Original grid dimensions
        pad1, pad2, pad3: Padding amounts for each dimension
        
    Returns:
        Padded Hamiltonian array
    """
    from scipy import fftpack as FFT
    
    # Pad in k-space
    HK = FFT.fftn(HR, axes=(0, 1, 2))
    HK_padded = np.zeros((nk1+pad1, nk2+pad2, nk3+pad3), dtype=complex)
    
    # Copy data
    HK_padded[:nk1, :nk2, :nk3] = HK
    
    # Back to real space
    HR_padded = FFT.ifftn(HK_padded, axes=(0, 1, 2))
    
    return HR_padded


def write_wannier90_hr(HRS, nk1, nk2, nk3, nawf, ispin, f, header="PAOFLOW to TB2J Converter"):
    """
    Write Hamiltonian in Wannier90 _hr.dat format compatible with TB2J.
    
    Args:
        HRS: Real-space Hamiltonian array
        nk1, nk2, nk3: Grid dimensions
        nawf: Number of Wannier functions
        ispin: Spin index
        f: File handle to write to
        header: Header string for the file
        
    Note:
        TB2J divides all matrix elements by 2.0 when reading, so we multiply by 2.0 when writing.
    """
    nkpts = nk1 * nk2 * nk3
    f.write(header + "\n")
    f.write('%5d \n' % nawf)
    f.write('%5d \n' % nkpts)
    
    # Write degeneracy weights (all 1 for uniform grid)
    nl = 15
    nlines = nkpts // nl
    nlast = nkpts % nl
    
    for j in range(nlines):
        f.write("1 " * nl)
        f.write("\n")
    f.write("1 " * nlast)
    f.write("\n")
    
    # Write Hamiltonian matrix elements
    # Multiply by 2.0 to compensate for TB2J's division by 2.0 when reading
    for i in range(nk1):
        for j in range(nk2):
            for k in range(nk3):
                Rx = float(i) / float(nk1)
                Ry = float(j) / float(nk2)
                Rz = float(k) / float(nk3)
                
                # Shift to [-0.5, 0.5)
                if Rx >= 0.5: Rx = Rx - 1.0
                if Ry >= 0.5: Ry = Ry - 1.0
                if Rz >= 0.5: Rz = Rz - 1.0
                
                # Convert to integer R vectors
                ix = -round(Rx * nk1, 0)
                iy = -round(Ry * nk2, 0)
                iz = -round(Rz * nk3, 0)
                
                for m in range(nawf):
                    for l in range(nawf):
                        # Multiply by 2.0 for TB2J compatibility
                        f.write('%3d %3d %3d %5d %5d %28.14f %28.14f\n' % (
                            ix, iy, iz, l+1, m+1,
                            2.0 * HRS[l, m, i, j, k, ispin].real,
                            2.0 * HRS[l, m, i, j, k, ispin].imag))


def parse_paoflow_hr(fname):
    """
    Parse PAOFLOW Hamiltonian file (Wannier90 format).
    
    Returns:
        n_wann: Number of Wannier functions
        n_R: Number of R points
        R_degens: Degeneracy weights
        H_data: List of (Rx, Ry, Rz, m, n, H_real, H_imag) tuples
    """
    with open(fname, 'r') as f:
        lines = f.readlines()
    
    # Line 0: Header
    # Line 1: n_wann
    # Line 2: n_R
    n_wann = int(lines[1].strip())
    n_R = int(lines[2].strip())
    
    # Read degeneracy weights (15 per line)
    nline = int(np.ceil(n_R / 15.0))
    R_degens = []
    for i in range(3, 3 + nline):
        R_degens.extend(map(int, lines[i].strip().split()))
    R_degens = np.array(R_degens, dtype=int)
    
    # Read Hamiltonian matrix elements
    H_data = []
    for i in range(3 + nline, len(lines)):
        parts = lines[i].strip().split()
        if len(parts) >= 7:
            Rx, Ry, Rz = map(int, parts[0:3])
            m, n = map(int, parts[3:5])
            H_real, H_imag = map(float, parts[5:7])
            H_data.append((Rx, Ry, Rz, m, n, H_real, H_imag))
    
    return n_wann, n_R, R_degens, H_data


def write_tb2j_hr(fname, n_wann, n_R, R_degens, H_data, header="PAOFLOW to TB2J Converter"):
    """
    Write Hamiltonian in TB2J-compatible Wannier90 format.
    
    TB2J divides all matrix elements by 2.0 when reading, so we multiply by 2.0 when writing.
    """
    with open(fname, 'w') as f:
        # Write header
        f.write(header + "\n")
        f.write(f'{n_wann:5d} \n')
        f.write(f'{n_R:5d} \n')
        
        # Write degeneracy weights (15 per line)
        nl = 15
        nlines = n_R // nl
        nlast = n_R % nl
        
        idx = 0
        for j in range(nlines):
            for k in range(nl):
                f.write(f'{R_degens[idx]} ')
                idx += 1
            f.write("\n")
        for k in range(nlast):
            f.write(f'{R_degens[idx]} ')
            idx += 1
        if nlast > 0:
            f.write("\n")
        
        # Write Hamiltonian matrix elements
        # Multiply by 2.0 to compensate for TB2J's division by 2.0 when reading
        for Rx, Ry, Rz, m, n, H_real, H_imag in H_data:
            f.write(f'{Rx:3d} {Ry:3d} {Rz:3d} {m:5d} {n:5d} {2.0*H_real:28.14f} {2.0*H_imag:28.14f}\n')


def convert_from_write_HRs(input_dir, prefix, output_prefix='tb2j'):
    """
    Convert PAOFLOW write_HRs output to TB2J format.
    
    This reads the files created by PAOFLOW.write_Hamiltonian() method and
    adjusts the Hamiltonian values to account for TB2J's factor of 2 division.
    
    Args:
        input_dir: Directory containing PAOFLOW output
        prefix: Prefix of the PAOFLOW Hamiltonian files
        output_prefix: Prefix for TB2J output files
    """
    # Check for existing files
    fname_0 = os.path.join(input_dir, f'{prefix}_0')
    fname_1 = os.path.join(input_dir, f'{prefix}_1')
    fname_single = os.path.join(input_dir, prefix)
    
    if os.path.exists(fname_0) and os.path.exists(fname_1):
        # Spin-polarized case
        print(f"Found spin-polarized PAOFLOW output: {fname_0}, {fname_1}")
        print("Parsing and converting to TB2J format...")
        print("Note: Multiplying matrix elements by 2.0 to compensate for TB2J's division")
        
        # Parse spin-up
        n_wann_up, n_R_up, R_degens_up, H_data_up = parse_paoflow_hr(fname_0)
        
        # Parse spin-down
        n_wann_dn, n_R_dn, R_degens_dn, H_data_dn = parse_paoflow_hr(fname_1)
        
        # Write TB2J files with factor of 2
        output_up = os.path.join(input_dir, f'{output_prefix}.up_hr.dat')
        output_dn = os.path.join(input_dir, f'{output_prefix}.dn_hr.dat')
        
        write_tb2j_hr(output_up, n_wann_up, n_R_up, R_degens_up, H_data_up)
        write_tb2j_hr(output_dn, n_wann_dn, n_R_dn, R_degens_dn, H_data_dn)
        
        print(f"Created TB2J files:")
        print(f"  - {output_up} ({len(H_data_up)} matrix elements)")
        print(f"  - {output_dn} ({len(H_data_dn)} matrix elements)")
        
    elif os.path.exists(fname_single):
        # Non-spin-polarized case
        print(f"Found non-spin-polarized PAOFLOW output: {fname_single}")
        print("Parsing and converting to TB2J format...")
        print("Note: Multiplying matrix elements by 2.0 to compensate for TB2J's division")
        
        n_wann, n_R, R_degens, H_data = parse_paoflow_hr(fname_single)
        
        output_file = os.path.join(input_dir, f'{output_prefix}_hr.dat')
        write_tb2j_hr(output_file, n_wann, n_R, R_degens, H_data)
        
        print(f"Created TB2J file: {output_file} ({len(H_data)} matrix elements)")
        
    else:
        raise FileNotFoundError(
            f"Could not find PAOFLOW Hamiltonian files with prefix '{prefix}' in {input_dir}\n"
            f"Expected files: {fname_0} and {fname_1} (spin-polarized) or {fname_single} (non-spin-polarized)"
        )



def convert_from_Hks_npy(input_dir, output_prefix='tb2j', nk1=None, nk2=None, nk3=None):
    """
    Convert PAOFLOW k-space Hamiltonian (.npy format) to TB2J format.
    
    This reads kham_up.npy and kham_dn.npy files created by PAOFLOW with write_binary=True.
    
    Args:
        input_dir: Directory containing PAOFLOW .npy output
        output_prefix: Prefix for TB2J output files
        nk1, nk2, nk3: k-point grid dimensions (required)
    """
    if nk1 is None or nk2 is None or nk3 is None:
        raise ValueError("Must specify k-point grid dimensions (nk1, nk2, nk3) for .npy conversion")
    
    # Check for binary files
    kham_up = os.path.join(input_dir, 'kham_up.npy')
    kham_dn = os.path.join(input_dir, 'kham_dn.npy')
    kham_single = os.path.join(input_dir, 'kham.npy')
    
    if os.path.exists(kham_up) and os.path.exists(kham_dn):
        # Spin-polarized case
        print(f"Found spin-polarized k-space Hamiltonians: {kham_up}, {kham_dn}")
        
        # Load k-space Hamiltonians
        Hk_up_flat = np.load(kham_up)
        Hk_dn_flat = np.load(kham_dn)
        
        # Determine nawf from data
        nkpnts = nk1 * nk2 * nk3
        nawf = int(np.sqrt(len(Hk_up_flat) / nkpnts))
        
        print(f"Grid: {nk1}x{nk2}x{nk3}, Number of Wannier functions: {nawf}")
        
        # Reshape
        Hks = np.zeros((nawf, nawf, nkpnts, 2), dtype=complex)
        Hks[:, :, :, 0] = Hk_up_flat.reshape((nawf, nawf, nkpnts))
        Hks[:, :, :, 1] = Hk_dn_flat.reshape((nawf, nawf, nkpnts))
        
        # Reshape to 3D k-grid
        Hks = Hks.reshape((nawf, nawf, nk1, nk2, nk3, 2))
        
        # Fourier transform to real space
        HRS = np.fft.ifftn(Hks, axes=(2, 3, 4))
        
        # Pad to odd dimensions
        pad1 = 0 if nk1 % 2 else 1
        pad2 = 0 if nk2 % 2 else 1
        pad3 = 0 if nk3 % 2 else 1
        
        if pad1 or pad2 or pad3:
            print(f"Padding grid to odd dimensions: {nk1+pad1}x{nk2+pad2}x{nk3+pad3}")
            HRS_padded = np.zeros((nawf, nawf, nk1+pad1, nk2+pad2, nk3+pad3, 2), dtype=complex)
            for n in range(nawf):
                for m in range(nawf):
                    for ispin in range(2):
                        HRS_padded[n, m, :, :, :, ispin] = zero_pad(
                            HRS[n, m, :, :, :, ispin], nk1, nk2, nk3, pad1, pad2, pad3)
            HRS = HRS_padded
            nk1 += pad1
            nk2 += pad2
            nk3 += pad3
        
        # Write TB2J files
        output_up = os.path.join(input_dir, f'{output_prefix}.up_hr.dat')
        output_dn = os.path.join(input_dir, f'{output_prefix}.dn_hr.dat')
        
        with open(output_up, 'w') as f:
            write_wannier90_hr(HRS, nk1, nk2, nk3, nawf, 0, f)
        with open(output_dn, 'w') as f:
            write_wannier90_hr(HRS, nk1, nk2, nk3, nawf, 1, f)
        
        print(f"Created TB2J files:")
        print(f"  - {output_up}")
        print(f"  - {output_dn}")
        
    elif os.path.exists(kham_single):
        # Non-spin-polarized case
        print(f"Found non-spin-polarized k-space Hamiltonian: {kham_single}")
        # Similar process for single spin
        # (Implementation similar to above but for nspin=1)
        print("Non-spin-polarized .npy conversion not yet implemented")
        
    else:
        raise FileNotFoundError(
            f"Could not find PAOFLOW k-space Hamiltonian files in {input_dir}\n"
            f"Expected: {kham_up} and {kham_dn} (or {kham_single})"
        )


def main():
    parser = argparse.ArgumentParser(
        description='Convert PAOFLOW Hamiltonian output to TB2J Wannier90 format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert from write_Hamiltonian() output (already in Wannier90 format)
  paoflow2tb2j --input output/ --input-prefix hamiltonian.dat --output-prefix Fe
  
  # Convert from binary .npy files (requires grid dimensions)
  paoflow2tb2j --input output/ --format npy --nk 12 12 12 --output-prefix Fe

Output:
  For spin-polarized calculations:
    - {output_prefix}.up_hr.dat (spin-up)
    - {output_prefix}.dn_hr.dat (spin-down)
  
  For non-spin-polarized:
    - {output_prefix}_hr.dat

Usage with TB2J:
  wann2J --path output/ \\
         --prefix_up Fe.up \\
         --prefix_down Fe.dn \\
         --posfile POSCAR \\
         --elements Fe \\
         --efermi 0.0 \\
         --kmesh 10 10 10
        """
    )
    
    parser.add_argument('--input', '-i', required=True,
                        help='Input directory containing PAOFLOW output')
    parser.add_argument('--input-prefix', '-p', default='hamiltonian.dat',
                        help='Prefix of PAOFLOW Hamiltonian files (default: hamiltonian.dat)')
    parser.add_argument('--output-prefix', '-o', default='tb2j',
                        help='Prefix for TB2J output files (default: tb2j)')
    parser.add_argument('--format', '-f', choices=['hr', 'npy'], default='hr',
                        help='Input format: hr (write_Hamiltonian output) or npy (write_binary output)')
    parser.add_argument('--nk', nargs=3, type=int, metavar=('NK1', 'NK2', 'NK3'),
                        help='k-point grid dimensions (required for --format npy)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("PAOFLOW to TB2J Converter")
    print("=" * 70)
    print(f"Input directory: {args.input}")
    print(f"Input format: {args.format}")
    print(f"Output prefix: {args.output_prefix}")
    print()
    
    try:
        if args.format == 'hr':
            # Convert from write_Hamiltonian output
            convert_from_write_HRs(args.input, args.input_prefix, args.output_prefix)
        elif args.format == 'npy':
            # Convert from binary .npy files
            if args.nk is None:
                print("ERROR: --nk is required when using --format npy")
                sys.exit(1)
            nk1, nk2, nk3 = args.nk
            convert_from_Hks_npy(args.input, args.output_prefix, nk1, nk2, nk3)
        
        print()
        print("=" * 70)
        print("Conversion successful!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Prepare structure file for TB2J")
        print("2. Run TB2J with the generated files")
        print("\nSee README.md for detailed TB2J usage instructions.")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
