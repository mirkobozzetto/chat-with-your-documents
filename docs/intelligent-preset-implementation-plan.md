# Plan d'Implémentation : Presets Intelligents avec Pédagogie & Coûts

## Analyse du Code Actuel

### Architecture Complexe Identifiée
- **12 fichiers impliqués** dans la configuration des presets
- **6 presets** avec paramètres redondants et coûts cachés
- **Interface éclatée** : 50+ options sans guidance utilisateur
- **Aucune estimation de coût** pour les stratégies agentiques/contextual

### Problèmes Critiques
1. **Stratégies agentiques** (`agentic_*`) = appels LLM non documentés → coût 10-50x
2. **Contextual RAG** = preprocessing + storage 2-3x → coût caché
3. **Neural reranking** = calcul intensif → latence non documentée
4. **Presets Academic/Creative** = échec scoring garanti (tailles > 1500)

## Solutions d'Implémentation

### 1. Smart Document Analysis & Recommendations

#### A. Détection Automatique des Besoins
```python
# src/document_management/document_analyzer.py
class SmartDocumentAnalyzer:
    def analyze_document_requirements(self, file_path: str) -> Dict[str, Any]:
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        token_estimate = file_size * 150  # approximation tokens/MB
        
        # Analyse basée sur taille et type
        if token_estimate > 200000:  # >200k tokens
            return {
                "recommended_preset": "contextual_large",
                "reasoning": "Document volumineux détecté - Contextual RAG recommandé",
                "cost_estimate": "€20-50 par traitement",
                "alternative": "Utiliser 'Standard' pour €1-2 par traitement"
            }
        elif file_size > 50:  # >50MB
            return {
                "recommended_preset": "agentic_premium", 
                "reasoning": "Gros fichier complexe - Chunking intelligent recommandé",
                "cost_estimate": "€15-30 par traitement",
                "alternative": "Utiliser 'Standard' si budget limité"
            }
        else:
            return {
                "recommended_preset": "standard",
                "reasoning": "Taille standard - Mode économique suffisant",
                "cost_estimate": "€1-3 par traitement"
            }
```

#### B. Interface Pédagogique avec Warnings
```python
# src/ui/components/smart_preset_selector.py
class SmartPresetSelector:
    def render_intelligent_selection(self, document_analysis: Dict) -> str:
        st.subheader("🎯 Sélection Intelligente de Preset")
        
        # Affichage recommandation
        rec = document_analysis["recommended_preset"]
        st.success(f"💡 Recommandé : **{rec}**")
        st.info(f"📝 Raison : {document_analysis['reasoning']}")
        
        # Warning coût
        if "premium" in rec or "contextual" in rec:
            st.warning(f"💰 Coût estimé : {document_analysis['cost_estimate']}")
            st.info(f"💡 Alternative économique : {document_analysis['alternative']}")
        
        # Sélecteur avec aide contextuelle
        preset_choice = st.radio(
            "Choisir le niveau de traitement :",
            options=["Standard (€1-3)", "Premium (€15-30)", "Ultra (€20-50)"],
            help="Standard = Rapide et fiable | Premium = Chunking intelligent | Ultra = Recherche contextuelle"
        )
        
        return self._map_choice_to_preset(preset_choice)
```

### 2. Presets Simplifiés avec Coûts Transparents

