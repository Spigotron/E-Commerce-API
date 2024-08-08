from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields, ValidationError
from sqlalchemy import delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from typing import List
import datetime

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://root:*********@localhost/ecommerce_app"

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)

class Customer(Base):
    __tablename__ = "Customers"
    customer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable = False)
    email: Mapped[str] = mapped_column(db.String(320))
    phone: Mapped[str] = mapped_column(db.String(15))
    orders: Mapped[List["Order"]] = db.relationship(back_populates="customer")

order_product= db.Table(
    "Order_Product",
    Base.metadata,
    db.Column("order_id", db.ForeignKey("Orders.order_id"), primary_key=True),
    db.Column("product_id", db.ForeignKey("Products.product_id"), primary_key=True)
)

class Order(Base):
    __tablename__ = "Orders"
    order_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customers.customer_id'))
    delivery_date: Mapped[datetime.date] = mapped_column(db.Date, nullable=False)
    ordered_product: Mapped[str] = mapped_column(db.String(255), nullable=False)
    customer: Mapped["Customer"] = db.relationship(back_populates="orders")
    products: Mapped[List["Product"]] = db.relationship(secondary=order_product)

class Product(Base):
    __tablename__ = "Products"
    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

class CustomerSchema(ma.Schema):
    id = fields.Integer(required=False)
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ("id", "name", "email", "phone")

class CustomersSchema(ma.Schema):
    customer_id = fields.Integer(required=True)
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ("customer_id", "name", "email", "phone")

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

@app.route("/customers", methods = ["GET"])
def get_customers():
    query = select(Customer)
    result = db.session.execute(query).scalars()
    print(result)
    customers = result.all()
    return customers_schema.jsonify(customers)

@app.route("/customers/<int:id>", methods = ["GET"])
def get_customer_by_id(id):
    query = select(Customer).filter(Customer.customer_id==id)
    customer = db.session.execute(query).scalars().first()
    if customer:
        return customer_schema.jsonify(customer)
    else:
        return jsonify({"Error": "Customer Not Found"}), 404

@app.route("/customers", methods = ["POST"])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
        print(customer_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    with Session(db.engine) as session:
        new_customer = Customer(name=customer_data["name"], email=customer_data["email"], phone=customer_data["phone"])
        session.add(new_customer)
        session.commit() 
    return jsonify({"Success": "Customer Added"}), 201

@app.route("/customers/<int:id>", methods = ["PUT"])
def update_customer(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Customer).filter(Customer.customer_id == id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"Error": "Customer Not Found"}), 404
            customer = result
        try:
            customer_data = customer_schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400
        for field, value in customer_data.items():
            setattr(customer, field, value)
        session.commit()
        return jsonify({"Success": "Customer Updated"}), 200

@app.route("/customers/<int:id>", methods = ["DELETE"])
def delete_customer(id):
    delete_statement = delete(Customer).where(Customer.customer_id == id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"Error": "Customer Not Found"}), 404
        return jsonify({"Success": "Customer Deleted"}), 200

class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=False)
    name = fields.String(required=True)
    price = fields.Float(required=True)

    class Meta:
        fields = ("product_id", "name", "price")

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

@app.route("/products", methods = ["GET"])
def get_products():
    query = select(Product)
    result = db.session.execute(query).scalars()
    products = result.all()
    return products_schema.jsonify(products)

@app.route("/products/<int:id>", methods = ["GET"])
def get_product_by_id(id):
    query = select(Product).filter(Product.product_id==id)
    product = db.session.execute(query).scalars().first()
    if product:
        return product_schema.jsonify(product)
    else:
        return jsonify({"Error": "Product Not Found"}), 404

@app.route('/products', methods = ["POST"])
def add_product():
    try: 
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    with Session(db.engine) as session:
        with session.begin():
            new_product = Product(name=product_data['name'], price=product_data['price'])
            session.add(new_product)
            session.commit()
    return jsonify({"Success": "Product Added"}), 201

@app.route("/products/<int:id>", methods = ["PUT"])
def update_product(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Product).filter(Product.product_id==id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"Error": "Product Not Found"}), 404
            product = result
            try:
                product_data = product_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            for field, value in product_data.items():
                setattr(product, field, value)
            session.commit()
            return jsonify({"Success": "Product Updated"}), 200

@app.route("/products/<int:id>", methods = ["DELETE"])
def delete_product(id):
    delete_statement = delete(Product).where(Product.product_id==id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"Error": "Product Not Found"}), 404
        return jsonify({"Success": "Product Deleted"}), 200
    
class OrderSchema(ma.Schema):
    order_id = fields.Integer(required=False)
    date = fields.Date(required=True)
    customer_id = fields.Integer(required=True)
    delivery_date = fields.Date(required=True)
    ordered_product = fields.String(required=True)

    class Meta:
        fields = ("order_id", "date", "customer_id", "delivery_date", "ordered_product")

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

@app.route("/orders", methods = ["GET"])
def get_orders():
    query = select(Order)
    result = db.session.execute(query).scalars()
    orders = result.all()
    return orders_schema.jsonify(orders)

@app.route("/orders/<int:id>", methods = ["GET"])
def get_orders_by_id(id):
    query = select(Order).filter(Order.order_id==id)
    order = db.session.execute(query).scalars().first()
    if order:
        return order_schema.jsonify(order)
    else:
        return jsonify({"Error": "Order Not Found"}), 404

@app.route("/orders", methods = ["POST"])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    with Session(db.engine) as session:
        with session.begin():
            new_order = Order(date=order_data['date'], customer_id=order_data['customer_id'], delivery_date=order_data['delivery_date'], ordered_product=order_data['ordered_product'])
            session.add(new_order)
            session.commit()
    return jsonify({"Success": "Order Added"}), 201

@app.route("/orders/<int:id>", methods = ["PUT"])
def update_order(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Order).filter(Order.order_id==id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"Error": "Order Not Found"}), 404
            order = result
            try:
                order_data = order_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            for field, value in order_data.items():
                setattr(order, field, value)
            session.commit()
            return jsonify({"Success": "Order Updated"}), 200

@app.route("/orders/<int:id>", methods = ["DELETE"])
def delete_order(id):
    delete_statement = delete(Order).where(Order.order_id==id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"Error": "Order Not Found"}), 404
        return jsonify({"Success": "Order Deleted"}), 200

@app.route("/")
def home():
    return "Greetings!"

if __name__== "__main__":
    app.run(debug=True)