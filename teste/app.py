import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Conversor Puglia - Hachi", page_icon="🚀", layout="centered"
)

st.title("🚀 Conversor e Processador - Puglia & Hachi")
st.write(
    "Faça o upload do seu arquivo para processar os dados e gerar o CSV limpo."
)

uploaded_file = st.file_uploader(
    "Escolha o arquivo (Excel ou CSV)", type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:
  try:
    # Leitura do arquivo dependendo da extensão
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)

    st.success("Arquivo carregado com sucesso!")
    st.write("Visualização prévia dos dados:")
    st.dataframe(df.head())

    if st.button("🚀 Processar e Gerar CSV"):
      # 4. Formatação do Histórico (Procura a coluna de descrição sem travar se mudar o nome)
      def limpar_texto(valor):
        if (
            pd.isna(valor)
            or str(valor).strip().lower() in ["nan", "none", "nat", ""]
        ):
          return ""
        return str(valor).strip()

      # Busca flexível para as colunas para evitar KeyError
      col_desc_encontrada = next(
          (
              c
              for c in df.columns
              if "desc" in c.lower() or "historico" in c.lower()
          ),
          None,
      )
      col_cli_encontrada = next(
          (c for c in df.columns if "cli" in c.lower() or "nome" in c.lower()),
          None,
      )
      col_doc_encontrada = next(
          (c for c in df.columns if "doc" in c.lower() or "num" in c.lower()),
          None,
      )
      col_cat_encontrada = next(
          (c for c in df.columns if "cat" in c.lower()), None
      )

      partes_historico = []
      if col_desc_encontrada:
        partes_historico.append(df[col_desc_encontrada].apply(limpar_texto))
      if col_cli_encontrada:
        partes_historico.append(df[col_cli_encontrada].apply(limpar_texto))
      if col_doc_encontrada:
        partes_historico.append(df[col_doc_encontrada].apply(limpar_texto))
      if col_cat_encontrada:
        partes_historico.append(df[col_cat_encontrada].apply(limpar_texto))

      if partes_historico:
        df["Historico"] = partes_historico[0]
        for p in partes_historico[1:]:
          df["Historico"] = df["Historico"] + " - " + p
      else:
        df["Historico"] = ""

      df["Historico"] = (
          df["Historico"]
          .str.replace(r"\s*-\s*-\s*", " - ", regex=True)
          .str.strip(" -")
      )

      st.success("Processamento concluído com sucesso!")
      st.dataframe(df.head())

      # Botão para baixar o CSV processado
      csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
      st.download_button(
          label="📥 Baixar CSV Processado",
          data=csv_data,
          file_name="arquivo_processado.csv",
          mime="text/csv",
      )

  except Exception as e:
    st.error(f"Ocorreu um erro ao processar o arquivo: {e}")