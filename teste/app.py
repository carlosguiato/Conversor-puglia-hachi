import io
import numpy as np
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
# CONVERSOR HACHIMITSU (Código Original Intacto)
# -------------------------------------------------------------
if opcao_conversor == "Conversor Hachimitsu":
  st.subheader("🍱 Conversor Hachimitsu")
  st.write(
      "Faça o upload da sua planilha de extrato bancário para gerar o arquivo"
      " CSV formatado corretamente."
  )

  uploaded_file = st.file_uploader(
      "Selecione o arquivo Excel do extrato (.xlsx, .xls)",
      type=["xlsx", "xls"],
      key="hachimitsu",
  )

  if uploaded_file is not None:
    try:
      # Leitura inicial do arquivo Excel
      df = pd.read_excel(uploaded_file, header=0, skiprows=[1])

      with st.expander("🔍 Ver colunas identificadas na planilha"):
        st.write(df.columns.tolist())

      # Descobre quais contas bancárias existem na coluna 'Conta bancária'
      contas_encontradas = []
      if "Conta bancária" in df.columns:
        contas_encontradas = df["Conta bancária"].dropna().unique()

      st.markdown("---")
      st.subheader("⚙️ Configuração das Contas no Domínio")

      # Mapeamento dinâmico dos bancos encontrados
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
            "A coluna 'Conta bancária' não foi encontrada. Será usada a conta"
            " padrão '9'."
        )

      # Configuração das contas transitórias
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

      # Botão para processar
      if st.button("🚀 Processar e Gerar CSV", type="primary", key="btn_hach"):
        if not conta_fornecedor or not conta_cliente:
          st.error(
              "Por favor, preencha as contas transitórias de Fornecedor e"
              " Cliente antes de continuar."
          )
        else:
          # 2. Tratamento da coluna VALOR
          if pd.api.types.is_numeric_dtype(df["Valor"]):
            df["VALOR_NUM"] = df["Valor"].fillna(0)
          else:
            df["VALOR_NUM"] = (
                df["Valor"]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df["VALOR_NUM"] = (
                pd.to_numeric(df["VALOR_NUM"], errors="coerce").fillna(0)
            )

          # 3. Lógica Contábil Dinâmica
          def define_debito(row):
            valor = row["VALOR_NUM"]
            if valor < 0:
              return conta_fornecedor
            else:
              banco_linha = row.get("Conta bancária")
              return mapeamento_contas.get(banco_linha, "9")

          def define_credito(row):
            valor = row["VALOR_NUM"]
            if valor < 0:
              banco_linha = row.get("Conta bancária")
              return mapeamento_contas.get(banco_linha, "9")
            else:
              return conta_cliente

          df["Conta Debito"] = df.apply(define_debito, axis=1)
          df["Conta Credito"] = df.apply(define_credito, axis=1)

          # 4. Formatação do Histórico (Limpando nulos e o 'nan')
          def limpar_texto(valor):
            if (
                pd.isna(valor)
                or str(valor).strip().lower() in ["nan", "none", "nat", ""]
            ):
              return ""
            return str(valor).strip()

          df["Historico"] = (
              df["Descrição"].apply(limpar_texto)
              + " - "
              + df["Cliente"].apply(limpar_texto)
              + " - "
              + df["Nr. doc."].apply(limpar_texto)
              + " - "
              + df["Categoria"].apply(limpar_texto)
          )
          df["Historico"] = (
              df["Historico"]
              .str.replace(r"\s*-\s*-\s*", " - ", regex=True)
              .str.strip(" -")
          )

          # 5. Montagem do layout final
          df_final = pd.DataFrame({
              "Data": pd.to_datetime(df["Data"], dayfirst=True).dt.strftime(
                  "%d/%m/%Y"
              ),
              "Conta Debito": df["Conta Debito"],
              "Conta Credito": df["Conta Credito"],
              "Valor": df["VALOR_NUM"].abs(),
              "Historico": df["Historico"],
          })

          # 6. Geração do CSV em memória com delimitador ponto e vírgula (sep=';')
          csv_buffer = io.StringIO()
          df_final.to_csv(
              csv_buffer, sep=";", index=False, decimal=",", encoding="cp1252"
          )
          csv_data = csv_buffer.getvalue()

          st.success("✨ Arquivo convertido com sucesso!")

          # Mostra uma prévia na tela
          with st.expander("👀 Visualizar prévia dos primeiros lançamentos"):
            st.dataframe(df_final.head(15))

          # Botão de Download
          st.download_button(
              label="📥 Baixar Arquivo CSV para o Domínio",
              data=csv_data.encode("cp1252", errors="replace"),
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
        col_tipo = df.columns[1]
        col_desc = df.columns[2]
        col_nota = df.columns[3]
        col_nome = df.columns[4]
        col_cd = df.columns[5]
        col_val = df.columns[7] if len(df.columns) > 7 else df.columns[-1]

        def criar_historico_puglia(row):
          partes = []
          desc = (
              str(row[col_desc]).strip() if pd.notna(row[col_desc]) else ""
          )
          if desc and desc.lower() != "nan":
            partes.append(desc)

          nota = (
              str(row[col_nota]).strip() if pd.notna(row[col_nota]) else ""
          )
          if nota and nota.lower() != "nan":
            partes.append(f"Nota: {nota}")

          nome = (
              str(row[col_nome]).strip() if pd.notna(row[col_nome]) else ""
          )
          if nome and nome.lower() != "nan":
            partes.append(nome)

          type_val = (
              str(row[col_tipo]).strip() if pd.notna(row[col_tipo]) else ""
          )
          if type_val and type_val.lower() != "nan":
            partes.append(type_val)

          return " - ".join(partes)

        df["Historico_Final"] = df.apply(criar_historico_puglia, axis=1)

        contas_debito = []
        contas_credito = []

        for _, row in df.iterrows():
          indicador_cd = str(row[col_cd]).strip().upper()
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

        output = io.BytesIO()
        df_final.to_csv(
            output, sep=";", index=False, decimal=",", encoding="cp1252"
        )
        processed_data = output.getvalue()

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