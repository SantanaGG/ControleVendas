import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import warnings
import os
import shutil

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão Pro", layout="wide", page_icon="🛡️")
warnings.simplefilter(action='ignore', category=FutureWarning)

# Importação segura
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
except ImportError:
    st.error("⚠️ Erro crítico: Biblioteca visual não instalada.")
    st.stop()

# --- SISTEMA DE BACKUP OTIMIZADO (TOP 3) ---
def realizar_backup():
    db_file = 'meu_negocio_v8.db'
    if os.path.exists(db_file):
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        # Cria o backup atual
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"backups/backup_{timestamp}.db"
        
        try:
            shutil.copy2(db_file, backup_name)
            
            # --- LIMPEZA AGRESSIVA: MANTÉM SÓ 3 ---
            # Lista todos os arquivos na pasta backups com o caminho completo
            arquivos = [os.path.join('backups', f) for f in os.listdir('backups')]
            # Filtra apenas arquivos (ignora pastas se tiver)
            arquivos = [f for f in arquivos if os.path.isfile(f)]
            # Ordena do mais antigo para o mais novo
            arquivos.sort(key=os.path.getmtime)
            
            # Enquanto tiver mais que 3, apaga o mais velho (o primeiro da lista)
            while len(arquivos) > 3:
                arquivo_velho = arquivos.pop(0)
                os.remove(arquivo_velho)
                
        except Exception:
            pass # Silencioso para não atrapalhar

realizar_backup()

