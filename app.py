"""
Web app for the Quantum Random Password Generator.

Run locally:  streamlit run app.py
"""
import random
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

import matplotlib
matplotlib.use("Agg")  # draw charts without opening windows

import pandas as pd
import streamlit as st
from scipy.stats import chisquare


# All Qiskit work runs on one long-lived worker thread. Streamlit runs each page
# refresh on a new short-lived thread, and Qiskit's compiled core can crash when
# it is called from many of those.
@st.cache_resource
def quantum_worker():
    return ThreadPoolExecutor(max_workers=1)


def on_worker(fn, *args):
    return quantum_worker().submit(fn, *args).result()


def _load():
    from src import quantum_password_generator as q
    return q


q = on_worker(_load)
CHARSET, N_QUBITS, strength = q.CHARSET, q.N_QUBITS, q.strength
CIRCUIT_TEXT = on_worker(lambda: str(q.CIRCUIT.draw(output="text")))


def quantum_password(length):
    return on_worker(q.quantum_password, length)


def quantum_bits(n):
    return on_worker(q.quantum_bits, n)

st.set_page_config(page_title="Quantum Password Generator", page_icon="🔐", layout="centered")

st.title("🔐 Quantum Random Password Generator")
st.caption("Quantum Computing (PCCCS581) · Hadamard gates + measurement with Qiskit")

# ---------------- Generate ----------------
st.subheader("Generate passwords")
c1, c2 = st.columns(2)
length = c1.slider("Password length", min_value=8, max_value=32, value=16)
count = c2.slider("How many passwords", min_value=1, max_value=5, value=3)

if st.button("Generate with quantum circuit", type="primary"):
    rows = []
    for _ in range(count):
        pw = quantum_password(length)
        bits, label = strength(pw)
        rows.append({"Password": pw, "Entropy (bits)": round(bits), "Strength": label})
    st.session_state["passwords"] = rows

if "passwords" in st.session_state:
    for r in st.session_state["passwords"]:
        st.code(r["Password"], language=None)
    r0 = st.session_state["passwords"][0]
    st.write(f"Each password has about **{r0['Entropy (bits)']} bits** of entropy: **{r0['Strength']}**.")

# ---------------- Circuit ----------------
st.divider()
st.subheader("The quantum circuit")
st.write(
    f"Each of the {N_QUBITS} qubits starts in |0⟩. A Hadamard gate (H) puts it into an equal "
    "superposition of |0⟩ and |1⟩, and measuring (M) collapses it to 0 or 1 with 50% probability each. "
    f"The {N_QUBITS} results form a number from 0 to 127, which picks one of the "
    f"{len(CHARSET)} characters."
)
st.code(CIRCUIT_TEXT, language=None)

# ---------------- Randomness test ----------------
st.divider()
st.subheader("How random is it?")
n = st.select_slider("Number of samples", options=[1000, 2000, 5000, 10000], value=5000)


@st.cache_data(show_spinner="Running the circuit...")
def compare(n_samples):
    q_vals = [int(b, 2) for b in quantum_bits(n_samples)]
    p_vals = [random.getrandbits(N_QUBITS) for _ in range(n_samples)]
    return q_vals, p_vals


q_vals, p_vals = compare(n)

q_bits = Counter("".join(format(v, f"0{N_QUBITS}b") for v in q_vals))
p_bits = Counter("".join(format(v, f"0{N_QUBITS}b") for v in p_vals))
total = n * N_QUBITS
bit_df = pd.DataFrame(
    {"Quantum circuit": [q_bits["0"] / total, q_bits["1"] / total],
     "Python random": [p_bits["0"] / total, p_bits["1"] / total]},
    index=["bit 0", "bit 1"],
)
st.write("**Share of 0s and 1s** (ideal: 0.5 each)")
st.bar_chart(bit_df, stack=False)

expected = [n / 2 ** N_QUBITS] * 2 ** N_QUBITS
q_chi = chisquare([Counter(q_vals)[i] for i in range(2 ** N_QUBITS)], expected)
p_chi = chisquare([Counter(p_vals)[i] for i in range(2 ** N_QUBITS)], expected)
st.write("**Chi-square test for uniform outcomes 0–127** (p-value above 0.05 means no evidence of bias)")
st.table(pd.DataFrame({
    "Source": ["Quantum circuit", "Python random"],
    "Chi-square": [round(q_chi.statistic, 1), round(p_chi.statistic, 1)],
    "p-value": [round(q_chi.pvalue, 3), round(p_chi.pvalue, 3)],
    "Looks uniform?": ["Yes" if q_chi.pvalue > 0.05 else "No", "Yes" if p_chi.pvalue > 0.05 else "No"],
}).set_index("Source"))

with st.expander("Simulator vs real quantum hardware"):
    st.markdown(
        """
This app runs the circuit on **Qiskit Aer**, a simulator that runs on a normal computer.
The simulator imitates measurement using a classical pseudo-random number generator, so its
output is not truly random.

Running the **same circuit on real quantum hardware** (for example an IBM Quantum computer)
gives true randomness, because the outcome of measuring a qubit in superposition is
fundamentally unpredictable.
        """
    )