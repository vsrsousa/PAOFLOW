#!/usr/bin/env python3
"""
Example: Export Quantum ESPRESSO Hamiltonians to TB2J format

This script demonstrates how to export spin-polarized tight-binding Hamiltonians
from a Quantum ESPRESSO calculation to TB2J format for calculating magnetic
exchange interactions.

Prerequisites:
- A completed QE nscf calculation with spin-polarized projections
- The QE .save directory containing the projection data
"""

from PAOFLOW import PAOFLOW

def main():
    # Initialize PAOFLOW with QE spin-polarized data
    # Replace 'fe.save' with your QE .save directory name
    paoflow = PAOFLOW.PAOFLOW(
        savedir='fe.save',           # QE .save directory
        outputdir='output_TB2J',     # Output directory for TB2J files
        verbose=True,
        dft='QE'                     # Specify Quantum ESPRESSO
    )
    
    # Read atomic projections from QE
    # For QE, projections are read from the .save directory
    # No need to specify basis manually - QE provides this information
    paoflow.read_atomic_proj_QE()
    
    # Calculate projectability and build tight-binding Hamiltonian
    paoflow.projectability()
    paoflow.pao_hamiltonian()
    
    # Export Hamiltonian in TB2J-compatible format
    # For spin-polarized calculations (nspin=2), this creates:
    #   - Fe.up_hr.dat (spin-up channel)
    #   - Fe.dn_hr.dat (spin-down channel)
    paoflow.write_Hamiltonian_TB2J(prefix='Fe')
    
    print("\n" + "="*70)
    print("SUCCESS: Hamiltonians exported for TB2J!")
    print("="*70)
    print("\nGenerated files:")
    print("  - Fe.up_hr.dat   (spin-up Hamiltonian)")
    print("  - Fe.dn_hr.dat   (spin-down Hamiltonian)")
    print("\nNext steps for TB2J:")
    print("1. Prepare your structure file (e.g., from QE output):")
    print("   You can use the atomic positions from your QE calculation")
    print("\n2. Run TB2J to calculate exchange interactions:")
    print("   wann2J --path ./output_TB2J/ \\")
    print("          --prefix_up Fe.up \\")
    print("          --prefix_down Fe.dn \\")
    print("          --posfile <structure_file> \\")
    print("          --elements Fe \\")
    print("          --efermi <fermi_energy> \\")
    print("          --kmesh 10 10 10")
    print("\n   Note: Fermi energy should be in eV")
    print("   (You can get it from the QE output or PAOFLOW)")
    print("="*70 + "\n")
    
    # Finish execution
    paoflow.finish_execution()

if __name__ == '__main__':
    main()
