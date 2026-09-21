import io
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Conversor de Extrato - Domínio",
    page_icon="📊",
    layout="centered",
)

st.title("📊 Sistema de Conversão de Extratos para o Domínio Web")
st.write(
    "Selecione o conversor desejado na barra lateral e faça o upload do arquivo."
)

# Barra lateral para escolha do conversor
st.sidebar.header("Menu de Navegação")
opcao_conversor = st.sidebar.radio(
    "Escolha o Conversor:", ("Conversor Hachimitsu", "Conversor Puglia")
)

# -------------------------------------------------------------
# CONVERSOR HACHIMITSU (Corrigido e Definitivo)
# -------------------------------------------------------------
if opcao_conversor == "Conversor Hachimitsu":
  st.subheader("🍱 Conversor Hachimitsu")
  st.write(
      "Faça o upload do arquivo Excel do Hachimitsu para gerar o CSV de"
      " importação correto."
  )

  uploaded_file = st.file_uploader(
      "Selecione o arquivo Excel (.xlsx, .xls)",
      type=["xlsx", "xls"],
      key="hachimitsu",
  )

  if uploaded_file is not None:
    try:
      # Leitura do Excel ignorando linhas vazias iniciais
      df = pd.read_excel(uploaded_file)
      df = df.dropna(how="all").reset_index(drop=True)

      with st.expander("🔍 Ver colunas identificadas na planilha"):
        st.write(df.columns.tolist())

      # Descobre contas bancárias na coluna correspondente
      contas_encontradas = []
      col_banco_origem = next(
          (c for c in df.columns if "conta" in c.lower() and "banco" in c.lower()),
          None,
      )
      if not col_banco_origem and "Conta bancária" in df.columns:
        col_banco_origem = "Conta bancária"

      if col_banco_origem:
        contas_encontradas = df[col_banco_origem].dropna().unique()

      st.markdown("---")
      st.subheader("⚙️ Configuração das Contas no Domínio")

      mapeamento_contas = {}
      if len(contas_encontradas) > 0:
        for conta in contas_encontradas:
          mapeamento_contas[conta] = st.text_input(
              f"Código da conta do banco **'{conta}'** no Domínio:",
              value="",
              key=f"hach_{conta}",
          )
      else:
        st.warning(
            "Coluna de conta bancária não identificada automaticamente."
            " Utilizará a padrão '9'."
        )

      col1, col2 = st.columns(2)
      with col1:
        conta_fornecedor = st.text_input(
            "Contra conta para **SAÍDAS** (Fornecedor / < 0):",
            value="",
            key="hach_forn",
        )
      with col2:
        conta_cliente = st.text_input(
            "Contra conta para **ENTRADAS** (Clientes / > 0):",
            value="",
            key="hach_cli",
        )

      st.markdown("---")

      if st.button(
          "🚀 Processar e Gerar CSV do Hachimitsu",
          type="primary",
          key="btn_hach",
      ):
        if not conta_fornecedor or not conta_cliente:
          st.error(
              "Por favor, preencha as contas transitórias de Fornecedor e"
              " Cliente."
          )
        else:
          # Localiza a coluna de valor
          col_valor = next(
              (c for c in df.columns if "valor" in c.lower()), "Valor"
          )

          # Tratamento do Valor
          if pd.api.types.is_numeric_dtype(df[col_valor]):
            df["VALOR_NUM"] = df[col_valor].fillna(0)
          else:
            df["VALOR_NUM"] = (
                df[col_valor]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df["VALOR_NUM"] = pd.to_numeric(
                df["VALOR_NUM"], errors="coerce"
            ).fillna(0)

          # Lógica Contábil
          def define_debito(row):
            valor = row["VALOR_NUM"]
            if valor < 0:
              return conta_fornecedor
            else:
              banco_linha = (
                  row.get(col_banco_origem) if col_banco_origem else None
              )
              return mapeamento_contas.get(banco_linha, "9")

          def define_credito(row):
            valor = row["VALOR_NUM"]
            if valor < 0:
              banco_linha = (
                  row.get(col_banco_origem) if col_banco_origem else None
              )
              return mapeamento_contas.get(banco_linha, "9")
            else:
              return conta_cliente

          df["Conta Debito"] = df.apply(define_debito, axis=1)
          df["Conta Credito"] = df.apply(define_credito, axis=1)

          # Formatação Segura do Histórico (Garante que só pega colunas de texto/descrição)
          def limpar_texto(valor):
            if (
                pd.isna(valor)
                or str(valor).strip().lower() in ["nan", "none", "nat", ""]
            ):
              return ""
            return str(valor).strip()

          col_desc = next(
              (
                  c
                  for c in df.columns
                  if "desc" in c.lower() or "historico" in c.lower()
              ),
              None,
          )
          col_cli = next(
              (
                  c
                  for c in df.columns
                  if "cli" in c.lower()
                  or "favorecido" in c.lower()
                  or "nome" in c.lower()
              ),
              None,
          )
          col_doc = next(
              (
                  c
                  for c in df.columns
                  if "doc" in c.lower() or "num" in c.lower()
              ),
              None,
          )

          partes_historico = []
          if col_desc:
            partes_historico.append(df[col_desc].apply(limpar_texto))
          if col_cli:
            partes_historico.append(df[col_cli].apply(limpar_texto))
          if col_doc:
            partes_historico.append(df[col_doc].apply(limpar_texto))

          if partes_historico:
            df["Historico"] = partes_historico[0]
            for p in partes_historico[1:]:
              df["Historico"] = df["Historico"] + " - " + p
          else:
            df["Historico"] = "Lancamento Hachimitsu"

          # Limpeza final do texto do histórico
          df["Historico"] = (
              df["Historico"]
              .str.replace(r"\s*-\s*-\s*", " - ", regex=True)
              .str.strip(" -")
          )

          # Localiza a coluna de data
          col_data = next(
              (c for c in df.columns if "data" in c.lower()), df.columns[0]
          )

          # Montagem do DataFrame final para o Domínio
          df_final = pd.DataFrame({
              "Data": pd.to_datetime(
                  df[col_data], dayfirst=True, errors="coerce"
              ).dt.strftime("%d/%m/%Y"),
              "Conta Debito": df["Conta Debito"],
              "Conta Credito": df["Conta Credito"],
              "Valor": df["VALOR_NUM"].abs(),
              "Historico": df["Historico"],
          }).dropna(subset=["Data"])

          # Geração do CSV SEM O CABEÇALHO (header=False) e com separador correto para o Domínio
          csv_buffer = io.StringIO()
          df_final.to_csv(
              csv_buffer,
              sep=";",
              index=False,
              header=False,
              decimal=",",
              encoding="cp1252",
          )
          csv_data = csv_buffer.getvalue().encode("cp1252", errors="replace")

          st.success(
              f"✨ Processo concluído! {len(df_final)} lançamentos gerados com"
              " sucesso."
          )

          with st.expander("👀 Visualizar prévia dos dados gerados"):
            st.dataframe(df_final.head(10))

          st.download_button(
              label="📥 Baixar Arquivo CSV para o Domínio",
              data=csv_data,
              file_name="extrato_hachimitsu_dominio.csv",
              mime="text/csv",
          )

    except Exception as e:
      st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# -------------------------------------------------------------
# CONVERSOR PUGLIA
# -------------------------------------------------------------
elif opcao_conversor == "Conversor Puglia":
  st.subheader("🍷 Conversor Puglia")
  st.write(
      "Processamento do relatório Puglia com exclusão de colunas B, C e Saldo,"
      " filtro 'Cons. == S' e histórico personalizado."
  )

  arquivo_puglia = st.file_uploader(
      "Envie o arquivo do Puglia (Excel)", type=["xlsx", "xls"], key="puglia"
  )

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
      st.warning(
          "Por favor, preencha todas as contas contábeis (Banco, Clientes e"
          " Fornecedores)."
      )
    else:
      try:
        df = pd.read_excel(arquivo_puglia)
        df = df.iloc[1:].reset_index(drop=True)

        colunas_para_remover = [df.columns[1], df.columns[2]]
        df = df.drop(columns=colunas_para_remover)

        colunas_saldo = [col for col in df.columns if "saldo" in col.lower()]
        if colunas_saldo:
          df = df.drop(columns=colunas_saldo)

        col_cons = [
            c
            for c in df.columns
            if "cons" in c.lower() and c.lower() != "data consol."
        ]
        if col_cons:
          nome_col_cons = col_cons[0]
          df = df[
              df[nome_col_cons].astype(str).str.strip().str.upper() == "S"
          ]

        col_data = df.columns[0]
        col_tipo = df.columns[1] if len(df.columns) > 1 else None
        col_desc = df.columns[2] if len(df.columns) > 2 else None
        col_nota = df.columns[3] if len(df.columns) > 3 else None
        col_nome = df.columns[4] if len(df.columns) > 4 else None
        col_cd = df.columns[5] if len(df.columns) > 5 else None
        col_val = (
            df.columns[7]
            if len(df.columns) > 7
            else (df.columns[6] if len(df.columns) > 6 else df.columns[-1])
        )

        def criar_historico_puglia(row):
          partes = []
          if col_desc and pd.notna(row[col_desc]):
            d = str(row[col_desc]).strip()
            if d and d.lower() != "nan":
              partes.append(d)

          if col_nota and pd.notna(row[col_nota]):
            n = str(row[col_nota]).strip()
            if n and n.lower() != "nan":
              partes.append(f"Nota: {n}")

          if col_nome and pd.notna(row[col_nome]):
            nm = str(row[col_nome]).strip()
            if nm and nm.lower() != "nan":
              partes.append(nm)

          if col_tipo and pd.notna(row[col_tipo]):
            t = str(row[col_tipo]).strip()
            if t and t.lower() != "nan":
              partes.append(t)

          return " - ".join(partes) if partes else "Lancamento Puglia"

        df["Historico_Final"] = df.apply(criar_historico_puglia, axis=1)

        contas_debito = []
        contas_credito = []

        for _, row in df.iterrows():
          indicador_cd = (
              str(row[col_cd]).strip().upper() if col_cd else "C"
          )
          if indicador_cd == "D":
            contas_debito.append(conta_forn_pug)
            contas_credito.append(conta_banco_pug)
          else:
            contas_debito.append(conta_banco_pug)
            contas_credito.append(conta_cli_pug)

        df["Conta Debito"] = contas_debito
        df["Conta Credito"] = contas_credito

        df_final = pd.DataFrame({
            "Data": pd.to_datetime(
                df[col_data], dayfirst=True, errors="coerce"
            ).dt.strftime("%d/%m/%Y"),
            "Conta Debito": df["Conta Debito"],
            "Conta Credito": df["Conta Credito"],
            "Valor": pd.to_numeric(df[col_val], errors="coerce").abs(),
            "Historico": df["Historico_Final"],
        }).dropna(subset=["Data"])

        output = io.StringIO()
        df_final.to_csv(
            output,
            sep=";",
            index=False,
            header=False,
            decimal=",",
            encoding="cp1252",
        )
        processed_data = output.getvalue().encode("cp1252", errors="replace")

        st.success(
            f"✨ Processo concluído! {len(df_final)} lançamentos gerados com"
            " sucesso."
        )

        st.download_button(
            label="Baixar CSV para o Domínio (Puglia)",
            data=processed_data,
            file_name="extrato_puglia_dominio.csv",
            mime="text/csv",
        )
      except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo Puglia: {e}")