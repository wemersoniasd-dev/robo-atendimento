# ============================================================
# CONFIGURAÇÃO DO NEGÓCIO
# Para atender outro tipo de empresa (pizzaria, clínica...),
# basta alterar este arquivo. Nada mais precisa mudar.
# ============================================================

NEGOCIO = {
    "nome": "Buguinha BARBER",
    "tipo": "Barbearia",
    "horario_funcionamento": "Segunda a Sábado, das 9h às 18h",
    "endereco": "Rua das Flores, 123 - Centro",
    "telefone_dono": "(11) 99999-9999",
}

# Serviços oferecidos (id, nome, duração em minutos, preço em R$)
SERVICOS = [
    {"id": 1, "nome": "Corte Feminino",   "duracao_min": 60,  "preco": 80.00},
    {"id": 2, "nome": "Corte Masculino",  "duracao_min": 40,  "preco": 45.00},
    {"id": 3, "nome": "Escova",           "duracao_min": 45,  "preco": 60.00},
    {"id": 4, "nome": "Coloração",        "duracao_min": 120, "preco": 180.00},
]

# Horários em que o robô pode marcar (o dono ajusta aqui)
HORARIOS_DISPONIVEIS = [
    "09:00", "10:00", "11:00",
    "13:00", "14:00", "15:00", "16:00", "17:00",
]

DIAS_FUNCIONAMENTO = [0, 1, 2, 3, 4, 5]  # 0=Segunda ... 6=Domingo
