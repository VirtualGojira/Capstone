import numpy as np
from random import randint

# Define constants for NTRU
N = 7   # Polynomial degree, this should be much larger in real-world usage (e.g., 509, 701, etc.)
P = 3   # Small integer modulus (typically 3)
Q = 32  # Larger integer modulus (typically a power of 2)

# Generate a random polynomial
def generate_random_polynomial(degree, modulus):
    return np.array([randint(0, modulus-1) for _ in range(degree)])

# Polynomial addition
def poly_add(p1, p2, modulus):
    return (p1 + p2) % modulus

# Polynomial multiplication (mod X^N - 1)
def poly_multiply(p1, p2, modulus, N):
    result = np.zeros(2 * N - 1, dtype=int)
    for i in range(N):
        for j in range(N):
            result[i + j] += p1[i] * p2[j]
    return result[:N] % modulus

# Inverse modulo X^N - 1 of a polynomial using the Extended Euclidean algorithm
def poly_inverse(f, modulus, N):
    a = np.zeros(N, dtype=int)
    b = np.ones(N, dtype=int)  # b will be the inverse (start with 1)
    for i in range(N):
        a[i] = f[i]

    # Extended Euclidean algorithm
    for _ in range(2 * N):
        q = np.zeros(N, dtype=int)
        for i in range(N):
            q[i] = a[i]
        for i in range(N):
            if q[i] != 0:
                for j in range(i, N):
                    b[j] = (b[j] + q[j]) % modulus
        a = poly_add(a, q, modulus)
    return b

# Key Generation
def key_generation():
    # Generate f and g (polynomials)
    f = generate_random_polynomial(N, P)
    g = generate_random_polynomial(N, P)
    f_inv = poly_inverse(f, P, N)

    # Public key = h = f_inv * g (mod Q)
    h = poly_multiply(f_inv, g, Q, N)

    # Private key = f, g
    return (f, g), h

# Encryption
def encrypt(message, public_key):
    # m is the plaintext message, encoded as a polynomial
    m = np.array(message, dtype=int)

    # Generate a random polynomial r (small values)
    r = generate_random_polynomial(N, P)

    # h is the public key
    h = public_key

    # c = r * h + m (mod Q)
    c = poly_multiply(r, h, Q, N)
    c = poly_add(c, m, Q)

    return c

# Decryption
def decrypt(ciphertext, private_key):
    f, g = private_key

    # c is the ciphertext (received)
    c = np.array(ciphertext, dtype=int)

    # Step 1: Multiply the ciphertext by f (mod Q)
    result = poly_multiply(c, f, Q, N)

    # Step 2: Reduce the result modulo P to obtain the message
    return result % P

# Main
if __name__ == '__main__':
    # Key Generation
    private_key, public_key = key_generation()
    print("Private key:", private_key)
    print("Public key:", public_key)

    # Encrypt a simple message
    message = [1, 0, 1, 1, 0, 1, 0]  # Example message as a list of bits (polynomial)
    print("Original Message:", message)

    ciphertext = encrypt(message, public_key)
    print("Ciphertext:", ciphertext)

    # Decrypt the message
    decrypted_message = decrypt(ciphertext, private_key)
    print("Decrypted Message:", decrypted_message)
