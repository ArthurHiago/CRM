🧩 CRM Básico com Python, FastAPI e SQLModel

Este projeto é uma API RESTful completa para gerenciamento de clientes (CRM).
Desenvolvida em Python, utilizando FastAPI para criação dos endpoints e SQLModel para mapeamento e persistência dos dados em um banco SQLite.

A API oferece operações CRUD completas:

Criar clientes

Listar clientes com paginação

Consultar cliente por ID

Atualizar dados de clientes

Excluir clientes

A estrutura do banco é totalmente gerenciada pelo SQLModel, e as tabelas são criadas automaticamente na inicialização da aplicação. O projeto usa o padrão de lifespan do FastAPI para configurar o banco ao iniciar a API.

Ideal como base para estudos, pequenos sistemas internos ou como ponto de partida para um CRM mais robusto.
