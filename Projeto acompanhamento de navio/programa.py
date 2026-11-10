import datetime
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Rastreamento de Containers por Booking", layout="wide"
)

st.title("🚢 Monitoramento de Containers e ETAs")
st.markdown(
    "Acompanhe as datas de saída, compare o **ETA Inicial** com o **ETA Atual**"
    " e acesse o tracking direto do armador."
)

# Inicializando o armazenamento dos bookings monitorados na sessão
if "bookings" not in st.session_state:
  st.session_state.bookings = pd.DataFrame(
      columns=[
          "Booking",
          "Armador",
          "Navio",
          "Origem",
          "Destino",
          "Data Saída",
          "ETA Inicial",
          "ETA Atual",
          "Link Tracking",
      ]
  )

# Base de dados interna (Memória para lembrar dos bookings já cadastrados)
if "db_bookings" not in st.session_state:
  st.session_state.db_bookings = {
      "BKG123456": {
          "armador": "MSC",
          "navio": "MSC FABIOLA",
          "origem": "Algeciras",
          "destino": "Manaus",
          "saida": datetime.date(2026, 10, 10),
          "eta_inicial": datetime.date(2026, 11, 5),
          "eta_atual": datetime.date(2026, 11, 8),
      }
  }


# Função para gerar o link oficial de rastreio por armador
def gerar_link_rastreio(armador, booking):
  booking = booking.strip().upper()
  if not booking:
    return "#"
  if armador == "MSC":
    return f"https://www.msc.com/en/track-a-shipment?agencyPath=%2Fen%2F&number={booking}"
  elif armador == "Maersk":
    return f"https://www.maersk.com/tracking/{booking}"
  elif armador == "CMA CGM":
    return f"https://www.cma-cgm.com/ebusiness/tracking/search?SearchBy=Booking&Reference={booking}"
  elif armador == "Hapag-Lloyd":
    return f"https://www.hapag-lloyd.com/en/online-business/tracing/tracing-by-booking.html?bkg={booking}"
  elif armador == "ONE":
    return f"https://ecomm.one-line.com/ecom/CUP_HOM_3301.do?bkgNo={booking}"
  else:
    return "#"


# ==============================================================================
# BARRA LATERAL (Sidebar) - Consulta Inteligente e Cadastro
# ==============================================================================
st.sidebar.header("🔍 Consultar e Cadastrar Booking")

booking_input = (
    st.sidebar.text_input("Número do Booking", placeholder="Ex: EBKG1889963")
    .strip()
    .upper()
)

armadores_lista = ["MSC", "Maersk", "CMA CGM", "Hapag-Lloyd", "ONE", "Outro"]
armador_pesquisa = st.sidebar.selectbox(
    "Armador para o Link Rápido", armadores_lista, key="arm_pesq"
)

# Gera o link oficial na hora para consulta rápida
link_oficial_gerado = gerar_link_rastreio(armador_pesquisa, booking_input)

dados_encontrados = {}
if booking_input:
  if booking_input in st.session_state.db_bookings:
    dados_encontrados = st.session_state.db_bookings[booking_input]
    st.sidebar.success(
        "✅ Booking já cadastrado na base! Dados carregados abaixo."
    )
  else:
    st.sidebar.warning("⚠️ Booking novo na base interna.")
    if booking_input:
      st.sidebar.markdown(
          f"🔗 **[Abrir Tracking Oficial da"
          f" {armador_pesquisa}]({link_oficial_gerado})**"
      )
      st.sidebar.caption(
          "Clique acima para conferir os dados no site do armador e preencha"
          " abaixo."
      )

st.sidebar.markdown("---")
st.sidebar.header("➕ Salvar no Monitor")

