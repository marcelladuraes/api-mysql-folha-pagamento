from flask import Flask
from flask_restful import reqparse, Api, Resource, fields

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@localhost/empresa'

db = SQLAlchemy(app)
marshmallow = Marshmallow(app)

class FuncionarioDataBase(db.Model):
  __tablename__ = "Funcionario"
  cpf = db.Column(db.Integer, primary_key = True)
  nome = db.Column(db.String(256), unique = True, nullable = False)
  horas_trabalhadas = db.Column(db.Integer, nullable = False)
  valor_hora = db.Column(db.Float, nullable = False)

  def __init__(self, cpf, nome, horas_trabalhadas, valor_hora):
    self.cpf = cpf
    self.nome = nome
    self.horas_trabalhadas = horas_trabalhadas
    self.valor_hora = valor_hora

  def create(self):
    db.session.add(self)
    db.session.commit()
    return self

  def __repr__(self):
    return f"{self.cpf, self.nome, self.horas_trabalhadas, self.valor_hora}"

class FuncionarioDataBaseSchema(marshmallow.SQLAlchemyAutoSchema):
  class Meta:
    model = FuncionarioDataBase
    sqla_session = db.session
  
  cpf = fields.Number()#dump_only=True)
  nome = fields.String(required=True)
  horas_trabalhadas = fields.Number(required=True)
  valor_hora = fields.Float(required=True)


api = Api(app)

# Parse dos dados enviados na requisição no formato JSON:
parser = reqparse.RequestParser()
parser.add_argument('cpf', type=int, help='cpf do funcionario')
parser.add_argument('nome', type=str, help='nome do funcionario')
parser.add_argument('horas_trabalhadas', type=int, help='quantidade de horas trabalhadas pelo funcionario')
parser.add_argument('valor_hora', type=float, help='valor da hora trabalhada pelo funcionario')

# Produto:
# 1) Apresenta um único produto.
# 2) Remove um único produto.
# 3) Atualiza (substitui) um produto.
class Funcionario(Resource):
  def get(self, cpf):
    funcionario = FuncionarioDataBase.query.get(cpf)
    funcionario_schema = FuncionarioDataBaseSchema()
    resp = funcionario_schema.dump(funcionario)
    return {"funcionario": resp}, 200 #200: Ok
  
  def delete(self, cpf):
    funcionario = FuncionarioDataBase.query.get(cpf)
    db.session.delete(funcionario)
    db.session.commit()
    return '', 204 #204: No Content

  
  def put(self, cpf):
    funcionario_json = parser.parse_args()
    funcionario = FuncionarioDataBase.query.get(cpf)
    
    if funcionario_json.get('nome'):
      funcionario.nome = funcionario_json.nome
    if funcionario_json.get('horas_trabalhadas'):
       funcionario.horas_trabalhadas = funcionario_json.horas_trabalhadas
    if funcionario_json.get('valor_hora'):
       funcionario.valor_hora = funcionario_json.valor_hora
     
    db.session.add(funcionario)
    db.session.commit()
    
    funcionario_schema = FuncionarioDataBaseSchema(only=['cpf', 'nome', 'horas_trabalhadas', 'valor_hora'])
    resp = funcionario_schema.dump(funcionario)
     
    return {"funcionario": resp}, 200 #200: OK

  def patch(self, cpf, nome):
    funcionario_schema = FuncionarioDataBaseSchema()
    funcionarios = FuncionarioDataBase.query.all()
    for funcionario in funcionarios:
        prod = funcionario_schema.dump(funcionario)
        if prod['cpf'] == int(cpf):
            prod['nome'] = str(nome)
    return prod

# ListaProduto:
# 1) Apresenta a lista de produtos.
# 2) Insere um novo produto.
class ListaFuncionario(Resource):
  def get(self):
    funcionarios = FuncionarioDataBase.query.all()
    funcionario_schema = FuncionarioDataBaseSchema(many=True) # Converter objto Python para JSON.
    resp = funcionario_schema.dump(funcionarios)
    return {"funcionarios": resp}, 200 #200: Ok

  def post(self):
     
    funcionario_json = parser.parse_args()
    funcionario_schema = FuncionarioDataBaseSchema()
    funcionario = funcionario_schema.load(funcionario_json)
    funcionarioDataBase = FuncionarioDataBase(funcionario["cpf"], funcionario["nome"], funcionario["horas_trabalhadas"], funcionario["valor_hora"])
    resp = funcionario_schema.dump(funcionarioDataBase.create())
    return {"funcionario": resp}, 201 #201: Created



    

class ValorTotalFolha(Resource):    
    def get(self):
        total = 0
        funcionario_schema = FuncionarioDataBaseSchema()
        funcionarios = FuncionarioDataBase.query.all()
        for funcionario in funcionarios:
            prod = funcionario_schema.dump(funcionario)
            total = total + prod["horas_trabalhadas"] * prod["valor_hora"]
        return {"Valor total a ser pago" : total}

class ValorFolhaFuncionario(Resource):
    def get(self, cpf):
        funcionario_schema = FuncionarioDataBaseSchema()
        funcionarios = FuncionarioDataBase.query.all()
        for funcionario in funcionarios:
            prod = funcionario_schema.dump(funcionario)
            if prod['cpf'] == int(cpf):
                return prod['horas_trabalhadas']*prod['valor_hora']

class ValorFolhaFuncionarioTodos(Resource):    
    def get(self):
        funcionario_schema = FuncionarioDataBaseSchema()
        funcionarios = FuncionarioDataBase.query.all()
        for funcionario in funcionarios:
            prod = funcionario_schema.dump(funcionario)
            total = total + prod["horas_trabalhadas"]*prod['valor_hora']
        return total


class Pagamento(Resource):
    def get(self):
        funcionario_schema = FuncionarioDataBaseSchema()
        funcionarios = FuncionarioDataBase.query.all()
        prod = funcionario_schema.dump(funcionarios[0])
        menor =  prod["horas_trabalhadas"] * prod["valor_hora"]
        maior =  prod["horas_trabalhadas"] * prod["valor_hora"]

        for funcionario in funcionarios:
            prod = funcionario_schema.dump(funcionario)
            if prod["horas_trabalhadas"] * prod["valor_hora"] < menor:
                menor = prod["horas_trabalhadas"] * prod["valor_hora"]
            if prod["horas_trabalhadas"] * prod["valor_hora"] > maior:
                maior = prod["horas_trabalhadas"] * prod["valor_hora"]          
        dados_estoque = {
            "Menor pagamento": menor,
            "Maior pagamento":maior}
        return dados_estoque

## Roteamento de recursos: 
## 
api.add_resource(Funcionario, '/funcionarios/<cpf>')
api.add_resource(ListaFuncionario, '/funcionarios')
api.add_resource(ValorTotalFolha, '/valor/total')
api.add_resource(ValorFolhaFuncionario, '/valor/total/<cpf>')
api.add_resource(ValorFolhaFuncionarioTodos, '/funcionarios/total')
api.add_resource(Pagamento, '/pagamento')


 
if __name__ == '__main__':
  with app.app_context():
    db.create_all()
  app.run(debug=True)