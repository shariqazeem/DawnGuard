# CypherVault - Decentralized AI dApp for DAWN Black Box

![CypherVault](https://img.shields.io/badge/DAWN-Black%20Box-orange)
![Solana](https://img.shields.io/badge/Solana-Devnet-purple)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## 🌅 Built for DAWN

CypherVault is a privacy-first, decentralized AI assistant that runs entirely on your DAWN Black Box. It combines local AI processing with Solana blockchain to create a truly cypherpunk experience.

## ✨ Features

### 🤖 Local AI Processing
- Uses Ollama for completely private AI inference
- Streaming responses for real-time interaction
- No data ever leaves your Black Box

### 🔗 Solana Blockchain Integration
- Knowledge shared as on-chain records (dApp!)
- Wallet-based authentication (Phantom/Solflare)
- Decentralized storage architecture

### 🔐 End-to-End Encryption
- AES-256 encryption for all messages
- RSA-2048 for P2P key exchange
- Zero-knowledge proofs for authentication

### 🌐 P2P Mesh Networking
- Black Boxes form decentralized network
- Direct node-to-node communication
- Reputation-based trust system

### 🛡️ Zero-Knowledge Proofs
- Advanced cryptographic authentication
- Prove identity without revealing secrets
- On-chain verification

## 🎯 Why Every Black Box Needs CypherVault

1. **Data Sovereignty** - Your conversations never leave your device
2. **True Decentralization** - No central server, pure P2P + blockchain
3. **Cypherpunk Values** - Privacy, cryptography, and freedom by design
4. **DePIN Ready** - Built specifically for DAWN's decentralized network

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose
- Phantom Wallet (browser extension)

### Run on Black Box
```bash
# Clone repository
git clone https://github.com/yourusername/cyphervault.git
cd cyphervault

# Build and start
docker-compose up -d

# Wait for Ollama to download model (first time only)
docker-compose exec ollama ollama pull llama3.2:3b

# Access at http://localhost:8000