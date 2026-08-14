"""
Generate Galarix Architecture Block Diagram as PDF for MSME Hackathon.
No name or contact details in the file.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(1, 1, figsize=(16, 22))
ax.set_xlim(0, 16)
ax.set_ylim(0, 22)
ax.axis('off')
fig.patch.set_facecolor('#0f172a')

# ── Color Palette ──
C_BG = '#0f172a'
C_CARD = '#1e293b'
C_BORDER = '#334155'
C_ACCENT = '#6366f1'  # indigo
C_GREEN = '#10b981'
C_CYAN = '#06b6d4'
C_PINK = '#ec4899'
C_AMBER = '#f59e0b'
C_WHITE = '#f8fafc'
C_GRAY = '#94a3b8'
C_RED = '#ef4444'

def draw_box(x, y, w, h, label, sublabel="", color=C_ACCENT, text_color=C_WHITE):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor='white', linewidth=1.2, alpha=0.9)
    ax.add_patch(box)
    if sublabel:
        ax.text(x + w/2, y + h/2 + 0.18, label, ha='center', va='center',
                fontsize=9, fontweight='bold', color=text_color, family='sans-serif')
        ax.text(x + w/2, y + h/2 - 0.18, sublabel, ha='center', va='center',
                fontsize=6.5, color=C_GRAY, family='sans-serif')
    else:
        ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                fontsize=9, fontweight='bold', color=text_color, family='sans-serif')

def draw_arrow(x1, y1, x2, y2, color=C_GRAY):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5))

def draw_section_title(x, y, title, color=C_WHITE):
    ax.text(x, y, title, ha='center', va='center',
            fontsize=13, fontweight='bold', color=color, family='sans-serif')

# ════════════════════════════════════════════════
# TITLE
# ════════════════════════════════════════════════
ax.text(8, 21.3, "GALARIX", ha='center', va='center',
        fontsize=28, fontweight='bold', color=C_ACCENT, family='sans-serif')
ax.text(8, 20.8, "AI-Powered Synthetic Data Engine — System Architecture", ha='center', va='center',
        fontsize=11, color=C_GRAY, family='sans-serif')

# ════════════════════════════════════════════════
# ROW 1: USER INPUT
# ════════════════════════════════════════════════
draw_box(5.5, 19.5, 5, 0.9, 'USER PROMPT', '"Generate 10K credit card txns for India"', C_PINK)

draw_arrow(8, 19.5, 8, 18.9, C_PINK)

# ════════════════════════════════════════════════
# ROW 2: STAGE 0.5 — AI/NLP ENGINE
# ════════════════════════════════════════════════
draw_section_title(2.5, 18.55, "STAGE 0.5", C_CYAN)
draw_box(4, 18.0, 8, 0.9, 'AI/NLP ENGINE (Google Gemini LLM)', 'Intent Classification | Entity Extraction | Schema Generation', C_CYAN)

draw_arrow(8, 18.0, 8, 17.4, C_CYAN)

# ════════════════════════════════════════════════
# ROW 3: STAGE 1 — PROMPT FIREWALL + CONTRACT
# ════════════════════════════════════════════════
draw_section_title(2.5, 17.05, "STAGE 1", C_RED)

draw_box(4, 16.5, 3.5, 0.9, 'PROMPT FIREWALL', 'Injection Detection | PII Scan', C_RED)
draw_box(8.5, 16.5, 3.5, 0.9, 'CONTRACT BUILDER', 'AST Parser | Validation', '#7c3aed')

draw_arrow(7.5, 16.95, 8.5, 16.95, C_GRAY)
draw_arrow(8, 16.5, 8, 15.9, C_GRAY)

# ════════════════════════════════════════════════
# ROW 4: STAGE 1.5 — SCHEMA REGISTRY + ENRICHMENT
# ════════════════════════════════════════════════
draw_section_title(2.5, 15.55, "STAGE 1.5", C_AMBER)

draw_box(4, 15.0, 3.5, 0.9, 'SCHEMA REGISTRY', '15+ Entity Schemas | 7 Regions', C_AMBER)
draw_box(8.5, 15.0, 3.5, 0.9, 'ENRICHMENT ENGINE', 'Variable Resolution | Constraints', '#d97706')

draw_arrow(7.5, 15.45, 8.5, 15.45, C_GRAY)
draw_arrow(8, 15.0, 8, 14.4, C_GRAY)

# ════════════════════════════════════════════════
# ROW 5: STAGE 2 — STATISTICAL MODEL BUILDER
# ════════════════════════════════════════════════
draw_section_title(2.5, 14.05, "STAGE 2", C_GREEN)

draw_box(4, 13.5, 8, 0.9, 'STATISTICAL MODEL BUILDER',
         'Distribution Fitting | Covariance Matrix | Dependency Graph | Black Swan Morphing', C_GREEN)

draw_arrow(8, 13.5, 8, 12.9, C_GREEN)

# ════════════════════════════════════════════════
# ROW 6: STAGE 3 — GENERATION ENGINE (expanded)
# ════════════════════════════════════════════════
draw_section_title(2.5, 12.55, "STAGE 3", C_ACCENT)

# Section background
section_bg = FancyBboxPatch((3.5, 8.8), 9.5, 3.5, boxstyle="round,pad=0.2",
                            facecolor='#1e1e3f', edgecolor=C_ACCENT, linewidth=1.5, alpha=0.5)
ax.add_patch(section_bg)
ax.text(8, 12.0, "DATA GENERATION ENGINE", ha='center', va='center',
        fontsize=11, fontweight='bold', color=C_ACCENT, family='sans-serif')

# Sub-engines (2 rows of 3)
draw_box(4.0, 11.0, 2.7, 0.7, 'SEED ENGINE', 'Deterministic RNG', '#4f46e5')
draw_box(7.0, 11.0, 2.7, 0.7, 'MARGINAL SAMPLER', 'Distribution Sampling', '#4f46e5')
draw_box(10.0, 11.0, 2.7, 0.7, 'CORRELATION WEAVER', 'Copula Binding', '#4f46e5')

draw_box(4.0, 9.8, 2.7, 0.7, 'CONDITIONAL ENGINE', 'Business Rules', '#4f46e5')
draw_box(7.0, 9.8, 2.7, 0.7, 'ANOMALY INJECTOR', 'Fraud/Outlier Injection', '#4f46e5')
draw_box(10.0, 9.8, 2.7, 0.7, 'CONSTRAINT ENFORCER', 'Bounds & Uniqueness', '#4f46e5')

# Entity Consistency
draw_box(5.5, 8.9, 5.5, 0.65, 'ENTITY CONSISTENCY CACHE', 'Same entity = Same attributes across all rows', '#7c3aed')

# Arrows between sub-engines
draw_arrow(6.7, 11.35, 7.0, 11.35, C_GRAY)
draw_arrow(9.7, 11.35, 10.0, 11.35, C_GRAY)
draw_arrow(8, 11.0, 8, 10.5, C_GRAY)
draw_arrow(6.7, 10.15, 7.0, 10.15, C_GRAY)
draw_arrow(9.7, 10.15, 10.0, 10.15, C_GRAY)

draw_arrow(8, 8.8, 8, 8.2, C_ACCENT)

# ════════════════════════════════════════════════
# ROW 7: QUALITY + TRUST (side by side)
# ════════════════════════════════════════════════
draw_section_title(2.5, 7.85, "VALIDATION", C_GREEN)

draw_box(4, 7.3, 3.5, 0.9, 'QUALITY AUDITOR', 'NaN Check | Distribution Fit | Bounds', C_GREEN)
draw_box(8.5, 7.3, 3.5, 0.9, 'TRUST ENGINE', 'DPDP | GDPR | PCI-DSS Compliance', '#059669')

draw_arrow(7.5, 7.75, 8.5, 7.75, C_GRAY)
draw_arrow(8, 7.3, 8, 6.7, C_GREEN)

# ════════════════════════════════════════════════
# ROW 8: OUTPUTS
# ════════════════════════════════════════════════
draw_section_title(2.5, 6.35, "OUTPUT", C_PINK)

draw_box(3.5, 5.6, 2.8, 0.9, 'SYNTHETIC DATASET', 'CSV / JSON Export', C_PINK)
draw_box(6.8, 5.6, 2.8, 0.9, 'TRUST CERTIFICATE', 'PDF Compliance Report', '#be185d')
draw_box(10.1, 5.6, 2.8, 0.9, 'AUDIT REPORT', 'Quality Metrics', '#9d174d')

draw_arrow(6.5, 6.5, 5, 6.5, C_PINK)
draw_arrow(8, 6.7, 8, 6.5, C_PINK)
draw_arrow(9.5, 6.5, 11.5, 6.5, C_PINK)

# ════════════════════════════════════════════════
# ROW 9: FRONTEND
# ════════════════════════════════════════════════
draw_arrow(8, 5.6, 8, 5.0, C_GRAY)

frontend_bg = FancyBboxPatch((3.5, 3.5), 9.5, 1.3, boxstyle="round,pad=0.2",
                              facecolor='#1a1a2e', edgecolor=C_CYAN, linewidth=1.5, alpha=0.5)
ax.add_patch(frontend_bg)
ax.text(8, 4.55, "REACT FRONTEND", ha='center', va='center',
        fontsize=11, fontweight='bold', color=C_CYAN, family='sans-serif')

draw_box(4.0, 3.6, 2.5, 0.65, 'STUDIO', 'Prompt Interface', '#155e75')
draw_box(6.8, 3.6, 2.5, 0.65, 'DATA DASHBOARD', 'Table + Analytics', '#155e75')
draw_box(9.6, 3.6, 2.5, 0.65, 'TRUST VIEWER', 'Compliance Reports', '#155e75')

# ════════════════════════════════════════════════
# SIDE PANELS: Regional Data
# ════════════════════════════════════════════════
region_bg = FancyBboxPatch((0.3, 9.0), 2.8, 3.5, boxstyle="round,pad=0.15",
                           facecolor='#1e293b', edgecolor=C_AMBER, linewidth=1, alpha=0.7)
ax.add_patch(region_bg)
ax.text(1.7, 12.15, "REGIONAL DATA", ha='center', va='center',
        fontsize=8, fontweight='bold', color=C_AMBER, family='sans-serif')

regions = ["India (IN)", "United States (US)", "United Kingdom (UK)",
           "European Union (EU)", "Japan (JP)", "Australia (AU)", "Brazil (BR)"]
for idx, r in enumerate(regions):
    ax.text(1.7, 11.7 - idx * 0.38, r, ha='center', va='center',
            fontsize=7, color=C_GRAY, family='sans-serif')

draw_arrow(3.1, 10.5, 4.0, 10.5, C_AMBER)

# ════════════════════════════════════════════════
# SIDE PANEL: Federal Sources
# ════════════════════════════════════════════════
sources_bg = FancyBboxPatch((13.2, 9.0), 2.5, 3.5, boxstyle="round,pad=0.15",
                            facecolor='#1e293b', edgecolor=C_GREEN, linewidth=1, alpha=0.7)
ax.add_patch(sources_bg)
ax.text(14.45, 12.15, "DATA SOURCES", ha='center', va='center',
        fontsize=8, fontweight='bold', color=C_GREEN, family='sans-serif')

sources = ["RBI Bulletins", "BLS OEWS Reports", "CFPB Studies",
           "SEBI Filings", "Fed Reserve Data", "IRS Tax Tables", "IRDAI Reports"]
for idx, s in enumerate(sources):
    ax.text(14.45, 11.7 - idx * 0.38, s, ha='center', va='center',
            fontsize=7, color=C_GRAY, family='sans-serif')

draw_arrow(13.2, 10.5, 12.7, 10.5, C_GREEN)

# ════════════════════════════════════════════════
# KEY METRICS BAR
# ════════════════════════════════════════════════
metrics_bg = FancyBboxPatch((1.5, 1.8), 13, 1.2, boxstyle="round,pad=0.15",
                            facecolor='#1e293b', edgecolor=C_BORDER, linewidth=1, alpha=0.8)
ax.add_patch(metrics_bg)

metrics = [
    ("15+", "Entity Types"),
    ("7", "Global Regions"),
    ("6", "Pipeline Stages"),
    ("100%", "Data Validity"),
    ("0", "Real Data Required"),
]

for idx, (val, label) in enumerate(metrics):
    x = 2.8 + idx * 2.5
    ax.text(x, 2.7, val, ha='center', va='center',
            fontsize=16, fontweight='bold', color=C_ACCENT, family='sans-serif')
    ax.text(x, 2.2, label, ha='center', va='center',
            fontsize=7, color=C_GRAY, family='sans-serif')

# ════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════
ax.text(8, 1.2, "Galarix - AI-Powered Synthetic Data Engine for Privacy-Compliant Enterprise Analytics",
        ha='center', va='center', fontsize=8, color=C_GRAY, family='sans-serif', style='italic')
ax.text(8, 0.8, "Technology Stack: Python | React.js | Google Gemini API | NumPy | TailwindCSS",
        ha='center', va='center', fontsize=7, color='#64748b', family='sans-serif')

plt.tight_layout()
plt.savefig(r"C:\Users\Admin\Desktop\GALARIX_MAIN\GalarixArchitectureBlockDiagram.pdf",
            format='pdf', dpi=200, facecolor=C_BG, bbox_inches='tight')
print("PDF saved to Desktop: GalarixArchitectureBlockDiagram.pdf")
plt.close()
