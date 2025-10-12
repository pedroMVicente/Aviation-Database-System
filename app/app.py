#!/usr/bin/python3
# Copyright (c) BDist Development Team
# Distributed under the terms of the Modified BSD License.
import os
from logging.config import dictConfig

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool

from datetime import datetime, timedelta

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

app = Flask(__name__)
app.config.from_prefixed_env()
log = app.logger
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=RATELIMIT_STORAGE_URI,
)

# Use the DATABASE_URL environment variable if it exists, otherwise use the default.
# Use the format postgres://username:password@hostname/database_name to connect to the database.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://project06:soulindo@postgres/project06")

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    kwargs={
        "autocommit": True,  # If True don’t start transactions automatically.
        "row_factory": namedtuple_row,
    },
    min_size=4,
    max_size=10,
    open=True,
    # check=ConnectionPool.check_connection,
    name="postgres_pool",
    timeout=5,
)


def is_decimal(s):
    """Returns True if string is a parseable float number."""
    try:
        float(s)
        return True
    except ValueError:
        return False


@app.route("/", methods=("GET",))
@limiter.limit("1 per second")
def airport_index():
    """Retorna todos os aeroportos, ordenados por nome e cidade."""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT nome, cidade
                    FROM aeroporto
                ORDER BY nome, cidade;
                """,
                {},
            )

            airports = [{"nome" : linha[0], "cidade" : linha[1]} for linha in cur.fetchall()]
            log.debug(f"{cur.rowcount} linhas encontradas.")

    return jsonify({"dados": {"aeroportos": airports}, "status": "sucesso"}), 200


@app.route("/voos/<partida>/", methods=("GET",))
@limiter.limit("1 per second")
def flight_lookup(partida):
    """Retorna todos os voos que retornam nas próximas 12h."""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT no_serie, hora_partida, chegada
                    FROM voo
                WHERE partida = %(partida)s
                      AND hora_partida BETWEEN NOW()
                                               AND NOW() + INTERVAL '12 hours'
                ORDER BY hora_partida ASC;
                """,
                {"partida": partida},
            )

            voos = [{"no_serie" : linha[0], "hora_partida" : linha[1], 
                     "chegada" : linha[2]} for linha in cur.fetchall()]
            
            log.debug(f"{cur.rowcount} linhas encontradas.")

            if voos == []:
                return jsonify({"dados": {}, "mensagem": "Não foram encontrados voos "
                                "para as próximas 12 horas.", "status": "erro"}), 404

    return jsonify({"dados": {"voos": voos}, "status": "sucesso"}), 200


