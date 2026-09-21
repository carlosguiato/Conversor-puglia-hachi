import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Conversores Contábeis", page_icon="📊", layout="centered")

st.title("📊 Sistema de Conversão de Extratos para o Domínio")
st.write("Selecione o conversor desejado na barra lateral, faça o upload do arquivo e configure as contas.")

# Barra lateral para escolha do conversor
st.sidebar.header("Menu de Navegação")
opcao_conversor = st.sidebar.radio(
    "Escolha o Conversor:",
    ("Conversor Hachimitsu", "Conversor Puglia")
)

# -------------------------------------------------------------
# CONVERSOR HACHIMITSU (Com leitura dinâmica e memória dos bancos)
# -------------------------------------------------------------
if opcao_conversor == "Conversor Hachimitsu":
    st.subheader("🍱 Conversor Hachimitsu")
    st.write("Envie o arquivo para identificar os bancos e configurar as contas de cada um.")
    
    arquivo_hachimitsu = st.file_uploader("Envie o arquivo do Hachimitsu (Excel/CSV)", type=["xlsx", "xls", "csv"], key="hachimitsu")
    
    if arquivo_hachimitsu is not None:
        try:
            # Lê o arquivo se mudou ou se ainda não foi lido
            if arquivo_hachimitsu.name.endswith(('xlsx', 'xls')):
                df_hach = pd.read_excel(arquivo_hachimitsu)
            else:
                df_hach = pd.read_csv(arquivo_hachimitsu, sep=None, engine='python')
            
            # Tenta localizar automaticamente a coluna que contém os nomes dos bancos
            colunas_possiveis = [c for c in df_hach.columns if 'banco' in c.lower() or 'conta' in c.lower() or 'instituicao' in c.lower()]
            
            if colunas_possiveis:
                col_banco_hach = colunas_possiveis[0]
                bancos_encontrados = df_hach[col_banco_hach].dropna().unique()
                
                st.success(f"🔍 Coluna de bancos identificada: **{col_banco_hach}**")
                st.write("Informe a conta contábil do Domínio para cada banco listado abaixo:")
                
                # Cria os inputs para cada banco encontrado
                contas_bancos_input = {}
                for banco in bancos_encontrados:
                    contas_bancos_input[banco] = st.text_input(f"Conta Domínio para o Banco: {banco}", key=f"input_banco_{banco}")
                
                st.markdown("---")
            else:
                st.warning("Não foi possível detectar automaticamente a coluna de bancos.")
            
            # Contas Transitórias gerais do Hachimitsu
            st.write("### Contas Transitórias")
            col1, col2 = st.columns(2)
            with col1:
                conta_cli_hach = st.text_input("Transitória CLIENTES", key="cli_hach")
            with col2:
                conta_forn_hach = st.text_input("Transitória FORNECEDORES", key="forn_hach")

            if st.button("Processar Hachimitsu", key="btn_hach"):
                if not conta_cli_hach or not conta_forn_hach:
                    st.warning("Por favor, preencha as contas transitórias de Clientes e Fornecedores.")
                else:
                    # Lógica de substituição e geração do Hachimitsu
                    # Aqui você pode aplicar o mapeamento das contas dos bancos na coluna correspondente do df_hach se necessário
                    
                    output = io.BytesIO()
                    df_hach.to_csv(output, sep=';', index=False, header=False, decimal=',', encoding='cp1252')
                    processed_data = output.getvalue()

                    st.success("✨ Arquivo Hachimitsu processado com sucesso!")
                    st.download_button(
                        label="Baixar CSV para o Domínio (Hachimitsu)",
                        data=processed_data,
                        file_name="extrato_hachimitsu_dominio.csv",
                        mime="text/csv"
                    )
        except Exception as e:
            st.error(f"Erro ao ler o arquivo Hachimitsu: {e}")

