"""Controle local de candidaturas com SQLite e interface de linha de comando."""

import argparse
import csv
import sqlite3
import sys
from contextlib import closing
from datetime import date
from pathlib import Path

STATUS = ("enviada", "entrevista", "oferta", "encerrada")


class Tracker:
    def __init__(self, database="candidaturas.db"):
        self.database = database
        with closing(self.connect()) as connection, connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY,
                    company TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (
                        status IN ('enviada', 'entrevista', 'oferta', 'encerrada')
                    ),
                    applied_on TEXT NOT NULL
                )
            """)

    def connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    def add(self, company, role, applied_on=None):
        company, role = company.strip(), role.strip()
        if not company or not role:
            raise ValueError("Empresa e cargo não podem ficar vazios.")
        applied_on = date.fromisoformat(applied_on).isoformat() if applied_on else date.today().isoformat()
        with closing(self.connect()) as connection, connection:
            cursor = connection.execute(
                "INSERT INTO applications (company, role, status, applied_on) VALUES (?, ?, ?, ?)",
                (company, role, "enviada", applied_on),
            )
            return cursor.lastrowid

    def list(self, status=None):
        if status is not None and status not in STATUS:
            raise ValueError("Status inválido.")
        query = "SELECT * FROM applications"
        parameters = ()
        if status:
            query += " WHERE status = ?"
            parameters = (status,)
        with closing(self.connect()) as connection:
            return [dict(row) for row in connection.execute(query + " ORDER BY id DESC", parameters)]

    def update(self, application_id, status):
        if status not in STATUS:
            raise ValueError("Status inválido.")
        with closing(self.connect()) as connection, connection:
            cursor = connection.execute("UPDATE applications SET status = ? WHERE id = ?", (status, application_id))
            if not cursor.rowcount:
                raise ValueError("Candidatura não encontrada.")

    def summary(self):
        result = dict.fromkeys(STATUS, 0)
        with closing(self.connect()) as connection:
            for row in connection.execute("SELECT status, COUNT(*) AS total FROM applications GROUP BY status"):
                result[row["status"]] = row["total"]
        return result

    def export(self, destination):
        target = Path(destination)
        source = Path(self.database)
        if target.resolve() == source.resolve() or (target.exists() and source.exists() and target.samefile(source)):
            raise ValueError("A exportação não pode sobrescrever o banco de dados.")
        # Protege a abertura do CSV em planilhas contra fórmulas nas células.
        def safe(value):
            return "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value

        rows = self.list()
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("id", "company", "role", "status", "applied_on"))
            for row in rows:
                writer.writerow(safe(row[key]) for key in ("id", "company", "role", "status", "applied_on"))
        return len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="candidaturas.db", help="Caminho do banco SQLite")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("adicionar", help="Registrar candidatura")
    add.add_argument("empresa")
    add.add_argument("cargo")
    add.add_argument("--data", help="Data no formato AAAA-MM-DD")
    listing = commands.add_parser("listar", help="Listar candidaturas")
    listing.add_argument("--status", choices=STATUS)
    update = commands.add_parser("atualizar", help="Alterar etapa")
    update.add_argument("id", type=int)
    update.add_argument("status", choices=STATUS)
    commands.add_parser("resumo", help="Contagem por etapa")
    export = commands.add_parser("exportar", help="Exportar CSV")
    export.add_argument("arquivo")
    args = parser.parse_args(argv)
    try:
        tracker = Tracker(args.db)
        if args.command == "adicionar":
            print(f"Candidatura #{tracker.add(args.empresa, args.cargo, args.data)} registrada.")
        elif args.command == "listar":
            rows = tracker.list(args.status)
            if not rows:
                print("Nenhuma candidatura encontrada.")
            for row in rows:
                print(f"#{row['id']} | {row['company']} | {row['role']} | {row['status']} | {row['applied_on']}")
        elif args.command == "atualizar":
            tracker.update(args.id, args.status)
            print("Etapa atualizada.")
        elif args.command == "resumo":
            for status, total in tracker.summary().items():
                print(f"{status}: {total}")
        else:
            print(f"{tracker.export(args.arquivo)} candidatura(s) exportada(s).")
    except (ValueError, OSError, sqlite3.Error) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
