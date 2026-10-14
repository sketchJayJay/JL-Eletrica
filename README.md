# JL Elétrica

Sistema web de controle para elétrica automotiva, som, alarme e acessórios.

## Principais recursos
- Dashboard mensal
- Cadastro de clientes
- Cadastro de locais/instalações
- Ordens de serviço
- Orçamentos
- Pesquisa rápida
- Editar e excluir registros
- Alteração de status
- Marcar orçamento como aprovado
- Converter orçamento aprovado em OS
- Controle de pagamentos
- Impressão de OS e orçamento
- Layout responsivo para celular
- Banco SQLite persistente em volume Docker

## Coolify
1. Suba esta pasta para um repositório Git.
2. No Coolify escolha Docker Compose.
3. O arquivo já está na raiz: `docker-compose.yaml`.
4. Faça o deploy.
5. Se quiser, defina `SECRET_KEY` nas variáveis de ambiente.

A porta interna é 8000.

## Inicialização do banco
O banco SQLite é inicializado uma única vez por `init_db.py` antes do Gunicorn, evitando conflito entre workers no primeiro deploy.

## Foco automotivo
- Cadastro de veículos por cliente
- Placa, marca, modelo, ano e cor
- Histórico de OS e orçamento por veículo
- Quilometragem
- Categorias: elétrica automotiva, som, alarme, acessórios, iluminação e diagnóstico

## Atualização premium
- Nova identidade visual com logo automotiva
- Layout premium grafite/amarelo
- Nova OS em formato profissional para impressão
- Envio direto da OS por WhatsApp com cliente, veículo, placa, itens e total
- Dashboard e atalhos redesenhados
