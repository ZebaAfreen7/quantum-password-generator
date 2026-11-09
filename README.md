# Quantum Random Password Generator

**Subject:** Quantum Computing (PCCCS581)
**Team:** Harshita Jha (70) · Zeba Afreen (77) · Ritisha Mondal (79)
**Institute:** IEM Salt Lake · B.Tech 5th Semester · IOTCSBT

**Live demo:** [add your streamlit.app link here]

## About
Generates passwords from the measurement results of a quantum circuit instead of a classical pseudo-random number generator.

## How it works
1. Seven qubits start in state |0⟩.
2. A **Hadamard gate** on each qubit puts it into an equal superposition of |0⟩ and |1⟩.
3. **Measuring** each qubit gives 0 or 1 with 50% probability, so the 7 bits form a random number from 0 to 127.
4. Numbers below 88 pick a character from an 88-character set (letters, digits, symbols). Numbers 88–127 are discarded (rejection sampling), so every character is equally likely.
5. The app compares the circuit's output with Python's `random` module using bit frequencies and a chi-square test.

> The app runs on the Qiskit Aer **simulator**, which imitates measurement with a classical pseudo-random generator. Running the same circuit on real quantum hardware gives true randomness.

## How to run
```
pip install -r requirements.txt
python src/quantum_password_generator.py   # command-line version
streamlit run app.py                         # web app
```

## Project structure
```
src/quantum_password_generator.py   circuit, password generation, entropy, comparison plot
app.py                              Streamlit web app
results/                            saved bit distribution chart
requirements.txt                    Python libraries
```