@app.route("/voos/<partida>/<chegada>/", methods=("GET",),)
@limiter.limit("1 per second")
def next_available_flights(partida, chegada):
    """Retorna os próximos 3 voos da rota especificada."""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT v.no_serie, v.hora_partida
                    FROM voo v JOIN assento a USING(no_serie) 
                    LEFT JOIN bilhete b ON v.id = b.voo_id AND a.lugar = b.lugar
                WHERE partida = %(partida)s
                      AND chegada = %(chegada)s
                      AND hora_partida > NOW()
                GROUP BY v.no_serie, v.hora_partida
                HAVING count(b.id) < count(a.lugar)
                ORDER BY v.hora_partida
                LIMIT 3;
                """,
                {"partida": partida,
                 "chegada": chegada},
            )

            voos = [{"no_serie" : linha[0],
                     "hora_partida" : linha[1]} for linha in cur.fetchall()]

            log.debug(f"{cur.rowcount} linhas encontradas.")

            if voos == []:
                return jsonify({"dados": {"partida": partida,
                                           "chegada": chegada},
                                "mensagem": "Não foram encontrados voos para "
                                "a rota especificada.", "status": "erro"}), 404

    return jsonify({"dados": {"voos": voos}, "status": "sucesso"}), 200


@app.route("/compra/<voo>", methods=("POST",),)
def buy_tickets_for_flight(voo):
    """Regista uma venda e cria os bilhetes associados."""

    dados = request.get_json()
    if not dados:
        return jsonify({"dados": {}, "mensagem": "JSON inválido.", "status": "erro"}), 400

    nif = dados.get("nif")  
    if not isinstance(nif,str) or not nif.strip():
        return jsonify({"dados": {"nif": nif}, "mensagem": "O nif do comprador deve "
                            "ser uma string não vazia.", "status": "erro"}), 400
    
    bilhetes = dados.get("bilhetes")
    if not isinstance(bilhetes, list) or not bilhetes:
        return jsonify({"dados": {"bilhetes": bilhetes}, "mensagem": "Os bilhetes "
                            "devem ser uma lista não vazia.", "status": "erro"}), 400
    
    for bilhete in bilhetes:
        if not isinstance(bilhete, list) or len(bilhete) != 2:
            return jsonify({"dados": {"bilhete": bilhete}, "mensagem": "O bilhete "
                            "deves ser uma lista de tamanho 2.",
                            "status": "erro"}), 400
        
        if not isinstance(bilhete[0],str) or not bilhete[0].strip():
            return jsonify({"dados": {"nome_passegeiro": bilhete[0]},
                            "mensagem": "O nome do passageiro deve ser "
                            "uma string não vazia.",
                            "status": "erro"}), 400
        
        if not isinstance(bilhete[1], bool):
            return jsonify({"dados": {"classe": bilhete[1]},
                            "mensagem": "A classe deve ser um boleano.",
                            "status": "erro"}), 400
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                with conn.transaction():
                    cur.execute(
                        """
                        SELECT 1 
                            FROM voo WHERE id = %(voo)s;
                        """,
                        {"voo": voo},
                    )

                    if cur.rowcount == 0:
                        return (
                            jsonify({"dados": {"voo": voo},
                                     "mensagem": "Voo não encontrado.",
                                     "status": "erro"}),
                            404,
                        )
                                    
                    cur.execute(
                        """
                        INSERT INTO venda (nif_cliente, hora)
                        VALUES(%(nif)s, NOW()) RETURNING codigo_reserva;
                        """,
                        {"nif": nif},
                    )

                    codigo_reserva = cur.fetchone()[0]
                    for bilhete in bilhetes:
                        preco = 150 if bilhete[1] else 80
                        cur.execute(
                            """
                            INSERT INTO bilhete (codigo_reserva, voo_id, nome_passageiro, prim_classe, preco) 
                            VALUES(%(codigo_reserva)s, %(voo)s, %(nome_passageiro)s, %(prim_classe)s, %(preco)s);
                            """,
                            {"codigo_reserva": codigo_reserva,
                            "voo": voo,
                            "nome_passageiro":bilhete[0],
                            "prim_classe": bilhete[1],
                            "preco": preco},
                        )
            except Exception as e:
                mensagem = "Ocorreu um erro ao processar o pedido."
                diag = getattr(e, "diag", None)
                if diag:
                    mensagem = getattr(diag, "message_primary", mensagem)

                log.exception("Ocorreu um erro ao processar o pedido.")
                return jsonify({"dados": {}, "mensagem": mensagem,
                                "status": "erro"}), 500
            else:
                log.debug(f"{1 + len(bilhetes)} linhas criadas.")

                return jsonify({"dados": {"codigo_venda": codigo_reserva},
                                "status": "sucesso"}), 201

@app.route("/checkin/<bilhete>/", methods=("PUT",),)
def check_in(bilhete):
    """Realiza o check-in de um bilhete, associando-lhe um lugar."""

    with pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                with conn.transaction():
                    cur.execute(
                        """
                        SELECT b.prim_classe, v.id, b.lugar
                            FROM bilhete b JOIN voo v ON (b.voo_id = v.id)
                        WHERE b.id = %(bilhete)s;
                        """,
                        {"bilhete":bilhete},
                    )
                    resultado = cur.fetchone()

                    if not resultado:
                        return jsonify({"dados": {"bilhete": bilhete},
                                        "mensagem": "Bilhete não encontrado.",
                                        "status": "erro"}), 404

                    prim_classe, voo_id, lugar = resultado

                    if lugar is not None:
                        return jsonify({"dados": {"bilhete": bilhete,
                                                  "lugar": lugar},
                                        "mensagem": "O bilhete já tem um lugar associado.",
                                        "status": "erro"}), 409

                    cur.execute(
                        """
                        SELECT a.lugar, a.no_serie
                        FROM voo v JOIN assento a USING(no_serie) 
                        LEFT JOIN bilhete b ON b.voo_id = v.id AND a.lugar = b.lugar
                        WHERE v.id = %(voo_id)s AND b.lugar IS NULL AND a.prim_classe = %(prim_classe)s
                        LIMIT 1;
                        """,
                        {"prim_classe": prim_classe,
                         "voo_id": voo_id}
                    )

                    assento = cur.fetchone()

                    if not assento:
                        return jsonify({"dados": {"voo": voo_id},
                                        "mensagem": f"Já não há lugares disponíveis no avião para a {'primeira' if prim_classe else 'segunda'} classe.",
                                        "status": "erro"}), 409
                    
                    lugar, no_serie = assento

                    cur.execute(
                        """
                        UPDATE bilhete SET lugar = %(lugar)s, no_serie = %(no_serie)s WHERE id = %(bilhete)s;
                        """,
                        {"lugar": lugar,
                         "no_serie": no_serie,
                         "bilhete": bilhete}
                    )
            except Exception as e:
                mensagem = "Ocorreu um erro ao processar o pedido."
                diag = getattr(e, "diag", None)
                if diag:
                    mensagem = getattr(diag, "message_primary", mensagem)

                log.exception("Ocorreu um erro ao processar o pedido.")
                return jsonify({"dados": {}, "mensagem": mensagem,
                                "status": "erro"}), 500
            else:
                log.debug("1 linha alterada.")
                
                return jsonify({"dados": {"lugar": lugar},
                                "status": "sucesso"}), 200

if __name__ == "__main__":
    app.run()