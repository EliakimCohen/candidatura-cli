# Candidatura CLI

Controle de candidaturas pelo terminal, com armazenamento local em SQLite. Permite registrar vagas, atualizar etapas, filtrar resultados, acompanhar um resumo e exportar CSV.

**Python 3.12+ · SQLite · argparse · unittest · sem dependências externas**

## Demonstração

Dentro desta pasta, execute em um banco novo:

```bash
python candidaturas.py adicionar "Empresa Exemplo" "Estágio Python" --data 2026-11-02
python candidaturas.py atualizar 1 entrevista
python candidaturas.py listar --status entrevista
python candidaturas.py resumo
python candidaturas.py exportar candidaturas.csv
```

Saída de `listar`:

```text
#1 | Empresa Exemplo | Estágio Python | entrevista | 2026-11-02
```

Para separar bancos: `python candidaturas.py --db demo.db listar`. Veja os comandos com `python candidaturas.py --help`.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes verificam persistência, datas inválidas, campos vazios, filtros, atualização, resumo, SQL como dado literal e exportação para planilhas.

## Decisões técnicas

- SQL usa parâmetros para manter valores separados dos comandos.
- Uma restrição no SQLite protege os status permitidos também no banco.
- Cada operação fecha sua conexão; escritas usam transações.
- Datas usam ISO 8601. Os status são `enviada`, `entrevista`, `oferta` e `encerrada`.
- CSV neutraliza prefixos de fórmula em campos textuais.

`candidaturas.py` contém a interface de linha de comando e a camada de persistência. Os testes ficam em `tests/`. Não envia currículos nem consulta empresas. O banco é local e não tem criptografia.