# --- CSS ---
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Banco de dados
engine = create_engine('sqlite:///meu_negocio_v8.db')

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_venda TEXT,
                plataforma TEXT,
                categoria TEXT,
                qtd_itens INTEGER,
                valor_total_venda REAL,
                custo_total_produtos REAL,
                taxa_plataforma_total REAL,
                lucro_bruto REAL,
                data_recebimento TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_despesa TEXT,
                categoria_despesa TEXT,
                descricao TEXT,
                valor_despesa REAL
            )
        """))
        conn.commit()

init_db()

# --- FUNÇÃO AUXILIAR DE SEGURANÇA ---
def extrair_ids_seguro(selecionados):
    ids_validos = []
    if isinstance(selecionados, pd.DataFrame):
        lista_dados = selecionados.to_dict('records')
    elif isinstance(selecionados, list):
        lista_dados = selecionados
    else:
        lista_dados = []

    for item in lista_dados:
        if isinstance(item, dict):
            valor_id = item.get('id')
            if valor_id is not None:
                try:
                    ids_validos.append(int(valor_id))
                except ValueError:
                    pass
    return ids_validos

# --- FUNÇÃO VISUAL ---
def criar_tabela_clean(df, key_id):
    df_show = df.copy()
    for col in df_show.columns:
        if "data" in col:
            df_show[col] = df_show[col].astype(str)

    gb = GridOptionsBuilder.from_dataframe(df_show)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=6)
    gb.configure_default_column(editable=True, groupable=True)
    gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren=True)
    
    if 'valor_total_venda' in df_show.columns:
        gb.configure_column("valor_total_venda", header_name="Total", type=["numericColumn"], precision=2)
        gb.configure_column("lucro_bruto", header_name="Lucro", type=["numericColumn"], precision=2)
    
    gridOptions = gb.build()
    
    return AgGrid(
        df_show,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.AS_INPUT, 
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        theme='balham',
        height=350,
        width='100%',
        key=key_id
    )

# --- APP ---
st.title("🛡️ Gestão Financeira Segura")

# --- LANÇAMENTOS ---
with st.expander("➕ Novo Lançamento", expanded=True):
    aba_venda, aba_despesa = st.tabs(["💰 Venda", "💸 Despesa"])

    with aba_venda:
        with st.form("form_venda", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            data_venda = c1.date_input("Data", datetime.now())
            plataforma = c2.selectbox("Canal", ["Shopee", "Mercado Livre", "Venda Direta", "WhatsApp"])
            categoria = c3.selectbox("Categoria", ["Tênis Infantil", "Tênis Bebê", "Tênis Adulto", "Outros"])
            
            c4, c5, c6, c7 = st.columns(4)
            qtd = c4.number_input("Qtd", value=1, min_value=1)
            valor_venda = c5.number_input("Total Venda (R$)", value=0.0, step=1.0)
            custo_produtos = c6.number_input("Custo Prods (R$)", value=0.0, step=1.0)
            taxa_plat = c7.number_input("Taxas (R$)", value=0.0, step=1.0)
            
            if st.form_submit_button("Salvar Venda", use_container_width=True):
                lucro_bruto = valor_venda - custo_produtos - taxa_plat
                dias = 7 if "Shopee" in plataforma else 0
                data_rec = data_venda + timedelta(days=dias)
                
                with engine.connect() as conn:
                    conn.execute(text(f"""
                        INSERT INTO vendas (data_venda, plataforma, categoria, qtd_itens,
                        valor_total_venda, custo_total_produtos, taxa_plataforma_total,
                        lucro_bruto, data_recebimento) VALUES 
                        ('{data_venda}', '{plataforma}', '{categoria}', {qtd},
                        {valor_venda}, {custo_produtos}, {taxa_plat},
                        {lucro_bruto}, '{data_rec}')
                    """))
                    conn.commit()
                st.success("Venda Salva!")
                st.rerun()

    with aba_despesa:
        with st.form("form_despesa", clear_on_submit=True):
            c1, c2, c3 = st.columns([1, 1, 2])
            data_desp = c1.date_input("Data Gasto", datetime.now())
            tipo = c2.selectbox("Tipo", ["Logística", "Ads", "Embalagem", "Outros"])
            desc = c3.text_input("Descrição")
            valor = st.number_input("Valor (R$)", value=0.0, step=1.0)
            
            if st.form_submit_button("Salvar Despesa", use_container_width=True):
                with engine.connect() as conn:
                    conn.execute(text(f"""
                        INSERT INTO despesas (data_despesa, categoria_despesa, descricao, valor_despesa)
                        VALUES ('{data_desp}', '{tipo}', '{desc}', {valor})
                    """))
                    conn.commit()
                st.success("Despesa Salva!")
                st.rerun()

# --- DADOS ---
df_vendas = pd.read_sql("SELECT * FROM vendas", engine)
df_despesas = pd.read_sql("SELECT * FROM despesas", engine)

if not df_vendas.empty:
    df_vendas['data_venda'] = pd.to_datetime(df_vendas['data_venda'], errors='coerce').dt.date
    df_vendas = df_vendas.dropna(subset=['data_venda'])
    df_vendas_view = df_vendas[['id', 'data_venda', 'plataforma', 'categoria', 'qtd_itens', 'valor_total_venda', 'lucro_bruto']]
else:
    df_vendas_view = pd.DataFrame()

if not df_despesas.empty:
    df_despesas['data_despesa'] = pd.to_datetime(df_despesas['data_despesa'], errors='coerce').dt.date
    df_despesas = df_despesas.dropna(subset=['data_despesa'])
    df_despesas_view = df_despesas[['id', 'data_despesa', 'categoria_despesa', 'descricao', 'valor_despesa']]
else:
    df_despesas_view = pd.DataFrame()

# KPIs
total_vendas = df_vendas['valor_total_venda'].sum() if not df_vendas.empty else 0
total_custo = df_vendas['custo_total_produtos'].sum() if not df_vendas.empty else 0
total_taxas = df_vendas['taxa_plataforma_total'].sum() if not df_vendas.empty else 0
total_desp = df_despesas['valor_despesa'].sum() if not df_despesas.empty else 0
lucro_liq = total_vendas - total_custo - total_taxas - total_desp

st.markdown("### 📊 Visão Geral")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Lucro Líquido", f"R$ {lucro_liq:.2f}")
m2.metric("Entradas", f"R$ {total_vendas:.2f}")
m3.metric("Saídas", f"R$ {total_desp:.2f}")
m4.metric("Taxas", f"R$ {total_taxas:.2f}")

st.markdown("---")

# --- TABELAS ---
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("🛒 Vendas")
    if not df_vendas_view.empty:
        resp_venda = criar_tabela_clean(df_vendas_view, "grid_vendas")
        if st.button("🗑️ Deletar Vendas"):
            ids_venda = extrair_ids_seguro(resp_venda['selected_rows'])
            if ids_venda:
                ids_str = ', '.join(map(str, ids_venda))
                with engine.connect() as conn:
                    conn.execute(text(f"DELETE FROM vendas WHERE id IN ({ids_str})"))
                    conn.commit()
                st.success(f"{len(ids_venda)} deletados!")
                st.rerun()
            else:
                st.warning("Selecione itens.")
    else:
        st.info("Sem dados.")

with col2:
    st.subheader("📉 Despesas")
    if not df_despesas_view.empty:
        resp_desp = criar_tabela_clean(df_despesas_view, "grid_despesas")
        if st.button("🗑️ Deletar Despesas"):
            ids_desp = extrair_ids_seguro(resp_desp['selected_rows'])
            if ids_desp:
                ids_str = ', '.join(map(str, ids_desp))
                with engine.connect() as conn:
                    conn.execute(text(f"DELETE FROM despesas WHERE id IN ({ids_str})"))
                    conn.commit()
                st.success(f"{len(ids_desp)} deletados!")
                st.rerun()
            else:
                st.warning("Selecione itens.")
    else:
        st.info("Sem dados.")