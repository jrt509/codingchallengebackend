from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS 
from flask_heroku import Heroku
from flask_bcrypt import Bcrypt



app= Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://fliqxpqcgclqtt:6056f9650682ca4f7a0d35f813efd36fa81ad8847b446a840c0c83194ef8a6f9@ec2-52-86-116-94.compute-1.amazonaws.com:5432/dah6etap9jg3fo"

db = SQLAlchemy(app)
ma = Marshmallow(app)

heroku = Heroku(app)
CORS(app)
bcrypt = Bcrypt(app) 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)
    blogs = db.relationship("Blog", cascade="all,delete", backref="user", lazy=True)
    
    

    def __init__(self, username, password):
        self.username = username
        self.password = password

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    blog = db.Column(db.String(3000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    
    def __init__(self, title, blog, user_id):
        self.title = title
        self.blog = blog
        self.user_id = user_id
        
        
class BlogSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "blog", "user_id")    

blog_schema = BlogSchema()
blogs_schema = BlogSchema(many=True)

@app.route("/user/add", methods=["POST"])
def add_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    username_check = db.session.query(User.username).filter(User.username == username).first()
    if username_check is not None:
        return jsonify("Username Taken")

    hashed_password = bcrypt.generate_password_hash(password).decode("utf8")

    record = User(username, hashed_password)
    db.session.add(record)
    db.session.commit()

    return jsonify("User Created Successfully")

@app.route("/user/verified", methods=["POST"])
def verify_user():

    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    stored_password = db.session.query(User.password).filter(User.username == username).first()
    

    if stored_password is None:
        return jsonify("User NOT Verified")

    valid_password_check = bcrypt.check_password_hash(stored_password[0], password)

    if valid_password_check == False:
        return jsonify("User NOT Verified")

    return jsonify("User Verified")

@app.route("/blog/add", methods=["POST"])
def add_blog():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    post_data = request.get_json()
    title = post_data.get("title")
    blog = post_data.get("blog")
    username = post_data.get("username")

    user_id = db.session.query(User.id).filter(User.username == username).first()
    

    new_blog = Blog(title, blog, user_id[0])
    db.session.add(new_blog)
    db.session.commit()

    return jsonify("Blog added successfully")


@app.route("/blog/get", methods=["GET"])
def get_blogs():
    blogs = db.session.query(Blog).all()
    return jsonify(blogs_schema.dump(blogs))

@app.route("/blog/get/<username>", methods=["GET"])
def get_blogs_by_username(username):
    user_id = db.session.query(User.id).filter(User.username == username).first()[0]
    blogs = db.session.query(Blog).filter(Blog.user_id == user_id).all()
    return jsonify(blogs_schema.dump(blogs))

@app.route("/blog/delete/<username>", methods=["Delete"])
def delete_blog(id):
    blog = db.session.query(Blog).filter(Blog.id == id).first()
    db.session.delete(blog)
    db.session.commit()
    return jsonify("Blog deleted successfully")
    


if __name__ == "__main__":
    app.run(debug=True)