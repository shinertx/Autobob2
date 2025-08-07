# 🚀 V26MEME Production Deployment Guide

## 📋 Fresh Instance Setup (Recommended)

### Step 1: Initial Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y git curl build-essential pkg-config libssl-dev python3 python3-pip python3-venv

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Install Go
wget https://golang.org/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for docker group changes
```

### Step 2: Clone and Setup V26MEME
```bash
# Clone the repository
git clone https://github.com/shinertx/Autobob2.git
cd Autobob2

# Run automated setup
chmod +x setup.sh
./setup.sh

# Copy your API keys to .env
cp .env.example .env
# Edit .env with your real API keys (see API_KEYS_TODO.md)
nano .env
```

### Step 3: Configure Your API Keys
```bash
# Edit the .env file with your real keys:
nano .env

# Required updates:
# OPENAI_API_KEY=your_real_openai_key
# COINBASE_API_KEY=your_real_coinbase_key  
# COINBASE_SECRET=your_real_coinbase_secret
# KRAKEN_API_KEY=your_real_kraken_key
# KRAKEN_SECRET=your_real_kraken_secret
# INFURA_API_KEY=your_real_infura_key
# ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/your_infura_key
# FLASHBOTS_SIGNER_KEY=your_ethereum_private_key
# WALLET_PRIVATE_KEY=your_wallet_private_key
```

### Step 4: Start the System
```bash
# Start infrastructure (databases)
docker-compose up -d

# Wait for databases to initialize (30 seconds)
sleep 30

# Start V26MEME
python3 main.py
```

### Step 5: Verify Deployment
```bash
# Check processes
ps aux | grep -E "(discovery|execution|python.*main)"

# Check dashboard
curl http://localhost:5001/api/stats

# Monitor logs
tail -f v26meme.log
```

## 🌐 Access URLs
- **Dashboard**: http://your_server_ip:5001
- **API**: http://your_server_ip:5001/api/

## 🛡️ Production Security

### Firewall Setup
```bash
# Install UFW
sudo ufw enable

# Allow SSH (change port if needed)
sudo ufw allow 22/tcp

# Allow dashboard (restrict to your IP)
sudo ufw allow from YOUR_IP_ADDRESS to any port 5001

# Allow HTTPS for API callbacks
sudo ufw allow 443/tcp
```

### SSL/HTTPS (Optional)
```bash
# Install certbot for SSL certificates
sudo apt install certbot

# Get SSL certificate (if you have a domain)
sudo certbot --standalone -d yourdomain.com
```

## 📊 Monitoring & Maintenance

### System Monitoring
```bash
# Check system resources
htop

# Monitor V26MEME logs
tail -f v26meme.log

# Check database status
docker exec v26meme_db psql -U v26meme -d v26meme_db -c "SELECT COUNT(*) FROM discovered_patterns;"
```

### Backup Strategy
```bash
# Backup database daily
docker exec v26meme_db pg_dump -U v26meme v26meme_db > backup_$(date +%Y%m%d).sql

# Backup .env file (encrypted)
gpg -c .env -o env_backup_$(date +%Y%m%d).gpg
```

## 🚀 Going Live

### Switch to Live Trading (When Ready)
```bash
# Edit .env file
nano .env

# Change these settings:
ENABLE_PAPER_TRADING=false
ENABLE_REAL_TRADING=true
ENABLE_MEV_BOT=true
ENABLE_ARBITRAGE=true
ENABLE_TOKEN_SNIPING=true
ENABLE_MARKET_MAKING=true

# Restart system
pkill -f "python3 main.py"
python3 main.py
```

## ⚠️ Safety Checklist Before Going Live

- [ ] All API keys tested and verified
- [ ] Paper trading shows profitable patterns
- [ ] Risk management limits configured
- [ ] Monitoring and alerts set up
- [ ] Backup strategy implemented
- [ ] Emergency stop procedures tested
- [ ] Starting with minimal capital ($200)

## 🆘 Emergency Procedures

### Emergency Stop
```bash
# Stop all trading immediately
pkill -f "python3 main.py"
pkill -f "discovery_engine"
pkill -f "execution_engine"

# Check for open positions
curl http://localhost:5001/api/positions
```

### Quick Restart
```bash
# Restart infrastructure
docker-compose restart

# Restart V26MEME
python3 main.py
```

## 📞 Support

- **GitHub**: https://github.com/shinertx/Autobob2
- **Documentation**: API_KEYS_TODO.md
- **Logs**: v26meme.log

---

🎯 **Remember**: Start with paper trading and small amounts. The system is designed to be profitable, but crypto trading always carries risk.
