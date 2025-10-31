#!/usr/bin/env python3
"""
Example: Export Quantum ESPRESSO Hamiltonians for TB2J

This script demonstrates how to generate Hamiltonians from QE with PAOFLOW
that can be converted to TB2J format using the standalone paoflow2tb2j tool.
"""

from PAOFLOW import PAOFLOW

def main():
    # Initialize PAOFLOW with QE spin-polarized data
    # Replace 'fe.save' with your QE .save directory name
    paoflow = PAOFLOW.PAOFLOW(
        savedir='fe.save',           # QE .save directory
        outputdir='output_TB2J',     # Output directory
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
    
    # Write Hamiltonian using PAOFLOW's existing write_Hamiltonian method
    # For spin-polarized calculations, this creates:
    #   - hamiltonian.dat_0 (spin-up channel)
    #   - hamiltonian.dat_1 (spin-down channel)
    paoflow.write_Hamiltonian('hamiltonian.dat')
    
    print("\n" + "="*70)
    print("SUCCESS: Hamiltonians written!")
    print("="*70)
    print("\nGenerated files in output_TB2J/:")
    print("  - hamiltonian.dat_0 (spin-up)")
    print("  - hamiltonian.dat_1 (spin-down)")
    print("\nNext steps:")
    print("1. Convert to TB2J format using the standalone converter:")
    print("   cd ../../tools/paoflow2tb2j")
    print("   python paoflow2tb2j.py --input ../../examples/TB2J_example/output_TB2J/ \\")
    print("                          --input-prefix hamiltonian.dat \\")
    print("                          --output-prefix Fe")
    print("\n2. This will create:")
    print("   - Fe.up_hr.dat (spin-up, TB2J format)")
    print("   - Fe.dn_hr.dat (spin-down, TB2J format)")
    print("\n3. Run TB2J to calculate exchange interactions:")
    print("   wann2J --path output_TB2J/ \\")
    print("          --prefix_up Fe.up \\")
    print("          --prefix_down Fe.dn \\")
    print("          --posfile <structure_file> \\")
    print("          --elements Fe \\")
    print("          --efermi <fermi_energy> \\")
    print("          --kmesh 10 10 10")
    print("\n   Note: Get Fermi energy from QE output or PAOFLOW")
    print("="*70 + "\n")
    
    # Finish execution
    paoflow.finish_execution()

if __name__ == '__main__':
    main()