# -------------------------------------------------------------
# CONVERSOR PUGLIA (Banco único fixo)
# -------------------------------------------------------------
elif opcao_conversor == "Conversor Puglia":
    st.subheader("🍷 Conversor Puglia")
    st.write("Processamento do relatório com exclusão de colunas B, C e Saldo, filtro 'Cons. == S' e histórico personalizado.")
    
    arquivo_puglia = st.file_uploader("Envie o arquivo do Puglia (Excel)", type=["xlsx", "xls"], key="puglia")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        conta_banco_pug = st.text_input("Conta Banco", key="banco_pug")
    with col2:
        conta_cli_pug = st.text_input("Transitória CLIENTES", key="cli_pug")
    with col3:
        conta_forn_pug = st.text_input("Transitória FORNECEDORES", key="forn_pug")

    if st.button("Processar Puglia", key="btn_pug"):
        if not arquivo_puglia:
            st.warning("Por favor, faça o upload de um arquivo Excel.")
        elif not conta_banco_pug or not conta_cli_pug or not conta_forn_pug:
            st.warning("Por favor, preencha todas as contas contábeis (Banco, Clientes e Fornecedores).")
        else:
            try:
                # 1. Carrega o arquivo Excel
                df = pd.read_excel(arquivo_puglia)
                
                # 2. Pula a primeira linha de dados (ignora o "Saldo anterior")
                df = df.iloc[1:].reset_index(drop=True)
                
                # 3. Apaga as colunas B e C originais (índices 1 e 2)
                colunas_para_remover = [df.columns[1], df.columns[2]]
                df = df.drop(columns=colunas_para_remover)
                
                # 4. Apaga a coluna de Saldo
                colunas_saldo = [col for col in df.columns if 'saldo' in col.lower()]
                if colunas_saldo:
                    df = df.drop(columns=colunas_saldo)
                
                # 5. Filtra a coluna 'Cons.' mantendo apenas os valores 'S' (ignora 'N')
                col_cons = [c for c in df.columns if 'cons' in c.lower() and c.lower() != 'data consol.']
                if col_cons:
                    nome_col_cons = col_cons[0]
                    df = df[df[nome_col_cons].astype(str).str.strip().str.upper() == 'S']

                # Identifica as colunas restantes com base na posição atualizada
                col_data = df.columns[0]
                col_tipo = df.columns[1]
                col_desc = df.columns[2]
                col_nota = df.columns[3]
                col_nome = df.columns[4]
                col_cd   = df.columns[5]
                col_val  = df.columns[7] if len(df.columns) > 7 else df.columns[-1]

                # 6. Monta o Histórico na ordem exata: Descrição, NºNota, Nome e Tipo
                def criar_historico(row):
                    partes = []
                    desc = str(row[col_desc]).strip() if pd.notna(row[col_desc]) else ""
                    if desc and desc.lower() != 'nan': partes.append(desc)
                    
                    nota = str(row[col_nota]).strip() if pd.notna(row[col_nota]) else ""
                    if nota and nota.lower() != 'nan': partes.append(f"Nota: {nota}")
                    
                    nome = str(row[col_nome]).strip() if pd.notna(row[col_nome]) else ""
                    if nome and nome.lower() != 'nan': partes.append(nome)
                    
                    tipo = str(row[col_tipo]).strip() if pd.notna(row[col_tipo]) else ""
                    if tipo and tipo.lower() != 'nan': partes.append(tipo)
                    
                    return " - ".join(partes)

                df['Historico_Final'] = df.apply(criar_historico, axis=1)

                # 7. Define as contas de Débito e Crédito baseadas na coluna CD
                contas_debito = []
                contas_credito = []

                for _, row in df.iterrows():
                    indicador_cd = str(row[col_cd]).strip().upper()
                    if indicador_cd == 'D':
                        contas_debito.append(conta_forn_pug)
                        contas_credito.append(conta_banco_pug)
                    else:
                        contas_debito.append(conta_banco_pug)
                        contas_credito.append(conta_cli_pug)

                df['Conta Debito'] = contas_debito
                df['Conta Credito'] = contas_credito

                # 8. Formata o DataFrame final no layout exato
                df_final = pd.DataFrame({
                    'Data': pd.to_datetime(df[col_data], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y'),
                    'Conta Debito': df['Conta Debito'],
                    'Conta Credito': df['Conta Credito'],
                    'Valor': pd.to_numeric(df[col_val], errors='coerce').abs(),
                    'Historico': df['Historico_Final']
                }).dropna(subset=['Data'])

                # Converte para CSV em memória (sem cabeçalho)
                output = io.BytesIO()
                df_final.to_csv(output, sep=';', index=False, header=False, decimal=',', encoding='cp1252')
                processed_data = output.getvalue()

                st.success(f"✨ Processo concluído! {len(df_final)} lançamentos gerados com sucesso.")
                
                st.download_button(
                    label="Baixar CSV para o Domínio (Puglia)",
                    data=processed_data,
                    file_name="extrato_puglia_dominio.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar o arquivo Puglia: {e}")
