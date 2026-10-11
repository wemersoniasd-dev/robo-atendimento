# ============================================================
# BANCO DE DADOS (SQLite — arquivo único, sem instalação)
# Guarda clientes e agendamentos.
# ============================================================

import sqlite3
import os

PASTA_DADOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ARQUIVO_BD = os.path.join(PASTA_DADOS, "atendimento.db")


def _conectar():
    """Abre uma conexão com o banco, criando a pasta se necessário."""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    conn = sqlite3.connect(ARQUIVO_BD)
    conn.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    return conn


def inicializar():
    """Cria as tabelas na primeira execução."""
    with _conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agendamentos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente     TEXT NOT NULL,
                telefone    TEXT,
                servico     TEXT NOT NULL,
                data_hora   TEXT NOT NULL UNIQUE,
                criado_em   TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)


def horario_ocupado(data_hora):
    """Verifica se já existe agendamento nesse data_hora (formato AAAA-MM-DD HH:MM)."""
    with _conectar() as conn:
        linha = conn.execute(
            "SELECT 1 FROM agendamentos WHERE data_hora = ?", (data_hora,)
        ).fetchone()
    return linha is not None


def criar_agendamento(cliente, telefone, servico, data_hora):
    """Salva um agendamento. Retorna (True, msg_sucesso) ou (False, msg_erro)."""
    if horario_ocupado(data_hora):
        return False, "horario_ocupado"
    with _conectar() as conn:
        conn.execute(
            "INSERT INTO agendamentos (cliente, telefone, servico, data_hora) "
            "VALUES (?, ?, ?, ?)",
            (cliente, telefone, servico, data_hora),
        )
    return True, "ok"


def listar_agendamentos():
    """Lista todos os agendamentos, em ordem cronológica."""
    with _conectar() as conn:
        linhas = conn.execute(
            "SELECT id, cliente, telefone, servico, data_hora, criado_em "
            "FROM agendamentos ORDER BY data_hora"
        ).fetchall()
    return [dict(l) for l in linhas]


def excluir_agendamento(id_agendamento):
    """Remove um agendamento pelo id. Retorna True se excluiu algo."""
    with _conectar() as conn:
        cursor = conn.execute(
            "DELETE FROM agendamentos WHERE id = ?", (id_agendamento,)
        )
    return cursor.rowcount > 0


# Cria as tabelas assim que o módulo é importado
inicializar()
