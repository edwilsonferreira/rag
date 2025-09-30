# Guia: Como Atualizar o Projeto no GitHub

## 🔄 Atualizando Repositório Existente no GitHub

### 1️⃣ **Configurar Remote (Primeira vez)**

```bash
# Substitua pela URL do seu repositório GitHub
git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git

# Verificar se foi adicionado corretamente
git remote -v
```

### 2️⃣ **Configurar Usuário Git (Se necessário)**

```bash
# Configure seu nome e email (global ou por projeto)
git config user.name "Seu Nome"
git config user.email "seu.email@exemplo.com"
```

### 3️⃣ **Fazer Commit das Mudanças**

```bash
# Verificar arquivos que serão commitados
git status

# Fazer commit com mensagem descritiva
git commit -m "feat: Sistema RAG v2.2 - Correções importantes

✅ Correção das citações 'Documento X, Página N/A'  
✅ Sistema de conhecimento externo com Wikipedia
✅ Metadados corretos com nomes de arquivos reais
✅ Logging aprimorado com métricas de qualidade
✅ Fallback estruturado para respostas incompletas
✅ Suporte melhorado para PDF + Markdown

Detalhes técnicos:
- Refatoração da função _create_chunks()
- Nova classe ExternalKnowledgeProvider  
- Diretiva de segurança flexível
- 480 chunks processados corretamente"
```

### 4️⃣ **Sincronizar com GitHub**

#### **Opção A: Se o repositório GitHub está vazio ou é novo**
```bash
# Push inicial
git branch -M main
git push -u origin main
```

#### **Opção B: Se o repositório GitHub já tem conteúdo**
```bash
# Buscar mudanças do GitHub primeiro
git fetch origin

# Mesclar com o conteúdo existente (se houver conflitos, resolva-os)
git pull origin main --allow-unrelated-histories

# Fazer push das suas mudanças
git push origin main
```

### 5️⃣ **Comandos de Verificação**

```bash
# Verificar status após push
git status

# Ver histórico de commits
git log --oneline -5

# Verificar se o push foi bem-sucedido
git remote show origin
```

## 🚀 **Execução Rápida**

Se você souber a URL do seu repositório, execute:

```bash
cd /Users/ed/Downloads/rag-main

# 1. Adicionar remote (substitua pela URL real)
git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git

# 2. Configurar usuário
git config user.name "Seu Nome"
git config user.email "seu.email@exemplo.com"

# 3. Commit
git commit -m "feat: Sistema RAG v2.2 - Melhorias importantes"

# 4. Push (escolha A ou B conforme situação)
git push -u origin main  # Para repo novo
# OU
git pull origin main --allow-unrelated-histories && git push origin main  # Para repo existente
```

## ⚠️ **Possíveis Problemas e Soluções**

### **Erro: "remote origin already exists"**
```bash
git remote remove origin
git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
```

### **Erro: "failed to push some refs"**
```bash
git pull origin main --allow-unrelated-histories
git push origin main
```

### **Conflitos de Merge**
```bash
# Resolver conflitos manualmente nos arquivos indicados
# Depois:
git add .
git commit -m "resolve: Conflitos resolvidos"
git push origin main
```

## 📋 **Checklist Final**

- [ ] Remote configurado com URL correta
- [ ] Usuário Git configurado  
- [ ] Arquivos importantes no .gitignore
- [ ] Commit feito com mensagem descritiva
- [ ] Push bem-sucedido para GitHub
- [ ] Repositório GitHub atualizado com as melhorias

## 🎯 **Próximos Passos Após Push**

1. **Verificar no GitHub** se todos os arquivos foram enviados
2. **Atualizar README.md** no GitHub se necessário
3. **Criar Release/Tag** para marcar a versão v2.2
4. **Documentar** as mudanças no GitHub Issues/Wiki

---

💡 **Dica:** Mantenha commits frequentes e organizados para facilitar o tracking das mudanças!