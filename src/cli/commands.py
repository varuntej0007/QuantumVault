"""
QuantumVault CLI — startup-grade command interface.
Commands: keygen, encrypt, decrypt, migrate, bench, audit
"""
import click
from rich.console import Console
from rich.table import Table
from loguru import logger

console = Console()


@click.group()
@click.version_option("1.0.0", prog_name="QuantumVault")
def cli():
    """QuantumVault — Post-Quantum Cryptography File Encryption"""
    pass


@cli.command()
@click.option("--identity", "-i", required=True, help="Identity name (e.g., alice, server01)")
@click.option("--password", "-p", prompt=True, hide_input=True, confirmation_prompt=True)
def keygen(identity, password):
    """Generate Kyber-768 + Dilithium-3 keypairs for an identity."""
    from src.core.key_manager import generate_keypairs
    with console.status("[bold green]Generating PQC keypairs..."):
        keys = generate_keypairs(identity, password)
    console.print(f"[green]✓[/green] Keys generated for [bold]{identity}[/bold]")
    console.print(f"  Kyber-768 public key: {len(keys['kyber_pub'])} bytes")
    console.print(f"  Dilithium-3 public key: {len(keys['dil_pub'])} bytes")
    console.print(f"  Private keys encrypted in config/key_store/")


@cli.command()
@click.argument("input_file")
@click.argument("output_file")
@click.option("--identity", "-i", required=True, help="Identity whose keys to use")
@click.option("--password", "-p", prompt=True, hide_input=True)
def encrypt(input_file, output_file, identity, password):
    """Encrypt a file using Hybrid PQC (Kyber-768 + AES-256-GCM + Dilithium-3)."""
    import time
    from src.core.key_manager import load_private_keys, load_public_keys
    from src.core.hybrid_engine import encrypt_file

    keys_pub = load_public_keys(identity)
    keys_priv = load_private_keys(identity, password)

    start = time.perf_counter()
    encrypt_file(input_file, output_file,
                 keys_pub["kyber_pub"], keys_priv["dil_sec"])
    elapsed = time.perf_counter() - start

    import os
    size_mb = os.path.getsize(input_file) / 1e6
    console.print(f"[green]✓[/green] Encrypted [bold]{input_file}[/bold] → [bold]{output_file}[/bold]")
    console.print(f"  {size_mb:.2f} MB in {elapsed*1000:.1f}ms  ({size_mb/elapsed:.1f} MB/s)")


@cli.command()
@click.argument("input_file")
@click.argument("output_file")
@click.option("--identity", "-i", required=True)
@click.option("--password", "-p", prompt=True, hide_input=True)
def decrypt(input_file, output_file, identity, password):
    """Decrypt a .qvault file. Signature is verified BEFORE decryption."""
    import time
    from src.core.key_manager import load_private_keys, load_public_keys
    from src.core.hybrid_engine import decrypt_file

    keys_pub = load_public_keys(identity)
    keys_priv = load_private_keys(identity, password)

    start = time.perf_counter()
    decrypt_file(input_file, output_file,
                 keys_priv["kyber_sec"], keys_pub["dil_pub"])
    elapsed = time.perf_counter() - start

    console.print(f"[green]✓[/green] Decrypted [bold]{input_file}[/bold] → [bold]{output_file}[/bold]")
    console.print(f"  Time: {elapsed*1000:.1f}ms")


@cli.command()
@click.argument("rsa_archive")
@click.argument("rsa_key_pem")
@click.argument("output_vault")
@click.option("--identity", "-i", required=True)
@click.option("--password", "-p", prompt=True, hide_input=True)
def migrate(rsa_archive, rsa_key_pem, output_vault, identity, password):
    """Migrate a legacy RSA-encrypted archive to PQC format."""
    from src.core.key_manager import load_private_keys, load_public_keys
    from src.core.migration import migrate_rsa_to_pqc

    keys_pub = load_public_keys(identity)
    keys_priv = load_private_keys(identity, password)

    with console.status("[bold yellow]Migrating RSA → PQC..."):
        migrate_rsa_to_pqc(rsa_archive, rsa_key_pem, output_vault,
                           keys_pub["kyber_pub"], keys_priv["dil_sec"])
    console.print(f"[green]✓[/green] Migration complete → [bold]{output_vault}[/bold]")


@cli.command()
def bench():
    """Run full benchmark suite: PQC vs RSA speed comparison."""
    import subprocess
    subprocess.run(["python3", "benchmarks/run_bench.py"])


if __name__ == "__main__":
    cli()
@cli.command()
def cbom():
    """Generate Cryptography Bill of Materials — RBI Q-SAFE aligned."""
    from src.core.crypto_agility import generate_cbom_report
    generate_cbom_report()

@cli.command()
@click.argument("system")
def migrate_sim(system):
    """Simulate RSA→PQC migration for a banking system."""
    from src.core.crypto_agility import simulate_migration
    simulate_migration(system)
