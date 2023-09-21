from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect, render_template, request, abort, flash, session
from urllib.parse import unquote

from sqlalchemy.exc import IntegrityError

from model import Session, Despesas
from logger import logger
from schemas import *
from flask_cors import CORS

info = Info(title="Despesa API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

# definindo tags
home_tag = Tag(name="Documentação", description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
despesa_tag = Tag(name="Despesa", description="Adição, visualização e remoção de despesas à base")
usuario_tag = Tag(name="Usuario", description="Transfere para o serviço de Login para autenticar o usuário")

@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação.
    """
    return redirect('/openapi')

@app.post('/incluir_despesa', tags=[despesa_tag],
          responses={"200": DespesasViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def add_despesa(form: DespesasSchema):
    """Adiciona uma nova despesa à base de dados

    Retorna uma representação das despesas
    """
    despesa = Despesas(
        nome=form.nome,
        categoria=form.categoria,
        valor=form.valor,
        data_despesa=form.data_despesa,
        comentario=form.comentario)
    logger.debug(f"Adicionando despesa: '{despesa.nome}'")
    print('data despesa', despesa.data_despesa)
    try:
        # criando conexão com a base
        session = Session()
        # adicionando produto
        session.add(despesa)
        # efetivando o camando de adição de novo item na tabela
        session.commit()
        logger.debug(f"Adicionado despesa: '{despesa.nome}'")
        return apresenta_despesa(despesa), 200

    except IntegrityError as e:
        # como a duplicidade do nome é a provável razão do IntegrityError
        error_msg = "Despesa de mesmo nome já salvo na base :/"
        #ogger.warning(f"Erro ao adicionar despesa '{despesa.nome}', {error_msg}")
        return {"mesage": error_msg}, 409

    except Exception as e:
        # caso um erro fora do previsto
        error_msg = "Não foi possível salvar novo item :/"
        logger.warning(f"Erro ao adicionar despesa '{despesa.nome}', {error_msg}")
        return {"mesage": error_msg}, 400


@app.get('/buscar_despesa', tags=[despesa_tag],
         responses={"200": ListagemDespesasSchema, "404": ErrorSchema})
def get_despesas():
    """Faz a busca por todas as despesas cadastradas

    Retorna uma representação da listagem de despesas.
    """
    #logger.debug(f"Coletando despesas ")
    # criando conexão com a base
    session = Session()
    # fazendo a busca
    despesas = session.query(Despesas).all()

    if not despesas:
        # se não há despesas cadastradas
        return {"despesas": []}, 200
    else:
        logger.debug(f"%d despesas econtradas" % len(despesas))
        # retorna a representação da despesa
        return apresenta_despesas(despesas), 200


@app.delete('/deletar_despesa', tags=[despesa_tag],
            responses={"200": DespesasSchema, "404": ErrorSchema})
def del_despesa(query: DespesasViewSchema):
    """Exclui uma despesa a partir do id da despesa informada

    Retorna uma mensagem de confirmação da remoção.
    """
    despesa_id = query.id
    despesa_nome = unquote(unquote(query.nome))
    despesa_categoria = unquote(unquote(query.categoria))
    despesa_valor = query.valor
    despesa_data_despesa = query.data_despesa
    logger.debug(f"Deletando dados sobre a despesa #{despesa_nome}")
    # criando conexão com a base
    session = Session()
    # fazendo a remoção
    count = session.query(Despesas).filter(Despesas.id == despesa_id).delete()
    session.commit()

    if count:
        # retorna a representação da mensagem de confirmação
        logger.debug(f"Deletada despesa #{despesa_nome}")
        return {"mesage": "Despesa removida", "id": despesa_nome}
    else:
        # se a despesa não foi encontrada
        error_msg = "Despesa não encontrada na base :/"
        logger.warning(f"Erro ao deletar despesa {despesa_nome}', {error_msg}")
        return {"mesage": error_msg}, 404


@app.put('/alterar_despesa', tags=[despesa_tag],
          responses={"200": DespesasViewSchema, "409": ErrorSchema, "400": ErrorSchema})

def alt_despesa(form: DespesasViewSchema):
    """Altera uma despesa na base de dados

    Retorna uma representação das despesas
    """
    despesa = Despesas(
        nome=form.nome,
        categoria=form.categoria,
        valor=form.valor,
        data_despesa=form.data_despesa,
        comentario=form.comentario)

    logger.debug(f"Alterando despesa: '{despesa.nome}'")
    print('alterar despesa.......................',  despesa.nome, despesa.categoria)

    try:
        session = Session()
        # Alterando despesa
        my_despesa = session.query(Despesas).get(form.id)
        my_despesa.nome = despesa.nome
        my_despesa.categoria = despesa.categoria
        my_despesa.valor = despesa.valor
        my_despesa.data_despesa = despesa.data_despesa
        my_despesa.comentario = despesa.comentario
        # efetivando o comando de alteração doitem na tabela
        session.commit()
        return apresenta_despesa(despesa), 200


    except Exception as e:
        # caso um erro fora do previsto
        error_msg = "Não foi possível salvar novo item :/"
        logger.warning(f"Erro ao adicionar despesa '{despesa.nome}', {error_msg}")
        return {"mesage": error_msg}, 400

@app.get ('/login', tags=[usuario_tag])

def do_login(email, senha):
    """Faz o Autenticação do usuário no sistema

    Retorna o nome do usuário autenticado e libera o sistema para o seu uso
    """
    try:
        req = requests.get("http://127.0.0.1:5001/login?email=" + email + "&senha=" + senha)
    except requests.exceptions.ConnectionError:
        return "Service unavailable"
    return req.text
