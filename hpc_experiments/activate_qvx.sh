#!/bin/bash
# Source this at the top of every SLURM job script
module load miniconda3
source /home/apps/MLDL/DL-CondaPy3.10/etc/profile.d/conda.sh
conda activate qvx
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
export PYTHONPATH=/scratch/hpctw14/quantumvault_hpc/QuantumVault:$PYTHONPATH