with st.sidebar.form("add_booking_form"):
  booking_ref = st.text_input(
      "Referência do Booking",
      value=booking_input,
      placeholder="Ex: EBKG1889963",
  )

  armador_padrao = dados_encontrados.get("armador", armador_pesquisa)
  idx_armador = (
      armadores_lista.index(armador_padrao)
      if armador_padrao in armadores_lista
      else 0
  )
  armador_select = st.selectbox(
      "Armador responsável", armadores_lista, index=idx_armador
  )

  vessel = st.text_input(
      "Nome do Navio",
      value=dados_encontrados.get("navio", ""),
      placeholder="Ex: MSC FABIOLA",
  )
  origin = st.text_input(
      "Porto de Origem",
      value=dados_encontrados.get("origem", ""),
      placeholder="Ex: Manaus, BR",
  )
  dest = st.text_input(
      "Porto de Destino",
      value=dados_encontrados.get("destino", ""),
      placeholder="Ex: Cartagena, CO",
  )

  departure_date = st.date_input(
      "Data de Saída",
      value=dados_encontrados.get("saida", datetime.date.today()),
  )
  initial_eta = st.date_input(
      "ETA Inicial (Previsão Original)",
      value=dados_encontrados.get("eta_inicial", datetime.date.today()),
  )
  current_eta = st.date_input(
      "ETA Atual (Previsão Atualizada)",
      value=dados_encontrados.get("eta_atual", datetime.date.today()),
  )

  submit_button = st.form_submit_button(label="Adicionar ao Monitor")

  if submit_button:
    if booking_ref:
      link_final = gerar_link_rastreio(armador_select, booking_ref)

      # Salva na memória interna
      st.session_state.db_bookings[booking_ref] = {
          "armador": armador_select,
          "navio": vessel,
          "origem": origin,
          "destino": dest,
          "saida": departure_date,
          "eta_inicial": initial_eta,
          "eta_atual": current_eta,
      }

      new_row = {
          "Booking": booking_ref,
          "Armador": armador_select,
          "Navio": vessel,
          "Origem": origin,
          "Destino": dest,
          "Data Saída": departure_date,
          "ETA Inicial": initial_eta,
          "ETA Atual": current_eta,
          "Link Tracking": link_final,
      }

      # Verifica se já está no painel principal
      if (
          not st.session_state.bookings.empty
          and booking_ref in st.session_state.bookings["Booking"].values
      ):
        st.sidebar.warning("Este booking já está ativo no painel principal.")
      else:
        st.session_state.bookings = pd.concat(
            [st.session_state.bookings, pd.DataFrame([new_row])],
            ignore_index=True,
        )
        st.sidebar.success(f"Booking {booking_ref} salvo com sucesso!")
        st.rerun()
    else:
      st.sidebar.error("Informe a referência do booking.")


# ==============================================================================
# PAINEL PRINCIPAL (Tabela, Métricas e Links)
# ==============================================================================
if not st.session_state.bookings.empty:
  df = st.session_state.bookings.copy()

  df["ETA Inicial"] = pd.to_datetime(df["ETA Inicial"])
  df["ETA Atual"] = pd.to_datetime(df["ETA Atual"])
  df["Diferença (Dias)"] = (df["ETA Atual"] - df["ETA Inicial"]).dt.days


  def get_status(diff):
    if diff > 0:
      return f"⚠️ Atrasado (+{diff}d)"
    elif diff < 0:
      return f"⚡ Adiantado ({diff}d)"
    else:
      return "✅ No Prazo"


  df["Status ETA"] = df["Diferença (Dias)"].apply(get_status)

  col1, col2, col3 = st.columns(3)
  col1.metric("Total de Bookings Monitorados", len(df))
  col2.metric("Com Atraso no ETA", len(df[df["Diferença (Dias)"] > 0]))
  col3.metric("No Prazo / Adiantados", len(df[df["Diferença (Dias)"] <= 0]))

  st.markdown("---")
  st.subheader("📋 Tabela de Acompanhamento de Cargas")

  display_df = df.copy()
  display_df["Data Saída"] = pd.to_datetime(display_df["Data Saída"]).dt.strftime(
      "%d/%m/%Y"
  )
  display_df["ETA Inicial"] = display_df["ETA Inicial"].dt.strftime("%d/%m/%Y")
  display_df["ETA Atual"] = display_df["ETA Atual"].dt.strftime("%d/%m/%Y")

  st.dataframe(
      display_df[
          [
              "Booking",
              "Armador",
              "Navio",
              "Origem",
              "Destino",
              "Data Saída",
              "ETA Inicial",
              "ETA Atual",
              "Status ETA",
          ]
      ],
      use_container_width=True,
  )

  # Acesso rápido ao tracking
  st.markdown("### 🔗 Acesso Rápido ao Tracking Oficial do Armador")
  cols = st.columns(len(df) if len(df) <= 4 else 4)
  for index, row in df.iterrows():
    col_idx = index % 4
    with cols[col_idx]:
      st.markdown(
          f"**{row['Booking']}** ({row['Armador']})<br>[Abrir Tracking"
          f" Oficial]({row['Link Tracking']})",
          unsafe_allow_html=True,
      )

  st.markdown("---")
  st.subheader("🔄 Atualizar ETA de um Booking")

  col_up1, col_up2, col_up3 = st.columns([2, 2, 1])
  with col_up1:
    selected_booking = st.selectbox(
        "Selecione o Booking", df["Booking"].tolist(), key="select_up"
    )
  with col_up2:
    novo_eta = st.date_input("Nova Data de ETA Atualizada", key="date_up")
  with col_up3:
    st.write("")
    st.write("")
    atualizar_btn = st.button("Atualizar ETA")

  if atualizar_btn:
    st.session_state.bookings.loc[
        st.session_state.bookings["Booking"] == selected_booking, "ETA Atual"
    ] = pd.to_datetime(novo_eta).strftime("%Y-%m-%d")
    st.success(f"O ETA do booking {selected_booking} foi atualizado!")
    st.rerun()

else:
  st.info(
      "Nenhum booking cadastrado no momento. Digite o número do booking acima"
      " para começar."
  )