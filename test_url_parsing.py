"""
Script para testar o parsing da DATABASE_URL
"""
from urllib.parse import urlparse, unquote

# Exemplos de URLs problemáticas
test_urls = [
    "postgresql://user:pass@host.com:5432/db",
    "postgresql://user:p@ss$word@host.com:5432/db",
    "postgresql://user:MyP@ss%24word@host.com:5432/db",
]

for url in test_urls:
    print(f"\n🔍 Testing URL: {url}")
    parsed = urlparse(url)
    
    print(f"  Host: {parsed.hostname}")
    print(f"  Port: {parsed.port or 5432}")
    print(f"  Database: {parsed.path.lstrip('/')}")
    print(f"  User: {unquote(parsed.username) if parsed.username else None}")
    print(f"  Password: {unquote(parsed.password) if parsed.password else None}")