#### A. Nouvelle Structure (3 Presets)
```python
# src/ui/components/simplified_presets.py
INTELLIGENT_PRESETS = {
    "standard": {
        "display_name": "📋 Standard",
        "description": "Chunking fiable, résultats garantis",
        "cost_range": "€1-3 par document",
        "processing_time": "30 secondes - 2 minutes",
        "use_cases": ["Documents PDF normaux", "Premiers tests", "Budget limité"],
        "config": {
            "chunk_strategy": "recursive",
            "chunk_size": 1200,
            "chunk_overlap": 200,
            "enable_contextual_rag": False,
            "use_neural_reranker": False
        },
        "quality_score_expected": "0.65-0.75"
    },
    
    "premium": {
        "display_name": "🧠 Premium",
        "description": "Chunking intelligent pour gros fichiers",
        "cost_range": "€15-30 par document",
        "processing_time": "3-8 minutes",
        "use_cases": ["Livres >200 pages", "Documents structurés complexes", "Précision importante"],
        "config": {
            "chunk_strategy": "agentic_context",
            "chunk_size": 1500,
            "chunk_overlap": 250,
            "enable_contextual_rag": False,
            "use_neural_reranker": True
        },
        "quality_score_expected": "0.70-0.80",
        "warning": "⚠️ Utilise des appels LLM - coût élevé"
    },
    
    "ultra": {
        "display_name": "🚀 Ultra",
        "description": "Recherche contextuelle pour documents critiques",
        "cost_range": "€20-50 par document", 
        "processing_time": "5-15 minutes",
        "use_cases": ["Documents >500 pages", "Recherche très précise", "Applications critiques"],
        "config": {
            "chunk_strategy": "agentic_context",
            "chunk_size": 1200,
            "chunk_overlap": 200,
            "enable_contextual_rag": True,
            "use_neural_reranker": True,
            "dense_weight": 0.7,
            "sparse_weight": 0.3
        },
        "quality_score_expected": "0.75-0.85",
        "warning": "⚠️ Traitement le plus coûteux - réservé aux cas critiques"
    }
}
```

#### B. Interface avec Aide Contextuelle
```python
def render_preset_with_education(self) -> str:
    st.subheader("🎛️ Choisir le Niveau de Traitement")
    
    for preset_key, preset in INTELLIGENT_PRESETS.items():
        with st.expander(f"{preset['display_name']} - {preset['description']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Coût :** {preset['cost_range']}")
                st.write(f"**Temps :** {preset['processing_time']}")
                st.write(f"**Score qualité attendu :** {preset['quality_score_expected']}")
                
                st.write("**Idéal pour :**")
                for use_case in preset["use_cases"]:
                    st.write(f"• {use_case}")
            
            with col2:
                if st.button(f"Utiliser {preset['display_name']}", key=f"btn_{preset_key}"):
                    if preset.get("warning"):
                        if st.warning(preset["warning"]):
                            return preset_key
                    else:
                        return preset_key
    
    return None
```

### 3. Optimisation du Code Backend

#### A. Simplification Config (config.py)
```python
# config.py - Version simplifiée
# Suppression des paramètres redondants
PRESET_MODE = os.getenv("PRESET_MODE", "standard")  # standard|premium|ultra
ENABLE_COST_TRACKING = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"

# Suppression de ces variables complexes :
# - DENSE_WEIGHT, SPARSE_WEIGHT (calculés automatiquement)
# - RRF_K (valeur fixe optimale)
# - RELEVANCE_WEIGHT, ORIGINAL_WEIGHT (presets gèrent)
```

#### B. Consolidation DocumentProcessorManager
```python
# src/rag_system/document_processor_manager.py - Simplifié
class DocumentProcessorManager:
    def __init__(self, preset_config: Dict[str, Any], **kwargs):
        self.preset_config = preset_config
        self.cost_tracker = CostTracker() if ENABLE_COST_TRACKING else None
        
        # Initialisation basée sur preset seulement
        strategy = preset_config["chunk_strategy"]
        if strategy == "agentic_context":
            self._init_agentic_processor()
        else:
            self._init_standard_processor()
    
    def process_document_pipeline(self, file_path: str, **kwargs) -> Tuple[List[Document], bool, Dict]:
        start_time = time.time()
        
        chunks, should_vectorize = super().process_document_pipeline(file_path, **kwargs)
        
        processing_stats = {
            "processing_time": time.time() - start_time,
            "estimated_cost": self._calculate_processing_cost(chunks),
            "chunk_count": len(chunks),
            "preset_used": self.preset_config["display_name"]
        }
        
        return chunks, should_vectorize, processing_stats
```

