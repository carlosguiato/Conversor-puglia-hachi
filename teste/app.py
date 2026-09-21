# 4. Formatação do Histórico (Procura a coluna de descrição sem travar se mudar o nome)
          def limpar_texto(valor):
            if (
                pd.isna(valor)
                or str(valor).strip().lower() in ["nan", "none", "nat", ""]
            ):
              return ""
            return str(valor).strip()

          # Busca flexível para a coluna de descrição
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
              (
                  c
                  for c in df.columns
                  if "doc" in c.lower() or "num" in c.lower()
              ),
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