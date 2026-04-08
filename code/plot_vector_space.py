import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import ollama

# Importa il tuo database reale
try:
    from db_query import INTENT_SENTENCES
except ImportError:
    print("Errore: Impossibile trovare 'db_query.py'. Assicurati di essere nella cartella corretta.")
    sys.exit(1)

# ==========================================
# CONFIGURAZIONE
# ==========================================
EMBEDDING_MODEL = 'nomic-embed-text' # Lo stesso usato nel tuo VectorStore

COLORS = {
    'coding':  '#4da6ff',  # Azzurro
    'math':    '#4dff4d',  # Verde fluo
    'rights':  '#ff4d4d',  # Rosso acceso
    'general': '#ffaa00'   # Arancione brillante
}

plt.style.use('dark_background')

# ==========================================
# 1. ESTRAZIONE ED EMBEDDING
# ==========================================
print("⚙️ Inizio analisi del database reale...")

sentences = []
labels = []
vectors = []

# Conta totale per log
total_sentences = sum(len(frasi) for frasi in INTENT_SENTENCES.values())
processed = 0

for domain, frasi in INTENT_SENTENCES.items():
    print(f"➜ Calcolo embedding per il modulo [{domain.upper()}]...")
    for text in frasi:
        try:
            # Chiama Ollama per ottenere il vettore reale a 768 dimensioni
            response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
            vec = response['embedding']
            
            vectors.append(vec)
            labels.append(domain)
            sentences.append(text)
            
            processed += 1
            print(f"\rProgresso: {processed}/{total_sentences}", end="", flush=True)
        except Exception as e:
            print(f"\nErrore durante l'embedding di: '{text[:30]}...' -> {e}")

print("\n\n⚙️ Riduzione dimensionale (PCA da 768 a 2 dimensioni)...")
X = np.array(vectors)

# Normalizzazione L2 (la stessa che usi in vector_store.py)
norms = np.linalg.norm(X, axis=1, keepdims=True)
X_normalized = np.where(norms == 0, X, X / norms)

# Applica la PCA per ridurre a 2D
pca = PCA(n_components=2, random_state=42)
X_2d = pca.fit_transform(X_normalized)

# ==========================================
# 2. PLOT INTERATTIVO
# ==========================================
fig, ax = plt.subplots(figsize=(14, 10))
fig.patch.set_facecolor('#121212')
ax.set_facecolor('#121212')

plt.title(f"Spazio Vettoriale Reale ({total_sentences} frasi) - {EMBEDDING_MODEL}", fontsize=16, pad=20, color='white')

# Disegna i punti suddivisi per dominio
scatters = []
for domain in COLORS.keys():
    # Trova gli indici dei punti appartenenti a questo dominio
    idx = [i for i, label in enumerate(labels) if label == domain]
    
    if not idx:
        continue
        
    sc = ax.scatter(
        X_2d[idx, 0], 
        X_2d[idx, 1], 
        c=COLORS[domain], 
        label=domain.upper(), 
        alpha=0.8, 
        edgecolors='#121212', 
        linewidth=0.5,
        s=70 
    )
    scatters.append((sc, domain, idx))

# Configurazione Assi e Griglia
plt.axhline(0, color='#444444', linewidth=1, alpha=0.8)
plt.axvline(0, color='#444444', linewidth=1, alpha=0.8)
plt.xlabel(f"Dimensione Principale 1 (Varianza: {pca.explained_variance_ratio_[0]*100:.1f}%)", fontsize=12, color='#cccccc')
plt.ylabel(f"Dimensione Principale 2 (Varianza: {pca.explained_variance_ratio_[1]*100:.1f}%)", fontsize=12, color='#cccccc')

plt.grid(True, linestyle=':', color='#333333', alpha=0.8)
legend = plt.legend(loc='best', fontsize=12, title="Domini", facecolor='#1e1e1e', edgecolor='#444444')
plt.setp(legend.get_texts(), color='white')
plt.setp(legend.get_title(), color='white')

ax.tick_params(axis='x', colors='#cccccc')
ax.tick_params(axis='y', colors='#cccccc')
for spine in ax.spines.values():
    spine.set_edgecolor('#444444')

# ==========================================
# 3. GESTIONE TOOLTIP (HOVER)
# ==========================================
annot = ax.annotate(
    "", xy=(0,0), xytext=(15,15), textcoords="offset points",
    bbox=dict(boxstyle="round4,pad=0.5", fc="#1e1e1e", ec="#cccccc", lw=1, alpha=0.95),
    color="white", fontsize=10, zorder=100
)
annot.set_visible(False)

def update_annot(sc, ind, domain, indices):
    """Aggiorna il testo e la posizione del tooltip."""
    pos = sc.get_offsets()[ind["ind"][0]]
    annot.xy = pos
    
    # Recupera il testo reale della frase
    real_index = indices[ind["ind"][0]]
    text = sentences[real_index]
    
    # Formatta il testo per non farlo uscire dallo schermo (a capo ogni ~50 caratteri)
    import textwrap
    wrapped_text = "\n".join(textwrap.wrap(text, width=60))
    
    annot.set_text(f"[{domain.upper()}]\n{wrapped_text}")
    annot.get_bbox_patch().set_edgecolor(COLORS[domain])

def hover(event):
    """Evento scatenato dal movimento del mouse."""
    vis = annot.get_visible()
    if event.inaxes == ax:
        for sc, domain, indices in scatters:
            cont, ind = sc.contains(event)
            if cont:
                update_annot(sc, ind, domain, indices)
                annot.set_visible(True)
                fig.canvas.draw_idle()
                return
    if vis:
        annot.set_visible(False)
        fig.canvas.draw_idle()

fig.canvas.mpl_connect("motion_notify_event", hover)

plt.tight_layout()
print("\n✅ Calcolo completato! Generazione del grafico interattivo in corso...")
plt.show()