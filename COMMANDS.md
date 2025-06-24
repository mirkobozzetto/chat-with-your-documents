# 🛠️ Commandes Utiles - Autonomie

## 🐳 Docker

### Gestion des containers

```bash
# Voir les containers
docker ps -a

# Logs d'un container
docker logs chat-with-your-documents-rag-app-1 --tail 50
docker logs chat-with-your-documents-rag-app-1 -f  # En temps réel

# Arrêter tout
docker-compose down

# Rebuilder après changements
docker-compose build --no-cache rag-app

# Redémarrer
docker-compose up -d
```

### Commandes rapides

```bash
# Tout en une fois
make down && make build && make up

# Ou avec docker-compose
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

## 🗄️ Base de données

### Gestion utilisateurs

```bash
# Créer un utilisateur
make create-user USER=admin PASS=motdepasse123

# Initialiser la DB
make init-db

# Migrer de JSON vers PostgreSQL
make migrate-auth
```

### Connection directe PostgreSQL

```bash
# Depuis l'extérieur
psql -h localhost -p 5433 -U chat_with_your_documents -d chat_with_your_documents

# Depuis Docker
docker exec -it chat-with-your-documents-postgres-1 psql -U chat_with_your_documents -d chat_with_your_documents
```

### Requêtes SQL utiles

```sql
-- Voir les utilisateurs
SELECT * FROM users;

-- Compter les utilisateurs actifs
SELECT COUNT(*) FROM users WHERE is_active = true;

-- Supprimer un utilisateur
DELETE FROM users WHERE username = 'toto';
```

## 🔐 Authentification

### Debugging auth

```bash
# Vider les sessions persistantes
echo '{}' > auth_sessions.json

# Voir le contenu
cat auth_sessions.json

# Logs d'auth en temps réel
docker logs chat-with-your-documents-rag-app-1 -f | grep "🔐\|❌\|✅"
```

### Fichiers importants

```bash
# Voir qui utilise quoi
grep -r "AuthManager\|DBAuthManager" src/

# Vérifier l'import
head -10 src/ui/components/auth_component.py
```

## 🔍 Debugging

### Recherche dans le code

```bash
# Trouver un pattern
grep -r "pattern" src/

# Chercher dans les logs
docker logs chat-with-your-documents-rag-app-1 | grep "ERROR\|FATAL"

# Vérifier les imports
find src/ -name "*.py" -exec grep -l "import.*Auth" {} \;
```

### Status général

```bash
# Vérifier tout
docker ps && docker logs chat-with-your-documents-rag-app-1 --tail 5

# Ports occupés
lsof -i :8501
lsof -i :5433
```

## 🚀 Redémarrage complet

```bash
# Séquence complète de redémarrage
docker-compose down
docker system prune -f  # Nettoie les images
docker-compose build --no-cache
docker-compose up -d

# Attendre que tout soit up
sleep 10
docker logs chat-with-your-documents-rag-app-1 --tail 20
```

## 📊 Monitoring

### 🔥 LOGS EN TEMPS RÉEL (comme streamlit run app.py)

```bash
# Utiliser le script custom (RECOMMANDÉ)
./docker-logs.sh

# Ou directement
docker logs chat-with-your-documents-rag-app-1 -f --timestamps
```

### Vérifier les services

```bash
# Santé des containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Usage ressources
docker stats --no-stream

# Logs avec filtre auth/erreurs
docker logs chat-with-your-documents-rag-app-1 -f | grep -E "(🔐|❌|✅|ERROR|FATAL)"
```

## 🆘 Dépannage rapide

### Container ne démarre pas

```bash
# Vérifier les erreurs
docker logs chat-with-your-documents-rag-app-1

# Rebuild forcé
docker-compose down
docker rmi chat-with-your-documents-rag-app
docker-compose build --no-cache
```

### Problème de DB

```bash
# Vérifier PostgreSQL
docker exec chat-with-your-documents-postgres-1 pg_isready

# Recréer la DB
docker-compose down
docker volume rm chat-with-your-documents_postgres_data
docker-compose up -d
make init-db
```

### Sessions problématiques

```bash
# Reset complet des sessions
echo '{}' > auth_sessions.json
docker-compose restart rag-app
```

## 🏃‍♂️ Workflow quotidien

1. **Développement** : Modifier le code
2. **Test local** : `streamlit run app.py`
3. **Rebuild Docker** : `make build`
4. **Déployer** : `make up`
5. **Vérifier** : `docker logs chat-with-your-documents-rag-app-1 --tail 10`

## 📍 URLs importantes

- **Local** : http://localhost:8502
- **Docker** : http://localhost:8501
- **PostgreSQL** : localhost:5433
