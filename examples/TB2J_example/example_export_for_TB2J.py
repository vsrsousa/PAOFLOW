#!/usr/bin/env python3
"""
Example: Export VASP Hamiltonians for TB2J using existing PAOFLOW methods

This script demonstrates how to generate Hamiltonians with PAOFLOW that can
be converted to TB2J format using the standalone paoflow2tb2j converter tool.
"""

from PAOFLOW import PAOFLOW

def main():
    # Initialize PAOFLOW with spin-polarized DFT data
    # Adjust paths according to your directory structure
    paoflow = PAOFLOW(savedir='./nscf_nspin2/',  
                      outputdir='./output_TB2J/', 
                      verbose=True,
                      dft="VASP")
    
    # For VASP, you need to define the projection basis
    # Adjust basis configuration for your material
    basis_path = '../../../BASIS/'
    basis_config = {
        'Fe': ['3D', '4S', '4P'],  # Example for Fe
        # Add other elements as needed
    }
    paoflow.projections(basispath=basis_path, configuration=basis_config)
    
    # Calculate projectability and build Hamiltonian
    paoflow.projectability()
    paoflow.pao_hamiltonian()
    
    # Write Hamiltonian using PAOFLOW's existing write_Hamiltonian method
    # This creates files in Wannier90 format:
    # - hamiltonian.dat_0 (spin-up channel)
    # - hamiltonian.dat_1 (spin-down channel)
    paoflow.write_Hamiltonian('hamiltonian.dat')
    
    print("\n" + "="*60)
    print("Hamiltonians written successfully!")
    print("="*60)
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
    print("\n3. Run TB2J:")
    print("   wann2J --path output_TB2J/ \\")
    print("          --prefix_up Fe.up \\")
    print("          --prefix_down Fe.dn \\")
    print("          --posfile POSCAR \\")
    print("          --elements Fe \\")
    print("          --efermi 0.0 \\")
    print("          --kmesh 10 10 10")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
