#!/bin/bash
#SBATCH -J qvx_exp1_concurrent
#SBATCH -p standard
#SBATCH -N 1
#SBATCH -c 48
#SBATCH --time=02:00:00
#SBATCH -o /scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/slurm_logs/exp1_%j.out
#SBATCH -e /scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/slurm_logs/exp1_%j.err
#SBATCH -A iuac

echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Start: $(date)"

# Load environment
module load miniconda3
source /home/apps/MLDL/DL-CondaPy3.10/etc/profile.d/conda.sh
conda activate qvx
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
export PYTHONPATH=/scratch/hpctw14/quantumvault_hpc/QuantumVault:$PYTHONPATH

# Run experiment
python3 /scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/exp1_concurrent/pqc_concurrent_bench.py

echo "End: $(date)"
echo "EXPERIMENT 1 COMPLETE"