#### C. Suppression Fichiers Redondants
```python
# Fichiers à supprimer/simplifier :
# - src/document_management/agentic_document_processor.py (intégrer dans document_processor.py)
# - src/services/config_service.py (logique dans advanced_controls.py)
# - Simplifier src/ui/components/advanced_controls.py (mode expert uniquement)

# Garder seulement :
# - src/document_management/document_processor.py (unifié)
# - src/rag_system/document_processor_manager.py (orchestrateur)
# - src/ui/components/smart_preset_selector.py (nouveau)
```

### 4. Tracking des Coûts et Performance

#### A. Cost Tracker Intégré
```python
# src/utils/cost_tracker.py
class CostTracker:
    def track_llm_calls(self, strategy: str, tokens_used: int) -> float:
        rates = {
            "agentic_context": 0.002 * 10,  # GPT-4 + overhead agentique
            "contextual_preprocessing": 0.002 * 3,  # GPT-4 pour contexte
            "neural_reranking": 0.001  # Calcul local mais temps machine
        }
        return tokens_used * rates.get(strategy, 0)
    
    def estimate_document_cost(self, file_size_mb: float, preset: str) -> Dict:
        base_costs = {
            "standard": file_size_mb * 0.02,
            "premium": file_size_mb * 0.50,  
            "ultra": file_size_mb * 1.20
        }
        
        return {
            "estimated_cost_euros": base_costs[preset],
            "breakdown": self._get_cost_breakdown(preset),
            "processing_time_minutes": self._estimate_time(file_size_mb, preset)
        }
```

#### B. Interface de Feedback Coûts
```python
def show_processing_results(self, stats: Dict):
    st.success(f"✅ Document traité avec succès !")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Chunks créés", stats["chunk_count"])
    with col2:
        st.metric("Temps de traitement", f"{stats['processing_time']:.1f}s")
    with col3:
        st.metric("Coût estimé", f"€{stats['estimated_cost']:.2f}")
    
    if stats["preset_used"] in ["Premium", "Ultra"]:
        st.info(f"💡 Mode {stats['preset_used']} utilisé - Qualité optimisée")
```

## Plan d'Implémentation en 3 Phases

### Phase 1 : Interface Intelligente (Semaine 1)
1. **Créer** `SmartPresetSelector` avec 3 presets simplifiés
2. **Ajouter** détection automatique taille document → recommandation
3. **Implémenter** warnings coût et temps de traitement
4. **Tester** avec documents existants

### Phase 2 : Backend Optimisé (Semaine 2)
1. **Simplifier** `config.py` → suppression variables redondantes
2. **Refactorer** `DocumentProcessorManager` → preset-driven
3. **Intégrer** `CostTracker` pour transparence coûts
4. **Supprimer** fichiers redondants identifiés

### Phase 3 : UX Finale (Semaine 3)
1. **Mode Expert** derrière expander pour utilisateurs avancés
2. **Tooltips pédagogiques** sur impact des paramètres
3. **Feedback post-traitement** avec métriques coût/performance
4. **Tests utilisateur** et ajustements

## Résultats Attendus

### Simplification UX
- **Réduction 80%** du temps de configuration utilisateur
- **3 choix clairs** au lieu de 50+ paramètres
- **Guidance automatique** basée sur type de document

### Transparence Coûts
- **Estimation avant traitement** pour éviter surprises
- **Tracking temps réel** des coûts LLM
- **Comparaison modes** pour choix éclairé

### Performance Code
- **Suppression 30%** du code redondant
- **Architecture simplifiée** avec responsabilités claires
- **Maintenance facilitée** avec moins de fichiers

Cette approche transforme un système complexe en interface intuitive tout en préservant la puissance pour les experts via le mode avancé.