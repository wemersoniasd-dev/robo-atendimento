# ============================================================
# SERVIDOR WEB (Flask)
# Expõe o robô em uma página de chat no navegador.
# No futuro, o WhatsApp será conectado neste mesmo ponto.
# ============================================================

from flask import Flask, request, jsonify, render_template

from bot.config import SERVICOS
from bot.engine import AtendimentoBot

# mapa rápido: nome do serviço -> preço (para o painel)
PRECOS = {s["nome"]: s["preco"] for s in SERVICOS}

app = Flask(__name__)
robo = AtendimentoBot()  # um único robô atende todas as conversas


@app.route("/")
def pagina_chat():
    """Página principal com a interface de chat."""
    return render_template("chat.html")


@app.route("/api/mensagem", methods=["POST"])
def receber_mensagem():
    """Recebe {'id_conversa', 'mensagem'} e devolve a resposta do robô."""
    dados = request.get_json(silent=True) or {}
    id_conversa = dados.get("id_conversa", "anonimo")
    mensagem = (dados.get("mensagem") or "").strip()

    if not mensagem:
        return jsonify({"resposta": "Não recebi nada... escreva algo! 😊"})

    resposta = robo.processar_mensagem(id_conversa, mensagem)
    return jsonify({"resposta": resposta})


@app.route("/painel")
def painel():
    """Painel do dono: agendamentos, faturamento e cancelamento."""
    return render_template("painel.html")


@app.route("/api/agendamentos", methods=["GET"])
def ver_agendamentos():
    """Lista os agendamentos em JSON (usado pelo painel do dono)."""
    from bot import database
    agendamentos = database.listar_agendamentos()
    # acrescenta o preço de cada serviço (o banco só guarda o nome)
    for a in agendamentos:
        a["preco"] = PRECOS.get(a["servico"], 0.0)
    return jsonify({"agendamentos": agendamentos})


@app.route("/api/agendamentos/<int:id_agendamento>", methods=["DELETE"])
def cancelar_agendamento(id_agendamento):
    """Cancela (exclui) um agendamento pelo id."""
    from bot import database
    ok = database.excluir_agendamento(id_agendamento)
    return jsonify({"ok": ok}), (200 if ok else 404)


if __name__ == "__main__":
    print("🤖 Robô de atendimento rodando em http://localhost:5000")
    print("📊 Painel do dono em http://localhost:5000/painel")
    app.run(debug=True, host="0.0.0.0", port=5000)
