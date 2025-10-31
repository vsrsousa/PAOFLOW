#!/usr/bin/env python3
"""
Example script showing how to export PAOFLOW Hamiltonians for TB2J

This script demonstrates the workflow for a spin-polarized calculation.
"""

from PAOFLOW import PAOFLOW

def main():
    # Initialize PAOFLOW with spin-polarized DFT data
    # Adjust paths according to your directory structure
    paoflow = PAOFLOW(savedir='./nscf_nspin2/',  
                      outputdir='./output_TB2J/', 
                      verbose=True,
                      dft="VASP")  # Change to "QE" for Quantum ESPRESSO
    
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
    
    # Export Hamiltonian for TB2J
    # This creates:
    # - MyMaterial.up_hr.dat (spin-up channel)
    # - MyMaterial.dn_hr.dat (spin-down channel)
    paoflow.write_Hamiltonian_TB2J(prefix='MyMaterial')
    
    print("\n" + "="*60)
    print("Hamiltonians exported successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Copy your POSCAR file to the output_TB2J directory")
    print("2. Run TB2J with:")
    print("   wann2J --path ./output_TB2J/ \\")
    print("          --prefix_up MyMaterial.up \\")
    print("          --prefix_down MyMaterial.dn \\")
    print("          --posfile POSCAR \\")
    print("          --elements Fe \\")  # Adjust for your material
    print("          --efermi 0.0 \\")
    print("          --kmesh 10 10 10")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
