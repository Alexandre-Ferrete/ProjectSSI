# Project: Secure E2EE Chat System
[cite_start]**Course:** System Security Project [cite: 1, 2]
**Academic Year:** 2025/2026
[cite_start]**Deadline:** May 24, 2026 [cite: 42]

---

## 1. Project Objective
[cite_start]The goal is to develop a chat system that ensures **End-to-End Encryption (E2EE)**[cite: 4]. The system must provide strict guarantees of:
* [cite_start]**Confidentiality:** Content is inaccessible to third parties, including the server[cite: 5].
* [cite_start]**Integrity:** Messages cannot be tampered with[cite: 5].
* [cite_start]**Authenticity:** All communication between users and the server must be verified[cite: 5, 21].

**Technical Constraints:**
* [cite_start]**Language:** Python[cite: 6].
* [cite_start]**Library:** `cryptography` (mandatory for all primitives)[cite: 6].
* [cite_start]**Architecture:** Client-Server via TCP Sockets[cite: 8, 14].

---

## 2. System Architecture & Components

### 2.1 The Server (Honest but Curious)
* [cite_start]**Function:** Operates continuously to manage users, route messages, and store metadata[cite: 9].
* [cite_start]**Trust Model:** Trusted for functional integrity but **not** for data confidentiality[cite: 18].
* [cite_start]**Persistence:** Must store user data with the same security rigor as active messages[cite: 10].

### 2.2 The Client
* [cite_start]**Interface:** Command-line textual interpreter[cite: 11].
* [cite_start]**Identity:** Unique identifiers for each user; support for multiple sessions is optional[cite: 13].
* [cite_start]**Logic:** Handles all encryption/decryption locally to ensure E2EE[cite: 11, 15].

---

## 3. High-Grade Security Implementation (The "20/20" Strategy)

To achieve the maximum grade, the following advanced primitives and features will be prioritized:

### 3.1 Advanced Cryptographic Features (Valorizações)
* [cite_start]**Perfect Forward Secrecy (PFS):** Implementation of ephemeral key exchanges (e.g., ECDH) so that compromised long-term keys do not expose past sessions[cite: 32].
* [cite_start]**Internal PKI:** The server will act as a self-signed Certificate Authority (CA) to manage user identity certificates and serve as a "Root of Trust"[cite: 23, 29].
* [cite_start]**Offline Messaging:** Implementation of a store-and-forward mechanism where the server holds encrypted blobs for offline recipients[cite: 28].
* [cite_start]**Group Chat Security:** Secure multi-user rooms involving group key distribution and access control[cite: 31].
* [cite_start]**Hybrid Encryption:** Utilizing asymmetric primitives (RSA/ECC) for key encapsulation and symmetric primitives (AES-GCM/ChaCha20) for data transport[cite: 24].

### 3.2 Threat Mitigation
* [cite_start]**MitM Protection:** Active protection against Man-in-the-Middle attacks through certificate validation and signed handshakes[cite: 19].
* [cite_start]**Metadata Protection:** Minimizing the information available to the "curious" server[cite: 18].

---

## 4. Deliverables & Evaluation

### 4.1 Grading Breakdown
| Component | Weight | Requirement |
| :--- | :--- | :--- |
| **Security** | 35% | [cite_start]Rigor of the protocol and primitive choices[cite: 41]. |
| **Functionality** | 25% | [cite_start]Stability of the chat and command interpreter[cite: 41]. |
| **Valorizações** | 25% | [cite_start]Implementation of advanced features (PFS, PKI, etc.)[cite: 41]. |
| **Report** | 15% | [cite_start]Detailed Markdown documentation[cite: 41]. |

### 4.2 Required Report Structure (Markdown)
1. [cite_start]**Architecture:** Detailed flow of communication and key management methodology[cite: 36, 37].
2. [cite_start]**Security Model:** Justification of chosen primitives and analysis of security guarantees[cite: 37].
3. [cite_start]**Limitations:** Honest identification of inherent system weaknesses[cite: 37].
4. [cite_start]**Future Work:** Discussion of potential improvements not implemented due to scope[cite: 38].

---
[cite_start]**Note:** Attendance at the final defense is mandatory for grade approval[cite: 44, 45].