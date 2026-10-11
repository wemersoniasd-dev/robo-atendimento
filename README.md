# 🤖 Robô de Atendimento 24h para Pequenos Negócios

Assistente automático que recebe clientes, mostra serviços e preços,
**agenda horários** e registra tudo em um banco de dados — 24 horas por dia.

Pensado para cabeleireiros, pizzarias, clínicas odontológicas, barbearias etc.

## ▶️ Como executar (3 passos)

```bash
# 1. Entre na pasta do projeto
cd robo-atendimento

# 2. Instale a única dependência
pip install -r requirements.txt

# 3. Ligue o robô
python app.py
```

Depois abra no navegador: **http://localhost:5000**

> 💡 Para testar em outro computador/celular na mesma rede:
> troque a última linha de `app.run(...)` por
> `app.run(debug=True, host="0.0.0.0", port=5000)` e use o IP do PC.

## 🗨️ O que o robô já faz (Fase 1)

| Funcionalidade | Como testar |
|---|---|
| Menu de atendimento | envie `oi` |
| Agendamento completo | envie `1` e responda as perguntas |
| Preços e serviços | envie `2` |
| Horário e endereço | envie `3` |
| Falar com o responsável | envie `4` |
| Cancelar a qualquer momento | envie `cancelar` |

O agendamento **recusa horários já ocupados** e **salva no banco de dados**
(`data/atendimento.db`).

Painel do dono (JSON): http://localhost:5000/api/agendamentos

## 🗂️ Estrutura do projeto

```
robo-atendimento/
├── app.py              # servidor web (ponto de conexão com canais)
├── requirements.txt    # dependências
├── bot/
│   ├── config.py       # nome do negócio, serviços, preços, horários
│   ├── database.py     # banco de dados SQLite
│   └── engine.py       # cérebro: máquina de estados da conversa
├── templates/
│   └── chat.html       # interface de chat (estilo WhatsApp)
└── data/               # criado automaticamente (banco de dados)
```

**Para atender outra empresa** (pizzaria, dentista...): edite apenas
`bot/config.py`. Nada mais precisa mudar.

## 🗺️ Roadmap

- [x] **Fase 1** — robô com menu + agendamento + banco de dados *(atual)*
- [ ] **Fase 2** — lembretes automáticos + painel web para o dono
- [ ] **Fase 3** — integração com WhatsApp Business API
- [ ] **Fase 4** — IA para conversa em linguagem natural

## 🔌 Como o WhatsApp entrará depois

A integração futura trocará apenas a "porta de entrada": hoje o navegador
envia mensagens via `POST /api/mensagem`; amanhã será o webhook do
WhatsApp. **O robô (engine + banco) não muda** — essa foi a decisão de
arquitetura que mantém o projeto simples e preparado para crescer.
