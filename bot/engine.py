# ============================================================
# MOTOR DA CONVERSA (máquina de estados)
# Cada conversa tem um "estado" (em que passo está) e cada
# mensagem do cliente avança um passo. É aqui que o robô pensa.
# ============================================================

import unicodedata
import datetime

from . import config
from . import database


# ---------- utilitários ----------

def _sem_acento(texto):
    """Remove acentos: 'agendamento' == 'agendamentô' etc."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def _normalizar(texto):
    """Minúsculas, sem acentos, espaços extras removidos."""
    return " ".join(_sem_acento(texto.lower()).split())


def _contem(texto, palavras):
    """Verifica se alguma das palavras aparece no texto."""
    return any(p in texto for p in palavras)


def _formatar_data_legivel(data_iso):
    """'2026-10-05' -> '05/10/2026 (segunda-feira)'"""
    data = datetime.date.fromisoformat(data_iso)
    dias = ["segunda-feira", "terça-feira", "quarta-feira",
            "quinta-feira", "sexta-feira", "sábado", "domingo"]
    nome_dia = dias[data.weekday()]
    return f"{data.strftime('%d/%m/%Y')} ({nome_dia})"


# ---------- o robô ----------

class AtendimentoBot:
    """Gerencia várias conversas ao mesmo tempo (uma por cliente)."""

    def __init__(self):
        # Guarda o estado de cada conversa em memória.
        # Em uma versão futura isso vai para o banco de dados.
        self.conversas = {}

    # ---- ponto de entrada ----
    def processar_mensagem(self, id_conversa, texto):
        """Recebe uma mensagem do cliente e devolve a resposta."""
        estado = self.conversas.get(id_conversa)

        if estado is None:
            estado = {"passo": "inicio", "dados": {}}
            self.conversas[id_conversa] = estado

        # comando universal: cancelar/recomeçar a qualquer momento
        if _contem(_normalizar(texto), ["cancelar", "sair", "recomecar"]):
            self.conversas.pop(id_conversa, None)
            resposta, _ = self._menu_inicial("Sem problemas! Recomeçando do zero. 😊")
            return resposta

        passos = {
            "inicio": self._passo_inicio,
            "menu": self._passo_menu,
            "agendar_servico": self._passo_agendar_servico,
            "agendar_data": self._passo_agendar_data,
            "agendar_hora": self._passo_agendar_hora,
            "agendar_nome": self._passo_agendar_nome,
            "agendar_telefone": self._passo_agendar_telefone,
            "confirmar": self._passo_confirmar,
        }
        resultado = passos[estado["passo"]](id_conversa, texto)

        # um passo pode devolver (texto, novo_passo) — nesse caso
        # aplicamos a troca de estado aqui, de forma centralizada
        if isinstance(resultado, tuple):
            resposta, novo_passo = resultado
            self._trocar_passo(id_conversa, novo_passo)
            return resposta
        return resultado

    # ---- passo 0: boas-vindas ----
    def _passo_inicio(self, id_conversa, texto):
        saudacao = (
            f"👋 Olá! Bem-vindo(a) à *{config.NEGOCIO['nome']}*!\n\n"
            "Atendimento automático 24 horas. Como posso ajudar?"
        )
        return self._menu_inicial(saudacao)

    def _menu_inicial(self, cabecalho):
        return (
            f"{cabecalho}\n\n"
            "Escolha uma opção:\n"
            "1️⃣ - Agendar um horário\n"
            "2️⃣ - Ver serviços e preços\n"
            "3️⃣ - Horário de funcionamento e endereço\n"
            "4️⃣ - Falar com o responsável"
        ), "menu"

    # ---- passo 1: menu principal ----
    def _passo_menu(self, id_conversa, texto):
        t = _normalizar(texto)

        if _contem(t, ["1", "agendar", "marcar", "horario livre"]):
            self._trocar_passo(id_conversa, "agendar_servico")
            return self._lista_servicos()
        if _contem(t, ["2", "preco", "precos", "servico", "servicos", "valor"]):
            return self._tabela_precos()
        if _contem(t, ["3", "horario funcionamento", "funciona", "endereco", "onde", "aberto"]):
            return self._info_negocio()
        if _contem(t, ["4", "responsavel", "atendente", "dono", "humano", "pessoa"]):
            return self._falar_com_dono()

        return self._menu_inicial("Não entendi 🤔 Escolha uma das opções:")

    # ---- fluxo de agendamento (4 perguntas) ----
    def _passo_agendar_servico(self, id_conversa, texto):
        t = _normalizar(texto)
        escolhido = None

        # o cliente pode digitar o número OU o nome do serviço
        for servico in config.SERVICOS:
            if (t == str(servico["id"])
                    or servico["nome"].lower() in t):
                escolhido = servico
                break

        if escolhido is None:
            return self._lista_servicos("Escolha o número ou nome de um serviço:")

        self.conversas[id_conversa]["dados"]["servico"] = escolhido
        self._trocar_passo(id_conversa, "agendar_data")
        return (f"Ótima escolha! ✂️\n\n"
                f"Agora me diga a *data* desejada (ex.: 15/10 ou amanhã):")

    def _passo_agendar_data(self, id_conversa, texto):
        t = _normalizar(texto)
        hoje = datetime.date.today()

        # atalhos em linguagem natural
        if "amanha" in t:
            data = hoje + datetime.timedelta(days=1)
        elif "hoje" in t:
            data = hoje
        else:
            data = self._interpretar_data(texto)
            if data is None:
                return "Não entendi a data 🤔\nUse o formato dia/mês, ex.: *15/10*"

        if data.weekday() not in config.DIAS_FUNCIONAMENTO:
            return ("Ops, não atendemos nesse dia da semana. 😅\n"
                    f"Atendemos: {config.NEGOCIO['horario_funcionamento']}\n"
                    "Escolha outra data:")

        self.conversas[id_conversa]["dados"]["data"] = data
        self._trocar_passo(id_conversa, "agendar_hora")

        # mostra somente horários livres nesse dia
        livres = [h for h in config.HORARIOS_DISPONIVEIS
                  if not database.horario_ocupado(f"{data.isoformat()} {h}")]
        if not livres:
            return ("Esse dia já está com a agenda cheia! 😔\n"
                    "Escolha outra data:")
        lista = "  |  ".join(livres)
        return f"Horários livres em {_formatar_data_legivel(data.isoformat())}:\n\n{lista}\n\nQual você prefere?"

    def _passo_agendar_hora(self, id_conversa, texto):
        t = _normalizar(texto)
        hora_escolhida = None

        # extrai o primeiro número da mensagem (aceita "14", "14:00", "14h")
        import re
        numero = re.search(r"\d{1,2}", t)
        if numero:
            hora_digitada = f"{int(numero.group()):02d}"
            for horario in config.HORARIOS_DISPONIVEIS:
                if horario[:2] == hora_digitada:
                    hora_escolhida = horario
                    break

        if hora_escolhida is None:
            return "Escolha um dos horários listados, por favor. 🙏 (ex.: 14:00)"

        dados = self.conversas[id_conversa]["dados"]
        data_hora = f"{dados['data'].isoformat()} {hora_escolhida}"

        if database.horario_ocupado(data_hora):
            return "Esse horário acabou de ser ocupado! Escolha outro, por favor. 🙏"

        dados["data_hora"] = data_hora
        self._trocar_passo(id_conversa, "agendar_nome")
        return "Perfeito! ⏰\n\nAgora, qual é o seu *nome*?"

    def _passo_agendar_nome(self, id_conversa, texto):
        nome = texto.strip().title()
        if len(nome) < 2:
            return "Pode me dizer seu nome completo? 😊"
        self.conversas[id_conversa]["dados"]["cliente"] = nome
        self._trocar_passo(id_conversa, "agendar_telefone")
        return f"Prazer, {nome}! 🤝\n\nQual é o seu *WhatsApp* para confirmarmos?"

    def _passo_agendar_telefone(self, id_conversa, texto):
        telefone = "".join(c for c in texto if c.isdigit())
        if len(telefone) < 10:
            return "Hmm, esse número parece incompleto. Ex.: (11) 98888-7777"
        self.conversas[id_conversa]["dados"]["telefone"] = telefone

        # resumo para confirmação
        d = self.conversas[id_conversa]["dados"]
        data_legivel = _formatar_data_legivel(d["data"].isoformat())
        resumo = (
            "Confirme o agendamento, por favor:\n\n"
            f"💆 *Serviço:* {d['servico']['nome']}\n"
            f"📅 *Data:* {data_legivel}\n"
            f"⏰ *Hora:* {d['data_hora'][-5:]}\n"
            f"👤 *Cliente:* {d['cliente']}\n"
            f"💵 *Valor:* R$ {d['servico']['preco']:.2f}\n\n"
            "Está tudo certo? (sim / não)"
        )
        self._trocar_passo(id_conversa, "confirmar")
        return resumo

    def _passo_confirmar(self, id_conversa, texto):
        t = _normalizar(texto)
        d = self.conversas[id_conversa]["dados"]

        if _contem(t, ["sim", "ok", "certo", "isso", "confirmo"]):
            ok, _ = database.criar_agendamento(
                d["cliente"], d["telefone"],
                d["servico"]["nome"], d["data_hora"],
            )
            self.conversas.pop(id_conversa, None)  # conversa concluída
            if ok:
                return ("✅ *Agendamento confirmado!*\n\n"
                        "Te esperamos! Avisaremos o responsável sobre seu horário.\n"
                        "Precisa de mais alguma coisa? (digite *menu*)")
            return "Tivemos um problema ao salvar. Tente novamente com *menu*."

        self.conversas.pop(id_conversa, None)
        return self._menu_inicial("Sem problemas, cancelado! Vamos recomeçar:")

    # ---- respostas informativas ----
    def _lista_servicos(self, cabecalho="Temos os seguintes serviços:"):
        linhas = [f"{s['id']}️⃣ - {s['nome']} ({s['duracao_min']} min)" 
                  for s in config.SERVICOS]
        return ("\n".join([cabecalho] + linhas) +
                "\n\nQual você deseja? (número ou nome)")

    def _tabela_precos(self):
        linhas = [f"• {s['nome']}: *R$ {s['preco']:.2f}*" for s in config.SERVICOS]
        return ("💰 *Serviços e preços*\n\n" + "\n".join(linhas) +
                "\n\nDeseja agendar? Digite *1*")

    def _info_negocio(self):
        n = config.NEGOCIO
        return (f"ℹ️ *{n['nome']}*\n\n"
                f"🕘 Horário: {n['horario_funcionamento']}\n"
                f"📍 Endereço: {n['endereco']}\n\n"
                "Deseja agendar? Digite *1*")

    def _falar_com_dono(self):
        n = config.NEGOCIO
        return (f"👤 Para falar com o responsável:\n\n"
                f"📱 {n['telefone_dono']}\n\n"
                "(Nos próximos dias o robô mesmo encaminha a mensagem! 😉)\n\n"
                "Digite *menu* para voltar.")

    # ---- ajudantes ----
    def _trocar_passo(self, id_conversa, novo_passo):
        self.conversas[id_conversa]["passo"] = novo_passo

    def _interpretar_data(self, texto):
        """Converte '15/10' ou '15/10/2026' em date. Retorna None se inválido."""
        partes = texto.strip().split("/")
        try:
            dia, mes = int(partes[0]), int(partes[1])
            ano = int(partes[2]) if len(partes) > 2 else datetime.date.today().year
            return datetime.date(ano, mes, dia)
        except (ValueError, IndexError):
            return None
