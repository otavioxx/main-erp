# referencia_temas.py
"""
Referência rápida para trabalhar com temas no MainERP
"""

# ============================================================================
# APLICAR TEMAS
# ============================================================================

from styles import (
    aplicar_tema_dark_clean,
    aplicar_tema_dark_blue, 
    aplicar_tema_high_contrast,
    aplicar_tema_light_clean
)

# Usar tema claro (ATIVO AGORA)
# aplicar_tema_light_clean(app)

# Usar tema escuro padrão
# aplicar_tema_dark_clean(app)

# Usar tema azul escuro
# aplicar_tema_dark_blue(app)

# Usar alto contraste
# aplicar_tema_high_contrast(app)


# ============================================================================
# PALETA DE CORES CLARO
# ============================================================================

CORES_TEMA_CLARO = {
    "background_primary": "#f5f5f5",      # Fundo principal (cinza claro)
    "background_secondary": "#ffffff",    # Fundo secundário (branco)
    "background_tertiary": "#f9f9f9",     # Fundo terciário
    
    "text_primary": "#1a1a1a",            # Texto principal (preto)
    "text_secondary": "#333333",          # Texto secundário
    "text_muted": "#666666",              # Texto desativado
    "text_disabled": "#999999",           # Texto desabilitado
    
    "accent_primary": "#1A4968",          # Acento azul escuro
    "accent_hover": "#0c5991",            # Acento ao passar
    "accent_pressed": "#024f83",          # Acento pressionado
    
    "border_primary": "#d0d0d0",          # Bordas primárias
    "border_secondary": "#e0e0e0",        # Bordas secundárias
    "border_focus": "#1A4968",            # Borda com foco
    
    "success": "#4caf50",                 # Verde sucesso
    "success_border": "#45a049",          # Borda verde
    "warning": "#ff9800",                 # Laranja aviso
    "warning_border": "#fb8c00",          # Borda laranja
    "danger": "#f44336",                  # Vermelho erro
    "danger_border": "#da190b",           # Borda vermelha
    
    "selection_bg": "#1A4968",            # Fundo seleção
    "selection_text": "#ffffff",          # Texto seleção
    "hover_bg": "#eeeeee",                # Fundo hover
}


# ============================================================================
# PALETA DE CORES ESCURO
# ============================================================================

CORES_TEMA_ESCURO = {
    "background_primary": "#1a1a1a",      # Fundo principal (preto)
    "background_secondary": "#202020",    # Fundo secundário
    "background_tertiary": "#252525",     # Fundo terciário
    
    "text_primary": "#e0e0e0",            # Texto principal (branco)
    "text_secondary": "#b8b8b8",          # Texto secundário
    "text_muted": "#888888",              # Texto desativado
    "text_disabled": "#555555",           # Texto desabilitado
    
    "accent_primary": "#1A4968",          # Acento azul
    "accent_hover": "#0c5991",            # Acento ao passar
    "accent_pressed": "#024f83",          # Acento pressionado
    
    "border_primary": "#333333",          # Bordas primárias
    "border_secondary": "#404040",        # Bordas secundárias
    "border_focus": "#025a94",            # Borda com foco
    
    "success": "#2d5a2d",                 # Verde escuro
    "success_border": "#3d6b3d",          # Borda verde
    "warning": "#5a4d2d",                 # Laranja escuro
    "warning_border": "#6b5d3d",          # Borda laranja
    "danger": "#5a2d2d",                  # Vermelho escuro
    "danger_border": "#6b3d3d",           # Borda vermelha
    
    "selection_bg": "#025a94",            # Fundo seleção
    "selection_text": "#ffffff",          # Texto seleção
    "hover_bg": "#2a2a2a",                # Fundo hover
}


# ============================================================================
# TROCAR TEMA EM TEMPO DE EXECUÇÃO
# ============================================================================

def trocar_tema_dinamico(app, novo_tema):
    """
    Troca o tema da aplicação em tempo de execução
    
    Args:
        app: Instância da aplicação PyQt6
        novo_tema: String com nome do tema
                   ("light_clean", "dark_clean", "dark_blue", "high_contrast")
    """
    temas_disponiveis = {
        "light_clean": aplicar_tema_light_clean,
        "dark_clean": aplicar_tema_dark_clean,
        "dark_blue": aplicar_tema_dark_blue,
        "high_contrast": aplicar_tema_high_contrast,
    }
    
    if novo_tema in temas_disponiveis:
        temas_disponiveis[novo_tema](app)
        print(f"✅ Tema alterado para: {novo_tema}")
    else:
        print(f"❌ Tema '{novo_tema}' não encontrado!")
        print(f"   Temas disponíveis: {', '.join(temas_disponiveis.keys())}")


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    """
    Exemplos de como usar os temas
    """
    
    # Exemplo 1: Inicializar com tema claro
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    aplicar_tema_light_clean(app)
    # ... resto do código
    
    
    # Exemplo 2: Trocar tema dinamicamente
    # trocar_tema_dinamico(app, "dark_clean")
    
    
    # Exemplo 3: Acessar cores do tema
    print("Cores do tema claro:")
    for cor, valor in CORES_TEMA_CLARO.items():
        print(f"  {cor}: {valor}")