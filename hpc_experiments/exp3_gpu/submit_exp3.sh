#!/bin/bash
#SBATCH -J qvx_exp3_gpu_aes
#SBATCH -p gpu
#SBATCH -N 1
#SBATCH -c 8
#SBATCH --gres=gpu:2
#SBATCH --time=01:00:00
#SBATCH -o /scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/slurm_logs/exp3_%j.out
#SBATCH -e /scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/slurm_logs/exp3_%j.err
#SBATCH -A iuac

echo "Job ID: $SLURM_JOB_ID | Node: $SLURMD_NODENAME | Start: $(date)"
nvidia-smi

module load miniconda3
source /home/apps/MLDL/DL-CondaPy3.10/etc/profile.d/conda.sh
conda activate qvx
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
export PYTHONPATH=/scratch/hpctw14/quantumvault_hpc/QuantumVault:$PYTHONPATH

python3 /scratch/hpctw14/quantumvault_hpc/QuantumVault/hpc_experiments/exp3_gpu/gpu_aes_bench.py

echo "End: $(date) | EXPERIMENT 3 COMPLETE"
