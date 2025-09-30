# Guia de Configuração do Arquivo .env

Este sistema agora usa um arquivo `.env` para armazenar a chave de API do Google Gemini de forma segura.

## ✅ **Passos para Configurar:**

### 1. **Configure sua chave de API**
Edite o arquivo `.env` na raiz do projeto e adicione sua chave real:

```bash
# Google Gemini API Key
GOOGLE_API_KEY=SUA_CHAVE_REAL_AQUI
```

### 2. **Obtenha sua chave de API**
- Acesse: https://makersuite.google.com/app/apikey
- Faça login com sua conta Google
- Crie uma nova chave de API
- Copie a chave gerada

### 3. **Instale a dependência (se necessário)**
```bash
pip install python-dotenv
```

## 🔧 **Como Funciona:**

- ✅ **Chave de API:** Carregada do arquivo `.env` (seguro)
- ✅ **Outras configurações:** Definidas no `config.py` (fácil de gerenciar)
- ✅ **Controle de versão:** `.env` está no `.gitignore` (não será enviado para o Git)

## 📝 **Exemplo do arquivo .env:**

```
GOOGLE_API_KEY=AIzaSyDXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

## ⚠️ **Importante:**
- **NUNCA** compartilhe seu arquivo `.env`
- **NUNCA** faça commit do arquivo `.env` no Git
- Mantenha sua chave de API privada e segura