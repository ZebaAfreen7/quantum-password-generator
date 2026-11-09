"""
Quantum Random Password Generator (PCCCS581)
Uses Hadamard gates + measurement on a quantum circuit instead of a
pseudo-random number generator.

Note: AerSimulator is a classical simulator, so its "measurements" are
produced by a seeded pseudo-random generator. The circuit is a genuine
quantum random number generator design; it only becomes truly random
when run on real quantum hardware (e.g. an IBM Quantum backend).

Install:  pip install qiskit qiskit-aer matplotlib
Run:      python src/quantum_password_generator.py
"""
import math
import os
import random
import string
from collections import Counter

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

CHARSET = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.<>?/"  # 88 chars
N_QUBITS = 7  # 2^7 = 128 values; we keep values < len(CHARSET) (rejection sampling, no bias)

sim = AerSimulator()


def build_circuit():
    qc = QuantumCircuit(N_QUBITS, N_QUBITS)
    qc.h(range(N_QUBITS))                  # put every qubit in superposition (|0> + |1>)/sqrt(2)
    qc.measure(range(N_QUBITS), range(N_QUBITS))
    return qc


CIRCUIT = build_circuit()  # built once and reused for every run


def quantum_bits(n_samples):
    """Return n_samples random 7-bit strings, one per measurement (shot)."""
    result = sim.run(CIRCUIT, shots=n_samples, memory=True).result()
    return result.get_memory()


def quantum_password(length=16):
    chars = []
    while len(chars) < length:
        for bits in quantum_bits(length * 2):  # ~69% of 7-bit values are accepted
            value = int(bits, 2)
            if value < len(CHARSET):           # reject out-of-range values to avoid bias
                chars.append(CHARSET[value])
                if len(chars) == length:
                    break
    return "".join(chars)


def strength(pw):
    entropy = len(pw) * math.log2(len(CHARSET))  # ~6.46 bits per character
    if entropy < 50:
        label = "Weak"
    elif entropy < 80:
        label = "Good"
    elif entropy < 110:
        label = "Strong"
    else:
        label = "Excellent"
    return entropy, label


def compare_with_pseudo_random(n=4000):
    """Plot bit frequency of quantum circuit vs Python's pseudo-random generator."""
    q = Counter("".join(quantum_bits(n)))
    p = Counter("".join(format(random.getrandbits(N_QUBITS), f"0{N_QUBITS}b") for _ in range(n)))
    total = n * N_QUBITS
    xs = [0, 1]
    plt.figure()
    plt.bar([x - 0.15 for x in xs], [q[str(x)] / total for x in xs], 0.3, label="Quantum (Qiskit)")
    plt.bar([x + 0.15 for x in xs], [p[str(x)] / total for x in xs], 0.3, label="Pseudo-random (Python)")
    plt.axhline(0.5, color="gray", linestyle="--")
    plt.xticks(xs, ["bit 0", "bit 1"])
    plt.ylabel("Frequency")
    plt.title("Bit distribution comparison")
    plt.legend()
    os.makedirs("results", exist_ok=True)
    plt.savefig("results/bit_distribution.png", dpi=150, bbox_inches="tight")
    print("Saved results/bit_distribution.png")


def ask_length(default=16):
    raw = input(f"Password length (default {default}): ").strip()
    if not raw:
        return default
    try:
        n = int(raw)
        return n if n > 0 else default
    except ValueError:
        print(f"Not a number, using {default}.")
        return default


if __name__ == "__main__":
    print("=== Quantum Random Password Generator ===")
    n = ask_length()
    for i in range(3):
        pw = quantum_password(n)
        e, label = strength(pw)
        print(f"{i + 1}. {pw}   | entropy ~{e:.0f} bits | {label}")

    print("\nCircuit used:")
    print(CIRCUIT.draw(output="text"))

    compare_with_pseudo_random()
    