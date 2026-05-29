"""
Crypto-Agility Simulator
Simulates a financial institution's migration from classical to PQC cryptography.
Directly aligned with RBI Q-SAFE Expert Committee mandate:
- Cryptography Bill of Materials (CBOM)
- Crypto agility assessment
- Migration roadmap generation
"""
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()

# Simulated cryptographic inventory of a fictional bank's systems
# This is what the RBI Q-SAFE committee calls a "CBOM"
FINANCIAL_CRYPTO_INVENTORY = {
    "ATM_Network_Node": {
        "current_algo": "RSA-2048",
        "usage": "PIN block encryption",
        "quantum_risk": "CRITICAL",
        "migration_target": "Kyber-768 + AES-256-GCM",
        "estimated_migration_ms": 0.21,  # from our actual benchmarks
        "notes": "High-priority — directly handles customer PINs"
    },
    "Core_Banking_TLS": {
        "current_algo": "ECDH-P256 + AES-128",
        "usage": "Branch-to-datacenter communication",
        "quantum_risk": "HIGH",
        "migration_target": "Kyber-768 + AES-256-GCM",
        "estimated_migration_ms": 0.20,
        "notes": "Harvest-now-decrypt-later risk for archived transactions"
    },
    "Inter_Bank_Settlement": {
        "current_algo": "RSA-4096",
        "usage": "RTGS / NEFT transaction signing",
        "quantum_risk": "CRITICAL",
        "migration_target": "Dilithium-3",
        "estimated_migration_ms": 0.49,
        "notes": "NPCI settlement layer — regulatory priority"
    },
    "Mobile_Banking_Auth": {
        "current_algo": "RSA-2048",
        "usage": "OTP and session token signing",
        "quantum_risk": "HIGH",
        "migration_target": "Dilithium-3",
        "estimated_migration_ms": 0.49,
        "notes": "300M+ users — migration must be backward compatible"
    },
    "Document_Signing": {
        "current_algo": "RSA-2048",
        "usage": "Loan agreements, KYC documents",
        "quantum_risk": "MEDIUM",
        "migration_target": "Dilithium-3",
        "estimated_migration_ms": 0.49,
        "notes": "Long-lived documents need long-term signature validity"
    },
    "Audit_Log_Integrity": {
        "current_algo": "SHA-256 + RSA",
        "usage": "Tamper-evident audit trails",
        "quantum_risk": "MEDIUM",
        "migration_target": "SHA-3 + Dilithium-3",
        "estimated_migration_ms": 0.49,
        "notes": "Regulatory requirement — logs must be verifiable for 10 years"
    },
}


def generate_cbom_report(output_json=True):
    """
    Generate a Cryptography Bill of Materials report.
    This is the first deliverable the RBI Q-SAFE committee mandates.
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  CRYPTOGRAPHY BILL OF MATERIALS (CBOM)           [/bold cyan]")
    console.print("[bold cyan]  Aligned with RBI Q-SAFE Expert Committee        [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("System", style="bold", width=25)
    table.add_column("Current Crypto", width=18)
    table.add_column("Risk", justify="center", width=10)
    table.add_column("Migration Target", width=25)
    table.add_column("Migration Time", justify="right", width=14)

    risk_colors = {"CRITICAL": "red", "HIGH": "yellow", "MEDIUM": "cyan"}
    critical_count = 0
    total_migration_ms = 0

    for system, info in FINANCIAL_CRYPTO_INVENTORY.items():
        risk = info["quantum_risk"]
        color = risk_colors.get(risk, "white")
        if risk == "CRITICAL":
            critical_count += 1
        total_migration_ms += info["estimated_migration_ms"]
        table.add_row(
            system.replace("_", " "),
            info["current_algo"],
            f"[{color}]{risk}[/{color}]",
            info["migration_target"],
            f"{info['estimated_migration_ms']:.2f}ms"
        )

    console.print(table)
    console.print(f"\n[red]Critical systems requiring immediate migration: {critical_count}[/red]")
    console.print(f"[green]Total per-operation migration overhead: {total_migration_ms:.2f}ms[/green]")
    console.print(f"[cyan]Migration feasible on commodity ARM edge hardware (Pi 5)[/cyan]")
    console.print("\n[bold]Benchmark source:[/bold] QuantumVault v1.0 — Raspberry Pi 5 8GB, 500 iterations\n")

    if output_json:
        report = {
            "report_type": "CBOM",
            "generated": datetime.utcnow().isoformat(),
            "platform": "Raspberry Pi 5 8GB",
            "standard_alignment": ["NIST FIPS 203", "NIST FIPS 204", "RBI Q-SAFE"],
            "inventory": FINANCIAL_CRYPTO_INVENTORY,
            "summary": {
                "total_systems": len(FINANCIAL_CRYPTO_INVENTORY),
                "critical_systems": critical_count,
                "total_migration_overhead_ms": total_migration_ms
            }
        }
        with open("results/cbom_report.json", "w") as f:
            json.dump(report, f, indent=2)
        console.print("[green]CBOM report saved to results/cbom_report.json[/green]")


def simulate_migration(system_name: str):
    """
    Simulate the RSA → PQC migration for a specific banking system.
    Shows before/after performance comparison using real benchmark data.
    """
    if system_name not in FINANCIAL_CRYPTO_INVENTORY:
        console.print(f"[red]Unknown system: {system_name}[/red]")
        return

    info = FINANCIAL_CRYPTO_INVENTORY[system_name]
    rsa_keygen_ms = 341.0  # from our actual Pi 5 benchmark

    console.print(f"\n[bold]Migration Simulation: {system_name.replace('_', ' ')}[/bold]")
    console.print(f"  Current:  {info['current_algo']} — KeyGen: {rsa_keygen_ms:.1f}ms")
    console.print(f"  Target:   {info['migration_target']} — KeyGen: {info['estimated_migration_ms']:.2f}ms")
    speedup = rsa_keygen_ms / info['estimated_migration_ms']
    console.print(f"  Speedup:  [green]{speedup:.0f}x faster[/green]")
    console.print(f"  Note:     {info['notes']}")
    console.print(f"  Status:   [yellow]Migration tool available — QuantumVault --migrate-rsa[/yellow]")
